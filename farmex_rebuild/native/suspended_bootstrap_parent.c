/* Can target ONLY the hash-pinned sibling which this parent creates suspended.
 * No existing PID, program path or remote image bytes are accepted. */
#include "shared_vitals.h"
#include "image_identity.h"
#include <stdio.h>
#include <string.h>
#include "own_bootstrap_child.h"
#ifdef FARMEX_SOURCE_WORKER_PARENT
#include "source_remote_context.h"
#include "source_loader_worker_template.h"
typedef BOOL (WINAPI *SourceOwnFlush)(HANDLE,LPCVOID,SIZE_T);
#endif
#ifdef FARMEX_COPIED_WORKER_PARENT
#include "copied_worker.h"
#include "own_worker_bytes.h"
#include <stddef.h>
#endif
#ifdef FARMEX_TRANSFER_PARENT
#include "own_bridge_image.h"
#endif

typedef LONG (WINAPI *QueryObject)(HANDLE,ULONG,PVOID,ULONG,PULONG);
typedef HANDLE (WINAPI *CreateJob)(LPSECURITY_ATTRIBUTES,LPCSTR);
typedef BOOL (WINAPI *SetJobInfo)(HANDLE,JOBOBJECTINFOCLASS,LPVOID,DWORD);
typedef BOOL (WINAPI *AssignJob)(HANDLE,HANDLE);
typedef LPVOID (WINAPI *OwnAllocEx)(HANDLE,LPVOID,SIZE_T,DWORD,DWORD);
typedef BOOL (WINAPI *OwnWriteMemory)(HANDLE,LPVOID,LPCVOID,SIZE_T,SIZE_T *);
typedef BOOL (WINAPI *OwnReadMemory)(HANDLE,LPCVOID,LPVOID,SIZE_T,SIZE_T *);
typedef BOOL (WINAPI *OwnProtectEx)(HANDLE,LPVOID,SIZE_T,DWORD,PDWORD);
typedef BOOL (WINAPI *OwnFreeEx)(HANDLE,LPVOID,SIZE_T,DWORD);
static int granted(HANDLE handle,DWORD *mask) {
    DWORD words[14],length=0;QueryObject query;
    query=(QueryObject)GetProcAddress(GetModuleHandleA("ntdll.dll"),"NtQueryObject");
    if (!query || query(handle,0,words,sizeof(words),&length) || length!=sizeof(words)) return 0;
    *mask=words[1];return 1;
}
int main(int argc,char **argv) {
    char path[MAX_PATH],command[MAX_PATH+80],name[128];char *slash;
    HANDLE lock=INVALID_HANDLE_VALUE,job=NULL,ready=NULL,release=NULL,thread=NULL,opened=NULL,map=NULL;
    FarmexSharedVitals *view=NULL;JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits;
    STARTUPINFOA startup;PROCESS_INFORMATION child;MEMORY_BASIC_INFORMATION page;
    DWORD stage=1,error=0,hash_stage=0,created_mask=0,reopened_mask=0,code=0,previous=0;
    DWORD bootstrap_exit=0;int i,success=0;
    HMODULE kernel;CreateJob create_job;SetJobInfo set_job_info;AssignJob assign_job;
    LPVOID remote_argument=NULL;DWORD transferred=0,transfer_writes=0;
    DWORD header_protect=0,text_protect=0,data_protect=0;
    DWORD worker_write_calls=0,worker_code_bytes=0,worker_context_bytes=0,worker_detach_exit=0;
    DWORD cleanup_confirmed=0,child_exit_observed=0;
    DWORD source_preflight_exit=0,source_worker_exit=0,source_worker_started=0,source_publish_exit=0;
#ifdef FARMEX_SOURCE_WORKER_PARENT
    SourceRemoteContext source_context;LPVOID source_remote_context=NULL,source_remote_code=NULL;
    OwnProtectEx source_protect;OwnFreeEx source_free;SourceOwnFlush source_flush;DWORD source_old;
#endif
#ifdef FARMEX_COPIED_WORKER_PARENT
    OwnWorkerContext *context=NULL;LPVOID remote_context=NULL,remote_worker=NULL;
    OwnReadMemory own_read;OwnProtectEx own_protect;OwnFreeEx own_free;
    OwnFlush own_flush;DWORD value,old_protection;SIZE_T read_count;
#endif
#ifdef FARMEX_TRANSFER_PARENT
    OwnAllocEx own_alloc;OwnWriteMemory own_write;SIZE_T written;
    IMAGE_NT_HEADERS32 *bridge_nt;IMAGE_SECTION_HEADER *bridge_sections;
#endif
    memset(&child,0,sizeof(child));
    if (argc!=2 || strlen(argv[1])!=32 || sizeof(void *)!=4) return 2;
    for(i=0;i<32;i++) if(!strchr("0123456789abcdef",argv[1][i])) return 2;
    kernel=GetModuleHandleA("kernel32.dll");
    create_job=(CreateJob)GetProcAddress(kernel,"CreateJobObjectA");
    set_job_info=(SetJobInfo)GetProcAddress(kernel,"SetInformationJobObject");
    assign_job=(AssignJob)GetProcAddress(kernel,"AssignProcessToJobObject");
    if(!create_job || !set_job_info || !assign_job) goto done;
    if (!GetModuleFileNameA(NULL,path,sizeof(path))) goto done;
    slash=strrchr(path,'\\');if(!slash || slash-path>MAX_PATH-30) goto done;
    strcpy(slash+1,"farmex_probe_host.exe");
    lock=CreateFileA(path,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
    if(lock==INVALID_HANDLE_VALUE) goto done;
    if(farmex_check_image_file(path,own_child_sha256,OWN_CHILD_SIZE,&error,&hash_stage)) goto done;
    stage=2;job=create_job(NULL,NULL);if(!job) goto done;
    memset(&limits,0,sizeof(limits));limits.BasicLimitInformation.LimitFlags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    if(!set_job_info(job,JobObjectExtendedLimitInformation,&limits,sizeof(limits))) goto done;
    if(GetEnvironmentVariableA("FARMEX_OWN_BOOTSTRAP_NONCE",name,sizeof(name))) goto done;
    if(!SetEnvironmentVariableA("FARMEX_OWN_BOOTSTRAP_NONCE",argv[1])) goto done;
    memset(&startup,0,sizeof(startup));startup.cb=sizeof(startup);
    sprintf(command,"\"%s\" --owned-bootstrap-child",path);
    stage=3;
    i=CreateProcessA(path,command,NULL,NULL,FALSE,CREATE_SUSPENDED|CREATE_NO_WINDOW,NULL,NULL,&startup,&child);
    error=GetLastError();SetEnvironmentVariableA("FARMEX_OWN_BOOTSTRAP_NONCE",NULL);
    if(!i) goto done;
    error=0;
    if(!assign_job(job,child.hProcess)) goto done;
    stage=4;
    if(!granted(child.hProcess,&created_mask) || (created_mask&0x43a)!=0x43a) goto done;
    opened=OpenProcess(0x43a,FALSE,child.dwProcessId);
    if(!opened || !granted(opened,&reopened_mask) || (reopened_mask&0x43a)!=0x43a) goto done;
    if(!VirtualQueryEx(child.hProcess,(LPCVOID)OWN_CHILD_BASE,&page,sizeof(page)) ||
       page.Type!=MEM_IMAGE || (DWORD)(ULONG_PTR)page.AllocationBase!=OWN_CHILD_BASE) goto done;
    sprintf(name,"Local\\FarmexBootstrapMain.%lu.%s",child.dwProcessId,argv[1]);
    SetLastError(0);ready=CreateEventA(NULL,TRUE,FALSE,name);
    if(!ready || GetLastError()==ERROR_ALREADY_EXISTS) goto done;
    sprintf(name,"Local\\FarmexBootstrapRelease.%lu.%s",child.dwProcessId,argv[1]);
    SetLastError(0);release=CreateEventA(NULL,TRUE,FALSE,name);
    if(!release || GetLastError()==ERROR_ALREADY_EXISTS) goto done;
    stage=5;
    if(WaitForSingleObject(ready,0)!=WAIT_TIMEOUT) goto done;
#ifdef FARMEX_TRANSFER_PARENT
    own_alloc=(OwnAllocEx)GetProcAddress(kernel,"VirtualAllocEx");
    own_write=(OwnWriteMemory)GetProcAddress(kernel,"WriteProcessMemory");
    if(!own_alloc || !own_write) goto done;
    bridge_nt=(IMAGE_NT_HEADERS32 *)(own_bridge_image+((IMAGE_DOS_HEADER *)own_bridge_image)->e_lfanew);
    if(sizeof(own_bridge_image)!=10752 || bridge_nt->OptionalHeader.SizeOfImage!=0x5000 ||
       bridge_nt->OptionalHeader.SizeOfHeaders!=0x200 || bridge_nt->FileHeader.NumberOfSections!=3) goto done;
    remote_argument=own_alloc(child.hProcess,(LPVOID)0x20000000,0x5000,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
    if(remote_argument!=(LPVOID)0x20000000) goto done;
    written=0;
    if(!own_write(child.hProcess,remote_argument,own_bridge_image,0x200,&written) || written!=0x200) goto done;
    transferred+=written;transfer_writes++;
    bridge_sections=IMAGE_FIRST_SECTION(bridge_nt);
    for(i=0;i<3;i++) {
        IMAGE_SECTION_HEADER *s=bridge_sections+i;written=0;
        if(s->VirtualAddress>0x5000 || s->SizeOfRawData>0x5000-s->VirtualAddress ||
           s->PointerToRawData>sizeof(own_bridge_image) || s->SizeOfRawData>sizeof(own_bridge_image)-s->PointerToRawData) goto done;
        if(!own_write(child.hProcess,(BYTE *)remote_argument+s->VirtualAddress,
                      own_bridge_image+s->PointerToRawData,s->SizeOfRawData,&written) || written!=s->SizeOfRawData) goto done;
        transferred+=written;transfer_writes++;
    }
#endif
#ifdef FARMEX_SOURCE_WORKER_PARENT
    source_protect=(OwnProtectEx)GetProcAddress(kernel,"VirtualProtectEx");
    source_free=(OwnFreeEx)GetProcAddress(kernel,"VirtualFreeEx");
    source_flush=(SourceOwnFlush)GetProcAddress(kernel,"FlushInstructionCache");
    if(!source_protect || !source_free || !source_flush || sizeof(source_context)!=24)goto done;
    source_remote_context=own_alloc(child.hProcess,(LPVOID)0x22000000,sizeof(source_context),MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
    source_remote_code=own_alloc(child.hProcess,(LPVOID)0x21000000,sizeof(source_loader_worker_code),MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
    if(source_remote_context!=(LPVOID)0x22000000 || source_remote_code!=(LPVOID)0x21000000)goto done;
    source_context.image=(DWORD)remote_argument;
    source_context.nt=source_context.image+((IMAGE_DOS_HEADER *)own_bridge_image)->e_lfanew;
    source_context.relocs=source_context.image+bridge_nt->OptionalHeader.DataDirectory[5].VirtualAddress;
    source_context.imports=source_context.image+bridge_nt->OptionalHeader.DataDirectory[1].VirtualAddress;
    source_context.load=(DWORD)GetProcAddress(kernel,"LoadLibraryA");source_context.resolve=(DWORD)GetProcAddress(kernel,"GetProcAddress");
#ifdef FARMEX_SOURCE_BAD_API
    source_context.load^=1; /* Fixed negative context, not an arbitrary target. */
#endif
    written=0;if(!own_write(child.hProcess,source_remote_context,&source_context,sizeof(source_context),&written) || written!=sizeof(source_context))goto done;
    worker_context_bytes=written;worker_write_calls++;
    written=0;if(!own_write(child.hProcess,source_remote_code,source_loader_worker_code,sizeof(source_loader_worker_code),&written) || written!=sizeof(source_loader_worker_code))goto done;
    worker_code_bytes=written;worker_write_calls++;
#ifdef FARMEX_SOURCE_BAD_IMAGE
    { BYTE bad=(BYTE)(own_bridge_image[0]^1);written=0;
      if(!own_write(child.hProcess,remote_argument,&bad,1,&written) || written!=1)goto done; }
#endif
    if(!source_protect(child.hProcess,source_remote_code,sizeof(source_loader_worker_code),PAGE_EXECUTE_READ,&source_old) ||
       !source_protect(child.hProcess,remote_argument,0x5000,PAGE_EXECUTE_READWRITE,&source_old) ||
       !source_flush(child.hProcess,source_remote_code,sizeof(source_loader_worker_code)) ||
       !source_flush(child.hProcess,remote_argument,0x5000))goto done;
    thread=CreateRemoteThread(child.hProcess,NULL,0,(LPTHREAD_START_ROUTINE)(OWN_CHILD_BASE+OWN_SOURCE_PREFLIGHT_RVA),source_remote_context,0,NULL);
    if(!thread || WaitForSingleObject(thread,5000)!=WAIT_OBJECT_0 || !GetExitCodeThread(thread,&source_preflight_exit) || source_preflight_exit)goto done;
    CloseHandle(thread);thread=NULL;
    thread=CreateRemoteThread(child.hProcess,NULL,0,(LPTHREAD_START_ROUTINE)source_remote_code,source_remote_context,0,NULL);
    if(!thread)goto done;source_worker_started=1;
    if(WaitForSingleObject(thread,5000)!=WAIT_OBJECT_0 || !GetExitCodeThread(thread,&source_worker_exit) || source_worker_exit!=1)goto done;
    CloseHandle(thread);thread=NULL;
    thread=CreateRemoteThread(child.hProcess,NULL,0,(LPTHREAD_START_ROUTINE)(OWN_CHILD_BASE+OWN_SOURCE_PUBLISH_RVA),remote_argument,0,NULL);
#elif defined(FARMEX_COPIED_WORKER_PARENT)
    own_read=(OwnReadMemory)GetProcAddress(kernel,"ReadProcessMemory");
    own_protect=(OwnProtectEx)GetProcAddress(kernel,"VirtualProtectEx");
    own_free=(OwnFreeEx)GetProcAddress(kernel,"VirtualFreeEx");
    own_flush=(OwnFlush)GetProcAddress(kernel,"FlushInstructionCache");
    if(!own_read || !own_protect || !own_free || !own_flush) goto done;
    context=(OwnWorkerContext *)HeapAlloc(GetProcessHeap(),HEAP_ZERO_MEMORY,sizeof(*context));if(!context) goto done;
    remote_context=own_alloc(child.hProcess,(LPVOID)0x22000000,sizeof(*context),MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
    remote_worker=own_alloc(child.hProcess,(LPVOID)0x21000000,sizeof(own_worker_bytes),MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
    if(remote_context!=(LPVOID)0x22000000 || remote_worker!=(LPVOID)0x21000000) goto done;
    context->magic=0x31425746;context->size=sizeof(*context);context->image=(DWORD)remote_argument;
    context->load_library=(OwnLoadLibrary)GetProcAddress(kernel,"LoadLibraryA");
    context->get_proc=(OwnGetProc)GetProcAddress(kernel,"GetProcAddress");
    context->protect=(OwnProtect)GetProcAddress(kernel,"VirtualProtect");
    context->flush=own_flush;context->current=(OwnCurrent)GetProcAddress(kernel,"GetCurrentProcess");
    context->free_library=(OwnFreeLibrary)GetProcAddress(kernel,"FreeLibrary");
    context->free_memory=(OwnFree)GetProcAddress(kernel,"VirtualFree");
    if(!context->load_library || !context->get_proc || !context->protect || !context->current ||
       !context->free_library || !context->free_memory) goto done;
    i=GetSystemDirectoryA(context->system_paths[0],MAX_PATH);if(i<=0 || i>MAX_PATH-16) goto done;
    strcpy(context->system_paths[1],context->system_paths[0]);
    strcat(context->system_paths[0],"\\kernel32.dll");strcat(context->system_paths[1],"\\msvcrt.dll");
    strcpy(context->export_name,"FarmexPublishVitalsFixture");
    sprintf(context->mapping_name,"Local\\FarmexVitals.%lu.%s",child.dwProcessId,argv[1]);
    context->fixture_root=(DWORD)remote_context+offsetof(OwnWorkerContext,fixture_arena);
    value=250;memcpy(context->fixture_arena+0x6d8,&value,4);value=500;memcpy(context->fixture_arena+0x6d4,&value,4);
    value=100;memcpy(context->fixture_arena+0xbf0,&value,4);value=300;memcpy(context->fixture_arena+0xbec,&value,4);
    memcpy(context->expected_image,own_bridge_image,0x200);
    for(i=0;i<3;i++) memcpy(context->expected_image+bridge_sections[i].VirtualAddress,
        own_bridge_image+bridge_sections[i].PointerToRawData,bridge_sections[i].SizeOfRawData);
#ifdef FARMEX_BAD_WORKER_REFERENCE
    context->expected_image[0]^=1; /* Fixed negative fixture, never changes executable payload. */
#endif
    written=0;if(!own_write(child.hProcess,remote_context,context,sizeof(*context),&written) || written!=sizeof(*context)) goto done;
    worker_context_bytes=written;worker_write_calls++;
    written=0;if(!own_write(child.hProcess,remote_worker,own_worker_bytes,sizeof(own_worker_bytes),&written) || written!=sizeof(own_worker_bytes)) goto done;
    worker_code_bytes=written;worker_write_calls++;
    if(!own_protect(child.hProcess,remote_worker,sizeof(own_worker_bytes),PAGE_EXECUTE_READ,&old_protection) ||
       !own_flush(child.hProcess,remote_worker,sizeof(own_worker_bytes))) goto done;
    thread=CreateRemoteThread(child.hProcess,NULL,0,(LPTHREAD_START_ROUTINE)remote_worker,remote_context,0,NULL);
#else
    thread=CreateRemoteThread(child.hProcess,NULL,0,
        (LPTHREAD_START_ROUTINE)(OWN_CHILD_BASE+OWN_BOOTSTRAP_RVA),remote_argument,0,NULL);
#endif
    if(!thread) goto done;
    if(WaitForSingleObject(thread,5000)!=WAIT_OBJECT_0 || !GetExitCodeThread(thread,&bootstrap_exit) || bootstrap_exit) goto done;
    CloseHandle(thread);thread=NULL;
#ifdef FARMEX_SOURCE_WORKER_PARENT
    source_publish_exit=bootstrap_exit;
    if(!source_free(child.hProcess,source_remote_code,0,MEM_RELEASE) || !source_free(child.hProcess,source_remote_context,0,MEM_RELEASE))goto done;
    source_remote_code=NULL;source_remote_context=NULL;
#endif
#ifdef FARMEX_COPIED_WORKER_PARENT
    read_count=0;
    if(!own_read(child.hProcess,remote_context,context,sizeof(*context),&read_count) || read_count!=sizeof(*context) ||
       context->status || context->phase!=1 || context->relocations!=116 || context->imports!=43) goto done;
#endif
#ifdef FARMEX_TRANSFER_PARENT
    if(!VirtualQueryEx(child.hProcess,remote_argument,&page,sizeof(page)) || page.Protect!=PAGE_READONLY) goto done;
    header_protect=page.Protect;
    if(!VirtualQueryEx(child.hProcess,(BYTE *)remote_argument+0x1000,&page,sizeof(page)) || page.Protect!=PAGE_EXECUTE_READ) goto done;
    text_protect=page.Protect;
    if(!VirtualQueryEx(child.hProcess,(BYTE *)remote_argument+0x3000,&page,sizeof(page)) || page.Protect!=PAGE_READWRITE) goto done;
    data_protect=page.Protect;
#endif
    if(WaitForSingleObject(ready,0)!=WAIT_TIMEOUT) goto done; /* own main has not run */
    stage=6;sprintf(name,"Local\\FarmexVitals.%lu.%s",child.dwProcessId,argv[1]);
    map=OpenFileMappingA(FILE_MAP_READ,FALSE,name);if(!map) goto done;
    view=(FarmexSharedVitals *)MapViewOfFile(map,FILE_MAP_READ,0,0,84);if(!view) goto done;
    if(view->magic!=FARMEX_FRAME_MAGIC || view->abi_version!=1 || view->frame_size!=84 || view->sequence!=2 ||
       view->producer_pid!=child.dwProcessId || view->source_kind!=FARMEX_SOURCE_FIXTURE ||
       view->payload_size!=52 || view->reserved || view->payload.abi_version!=1 || view->payload.struct_size!=52 ||
       view->payload.process_id!=child.dwProcessId || view->payload.profile!=1 || view->payload.win_error || view->payload.failed_read_step ||
       view->payload.status || view->payload.bytes_read!=24 || view->payload.hp!=250 ||
       view->payload.hp_max!=500 || view->payload.mp!=100 || view->payload.mp_max!=300) goto done;
    UnmapViewOfFile(view);view=NULL;CloseHandle(map);map=NULL;
    stage=7;previous=ResumeThread(child.hThread);if(previous!=1) goto done;
    if(WaitForSingleObject(ready,5000)!=WAIT_OBJECT_0) goto done;
#ifdef FARMEX_COPIED_WORKER_PARENT
    value=1;written=0;
    if(!own_write(child.hProcess,(BYTE *)remote_context+offsetof(OwnWorkerContext,command),&value,4,&written) || written!=4) goto done;
    worker_write_calls++;
    thread=CreateRemoteThread(child.hProcess,NULL,0,(LPTHREAD_START_ROUTINE)remote_worker,remote_context,0,NULL);
    if(!thread || WaitForSingleObject(thread,5000)!=WAIT_OBJECT_0 || !GetExitCodeThread(thread,&worker_detach_exit) || worker_detach_exit) goto done;
    CloseHandle(thread);thread=NULL;
    read_count=0;
    if(!own_read(child.hProcess,remote_context,context,sizeof(*context),&read_count) || read_count!=sizeof(*context) || context->phase!=2 || context->status) goto done;
    if(!VirtualQueryEx(child.hProcess,remote_argument,&page,sizeof(page)) || page.State!=MEM_FREE) goto done;
    if(!own_free(child.hProcess,remote_worker,0,MEM_RELEASE) || !own_free(child.hProcess,remote_context,0,MEM_RELEASE)) goto done;
    remote_worker=NULL;remote_context=NULL;
#endif
    if(!SetEvent(release)) goto done;
    if(WaitForSingleObject(child.hProcess,5000)!=WAIT_OBJECT_0 || !GetExitCodeProcess(child.hProcess,&code) || code) goto done;
    child_exit_observed=1;cleanup_confirmed=1;
    stage=8;sprintf(name,"Local\\FarmexVitals.%lu.%s",child.dwProcessId,argv[1]);
    map=OpenFileMappingA(FILE_MAP_READ,FALSE,name);
    if(map || GetLastError()!=ERROR_FILE_NOT_FOUND) goto done;
    success=1;
done:
    if(!success && !error) error=GetLastError();
    if(view) UnmapViewOfFile(view);if(map) CloseHandle(map);
    if(thread) CloseHandle(thread);if(opened) CloseHandle(opened);
    if(child.hProcess) {
        if(!success) {
            TerminateProcess(child.hProcess,90);
            if(WaitForSingleObject(child.hProcess,5000)==WAIT_OBJECT_0 && GetExitCodeProcess(child.hProcess,&code)) {
                cleanup_confirmed=1;child_exit_observed=1;
            }
        }
        CloseHandle(child.hThread);CloseHandle(child.hProcess);
    }
    if(ready) CloseHandle(ready);if(release) CloseHandle(release);if(job) CloseHandle(job);
    if(lock!=INVALID_HANDLE_VALUE) CloseHandle(lock);
#ifdef FARMEX_COPIED_WORKER_PARENT
    if(context) HeapFree(GetProcessHeap(),0,context);
#endif
    printf("{\"passed\":%s,\"stage\":%lu,\"error\":%lu,\"child_pid\":%lu,"
           "\"created_mask\":%lu,\"reopened_mask\":%lu,\"bootstrap_exit\":%lu,\"resume_previous\":%lu,\"child_exit\":%lu,"
           "\"transferred_bytes\":%lu,\"transfer_writes\":%lu,\"transferred_base\":%lu,"
           "\"header_protect\":%lu,\"text_protect\":%lu,\"data_protect\":%lu,"
           "\"worker_write_calls\":%lu,\"worker_code_bytes\":%lu,\"worker_context_bytes\":%lu,\"worker_detach_exit\":%lu,"
           "\"cleanup_confirmed\":%lu,\"child_exit_observed\":%lu,"
           "\"source_preflight_exit\":%lu,\"source_worker_started\":%lu,\"source_worker_exit\":%lu,\"source_publish_exit\":%lu}\n",
           success?"true":"false",stage,error,child.dwProcessId,created_mask,reopened_mask,bootstrap_exit,previous,code,
           transferred,transfer_writes,(DWORD)(ULONG_PTR)remote_argument,header_protect,text_protect,data_protect,
           worker_write_calls,worker_code_bytes,worker_context_bytes,worker_detach_exit,cleanup_confirmed,child_exit_observed,
           source_preflight_exit,source_worker_started,source_worker_exit,source_publish_exit);
    return success?0:1;
}
