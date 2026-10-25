/* Controlled local PE bootstrap experiment: the build embeds ONLY our pinned
 * bridge DLL. No runtime image path, PID argument or remote-process operations.
 * This is not a game loader or a general-purpose DLL loading library. */
#include "shared_vitals.h"
#include <stdio.h>
#include <string.h>
#include "own_bridge_image.h"

typedef BOOL (WINAPI *Entry)(HINSTANCE,DWORD,LPVOID);
static BYTE *image;
static DWORD image_size,relocation_count,import_count;
static HMODULE dependencies[2];
static int dependency_count,attached;
static LPVOID reservation;
static Entry entry;
static BYTE arena[4096];
static DWORD root;

static void *at(DWORD rva,DWORD count) {
    if (rva>image_size || count>image_size-rva) return NULL;
    return image+rva;
}
static const char *string_at(DWORD rva) {
    DWORD i;
    for(i=0;i<256;i++) {
        char *p=(char *)at(rva+i,1);
        if (!p) return NULL;
        if (!*p) return (const char *)at(rva,i+1);
    }
    return NULL;
}
static FARPROC symbol(const char *wanted) {
    IMAGE_DOS_HEADER *dos=(IMAGE_DOS_HEADER *)image;
    IMAGE_NT_HEADERS32 *nt=(IMAGE_NT_HEADERS32 *)(image+dos->e_lfanew);
    IMAGE_DATA_DIRECTORY dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT];
    IMAGE_EXPORT_DIRECTORY *exp=(IMAGE_EXPORT_DIRECTORY *)at(dir.VirtualAddress,sizeof(*exp));
    DWORD *names,*functions,i,rva;WORD *ordinals;
    if (!exp || exp->NumberOfNames>64 || exp->NumberOfFunctions>64) return NULL;
    names=(DWORD *)at(exp->AddressOfNames,4*exp->NumberOfNames);
    functions=(DWORD *)at(exp->AddressOfFunctions,4*exp->NumberOfFunctions);
    ordinals=(WORD *)at(exp->AddressOfNameOrdinals,2*exp->NumberOfNames);
    if (!names || !functions || !ordinals) return NULL;
    for(i=0;i<exp->NumberOfNames;i++) {
        const char *name=string_at(names[i]);
        if (!name || ordinals[i]>=exp->NumberOfFunctions) return NULL;
        if (strcmp(name,wanted)) continue;
        rva=functions[ordinals[i]];
        if (rva>=dir.VirtualAddress && rva-dir.VirtualAddress<dir.Size) return NULL;
        return (FARPROC)at(rva,1);
    }
    return NULL;
}
static void cleanup(void) {
    int i;
    if (attached) { entry((HINSTANCE)image,DLL_PROCESS_DETACH,NULL);attached=0; }
    if (image) { VirtualFree(image,0,MEM_RELEASE);image=NULL; }
    for(i=dependency_count-1;i>=0;i--) FreeLibrary(dependencies[i]);
    dependency_count=0;
    if (reservation) { VirtualFree(reservation,0,MEM_RELEASE);reservation=NULL; }
}
#ifdef FARMEX_SOURCE_LOADER_WORKER
#include "source_loader_bridge_mode.h"
#endif
static int prepare_from(LPVOID supplied) {
    IMAGE_DOS_HEADER *dos=(IMAGE_DOS_HEADER *)own_bridge_image;
    IMAGE_NT_HEADERS32 *nt;
    IMAGE_SECTION_HEADER *sections;
    IMAGE_DATA_DIRECTORY dir;
    DWORD i,j,old,delta,offset=0,span,protection;
    BYTE *expected;MEMORY_BASIC_INFORMATION info;
    if (sizeof(void *)!=4 || sizeof(own_bridge_image)!=10752 ||
        dos->e_magic!=IMAGE_DOS_SIGNATURE || dos->e_lfanew<0 ||
        (DWORD)dos->e_lfanew>sizeof(own_bridge_image)-sizeof(*nt)) return 1;
    nt=(IMAGE_NT_HEADERS32 *)(own_bridge_image+dos->e_lfanew);
    if (nt->Signature!=IMAGE_NT_SIGNATURE || nt->FileHeader.Machine!=IMAGE_FILE_MACHINE_I386 ||
        nt->OptionalHeader.Magic!=IMAGE_NT_OPTIONAL_HDR32_MAGIC ||
        nt->FileHeader.NumberOfSections!=3 || nt->OptionalHeader.ImageBase!=0x10000000 ||
        nt->OptionalHeader.SizeOfImage!=0x5000 || nt->OptionalHeader.SizeOfHeaders!=0x200 ||
        nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_TLS].Size ||
        nt->OptionalHeader.DataDirectory[13].Size || nt->OptionalHeader.DataDirectory[14].Size) return 2;
    image_size=nt->OptionalHeader.SizeOfImage;
    sections=IMAGE_FIRST_SECTION(nt);
    for(i=0;i<3;i++) {
        IMAGE_SECTION_HEADER *s=sections+i;
        if (s->PointerToRawData>sizeof(own_bridge_image) ||
            s->SizeOfRawData>sizeof(own_bridge_image)-s->PointerToRawData ||
            s->VirtualAddress>image_size || s->SizeOfRawData>image_size-s->VirtualAddress) return 4;
    }
    if(supplied) {
        if ((DWORD)(ULONG_PTR)supplied==nt->OptionalHeader.ImageBase ||
            !VirtualQuery(supplied,&info,sizeof(info)) || info.AllocationBase!=supplied ||
            info.BaseAddress!=supplied || info.RegionSize!=image_size ||
            info.State!=MEM_COMMIT || info.Type!=MEM_PRIVATE || info.Protect!=PAGE_READWRITE) return 18;
        expected=(BYTE *)VirtualAlloc(NULL,image_size,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
        if(!expected) return 19;
        memcpy(expected,own_bridge_image,nt->OptionalHeader.SizeOfHeaders);
        for(i=0;i<3;i++) memcpy(expected+sections[i].VirtualAddress,
            own_bridge_image+sections[i].PointerToRawData,sections[i].SizeOfRawData);
        j=memcmp(expected,supplied,image_size);VirtualFree(expected,0,MEM_RELEASE);
        if(j) return 20; /* No foreign code: exact entire mapped image, including zero gaps. */
        image=(BYTE *)supplied; /* Own parent transfers ownership only after full validation. */
    } else {
        reservation=VirtualAlloc((LPVOID)nt->OptionalHeader.ImageBase,image_size,MEM_RESERVE,PAGE_NOACCESS);
        image=(BYTE *)VirtualAlloc(NULL,image_size,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
        if (!image || (DWORD)(ULONG_PTR)image==nt->OptionalHeader.ImageBase) return 3;
        memcpy(image,own_bridge_image,nt->OptionalHeader.SizeOfHeaders);
        for(i=0;i<3;i++) memcpy(image+sections[i].VirtualAddress,
            own_bridge_image+sections[i].PointerToRawData,sections[i].SizeOfRawData);
    }
    delta=(DWORD)(ULONG_PTR)image-nt->OptionalHeader.ImageBase;
#ifdef FARMEX_SOURCE_LOADER_WORKER
    i=prepare_original_source_worker(nt,delta);
    if(i)return (int)i;
#else
    dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_BASERELOC];
    while(offset<dir.Size) {
        IMAGE_BASE_RELOCATION *block=(IMAGE_BASE_RELOCATION *)at(dir.VirtualAddress+offset,8);
        WORD *words;
        if (!block || block->SizeOfBlock<8 || block->SizeOfBlock>dir.Size-offset ||
            (block->SizeOfBlock&1)) return 5;
        words=(WORD *)at(dir.VirtualAddress+offset+8,block->SizeOfBlock-8);
        if (!words) return 5;
        for(j=0;j<(block->SizeOfBlock-8)/2;j++) {
            DWORD *target;
            if (!words[j]) continue;
            /* Original worker adjusts every nonzero word. Our pinned DLL
             * contains only HIGHLOW and zero padding; reject any other kind. */
            if ((words[j]>>12)!=IMAGE_REL_BASED_HIGHLOW) return 6;
            target=(DWORD *)at(block->VirtualAddress+(words[j]&0xfff),4);
            if (!target) return 6;
            *target+=delta;relocation_count++;
        }
        offset+=block->SizeOfBlock;
    }
    dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];
    for(i=0;i<dir.Size/20;i++) {
        IMAGE_IMPORT_DESCRIPTOR *desc=(IMAGE_IMPORT_DESCRIPTOR *)at(dir.VirtualAddress+20*i,20);
        const char *dll_name;char system_path[MAX_PATH];UINT count;
        DWORD *lookup,*iat;
        if (!desc) return 7;
        if (!desc->OriginalFirstThunk) break;
        dll_name=string_at(desc->Name);
        if (!dll_name || (strcmp(dll_name,"kernel32.dll") && strcmp(dll_name,"msvcrt.dll")) ||
            dependency_count==2) return 8;
        count=GetSystemDirectoryA(system_path,MAX_PATH);
        if (!count || count>MAX_PATH-16) return 8;
        strcat(system_path,"\\");strcat(system_path,dll_name);
        dependencies[dependency_count]=LoadLibraryA(system_path);
        if (!dependencies[dependency_count]) return 9;
        dependency_count++;
        for(j=0;j<256;j++) {
            FARPROC address;const char *name;
            lookup=(DWORD *)at(desc->OriginalFirstThunk+4*j,4);
            iat=(DWORD *)at(desc->FirstThunk+4*j,4);
            if (!lookup || !iat) return 10;
            if (!*lookup) break;
            if (*lookup&IMAGE_ORDINAL_FLAG32)
                address=GetProcAddress(dependencies[dependency_count-1],(LPCSTR)(*lookup&0xffff));
            else {
                name=string_at(*lookup+2);if (!name) return 10;
                address=GetProcAddress(dependencies[dependency_count-1],name);
            }
            if (!address) return 11;
            *iat=(DWORD)(ULONG_PTR)address;import_count++;
        }
        if (j==256) return 12;
    }
    if (i==dir.Size/20 || dependency_count!=2) return 13;
#endif
    if (!VirtualProtect(image,image_size,PAGE_NOACCESS,&old) ||
        !VirtualProtect(image,0x1000,PAGE_READONLY,&old)) return 14;
    for(i=0;i<3;i++) {
        IMAGE_SECTION_HEADER *s=sections+i;
        span=s->Misc.VirtualSize>s->SizeOfRawData?s->Misc.VirtualSize:s->SizeOfRawData;
        protection=(s->Characteristics&IMAGE_SCN_MEM_EXECUTE)?PAGE_EXECUTE_READ:
            ((s->Characteristics&IMAGE_SCN_MEM_WRITE)?PAGE_READWRITE:PAGE_READONLY);
        if (!VirtualProtect(image+s->VirtualAddress,span,protection,&old)) return 15;
    }
    if (!FlushInstructionCache(GetCurrentProcess(),image,image_size)) return 16;
    entry=(Entry)at(nt->OptionalHeader.AddressOfEntryPoint,1);
#ifndef FARMEX_SOURCE_LOADER_WORKER
    if (!entry || !entry((HINSTANCE)image,DLL_PROCESS_ATTACH,NULL)) return 17;
#endif
    attached=1;return 0;
}
static int prepare(void) { return prepare_from(NULL); }
#ifdef FARMEX_SUSPENDED_CHILD
static volatile LONG bootstrap_ready;
#ifdef FARMEX_SOURCE_WORKER_CHILD
#include "source_remote_child.h"
#endif
__declspec(dllexport) DWORD WINAPI FarmexFixtureBootstrap(LPVOID argument) {
    FarmexPublishFixtureProc publish;FarmexFixtureProc fixture;
    FarmexVitals snapshot;char nonce[33],name[128];DWORD value,result;int code,i;
    if (bootstrap_ready || image) return 20;
#ifdef FARMEX_TRANSFER_CHILD
    if(!argument) return 26;
#else
    if(argument) return 26;
#endif
    if (GetEnvironmentVariableA("FARMEX_OWN_BOOTSTRAP_NONCE",nonce,sizeof(nonce))!=32) return 21;
    for(i=0;i<32;i++) if (!strchr("0123456789abcdef",nonce[i])) return 22;
#ifdef FARMEX_TRANSFER_CHILD
    code=prepare_from(argument);
#else
    code=prepare();
#endif
    if(code) { cleanup();return 100+code; }
    if(relocation_count!=116 || import_count!=43) { cleanup();return 27; }
    fixture=(FarmexFixtureProc)symbol("FarmexObserveFixture");
    publish=(FarmexPublishFixtureProc)symbol("FarmexPublishVitalsFixture");
    if (!fixture || !publish) { cleanup();return 23; }
    root=(DWORD)(ULONG_PTR)arena;
    value=250;memcpy(arena+0x6d8,&value,4);value=500;memcpy(arena+0x6d4,&value,4);
    value=100;memcpy(arena+0xbf0,&value,4);value=300;memcpy(arena+0xbec,&value,4);
    result=fixture((DWORD)(ULONG_PTR)&root,1,&snapshot,sizeof(snapshot));
    if (result || snapshot.bytes_read!=24 || snapshot.hp!=250 || snapshot.mp!=100) { cleanup();return 24; }
    sprintf(name,"Local\\FarmexVitals.%lu.%s",GetCurrentProcessId(),nonce);
    result=publish((DWORD)(ULONG_PTR)&root,1,name);
    if (result) { cleanup();return 25; }
    InterlockedExchange(&bootstrap_ready,1);return 0;
}
int main(int argc,char **argv) {
    char nonce[33],name[128];HANDLE ready=NULL,release=NULL;DWORD status;int result=30;
    if (argc!=2 || strcmp(argv[1],"--owned-bootstrap-child")) return 31;
#ifndef FARMEX_COPIED_WORKER_CHILD
    if (!bootstrap_ready) return 32;
#endif
    if (GetEnvironmentVariableA("FARMEX_OWN_BOOTSTRAP_NONCE",nonce,sizeof(nonce))!=32) return 32;
    sprintf(name,"Local\\FarmexBootstrapMain.%lu.%s",GetCurrentProcessId(),nonce);
    ready=OpenEventA(EVENT_MODIFY_STATE,FALSE,name);if (!ready) goto done;
    sprintf(name,"Local\\FarmexBootstrapRelease.%lu.%s",GetCurrentProcessId(),nonce);
    release=OpenEventA(SYNCHRONIZE,FALSE,name);if (!release) goto done;
    if (!SetEvent(ready)) goto done;
    status=WaitForSingleObject(release,5000);if (status!=WAIT_OBJECT_0) goto done;
    cleanup();result=0;
done:
    if (ready) CloseHandle(ready);if (release) CloseHandle(release);return result;
}
#else
int main(int argc,char **argv) {
    FarmexFixtureProc fixture;FarmexObserveProc production;FarmexPublishFixtureProc publish;
    FarmexVitals snapshot;MEMORY_BASIC_INFORMATION info;
    DWORD result,value;int code,i;char map_name[128];HANDLE handle;
    if (argc!=2 || strlen(argv[1])!=32) return 2;
    for(i=0;i<32;i++) if (!strchr("0123456789abcdef",argv[1][i])) return 2;
    code=prepare();
    if (code) { fprintf(stderr,"local preparation failed at %d error %lu\n",code,GetLastError());cleanup();return 3; }
    fixture=(FarmexFixtureProc)symbol("FarmexObserveFixture");
    production=(FarmexObserveProc)symbol("FarmexObserve");
    publish=(FarmexPublishFixtureProc)symbol("FarmexPublishVitalsFixture");
    if (!fixture || !production || !publish) { cleanup();return 4; }
    root=(DWORD)(ULONG_PTR)arena;
    value=250;memcpy(arena+0x6d8,&value,4);value=500;memcpy(arena+0x6d4,&value,4);
    value=100;memcpy(arena+0xbf0,&value,4);value=300;memcpy(arena+0xbec,&value,4);
    result=fixture((DWORD)(ULONG_PTR)&root,1,&snapshot,sizeof(snapshot));
    if (result || snapshot.bytes_read!=24 || snapshot.hp!=250 || snapshot.mp!=100) { cleanup();return 5; }
    result=production(1,&snapshot,sizeof(snapshot));
    if (result!=FARMEX_WRONG_PROCESS || snapshot.bytes_read) { cleanup();return 6; }
    if (!VirtualQuery(image,&info,sizeof(info)) || info.Type!=MEM_PRIVATE ||
        GetModuleHandleA("farmex_vitals_bridge.dll")) { cleanup();return 7; }
    sprintf(map_name,"Local\\FarmexVitals.%lu.%s",GetCurrentProcessId(),argv[1]);
    result=publish((DWORD)(ULONG_PTR)&root,1,map_name);
    if (result) { cleanup();return 8; }
    printf("{\"stage\":\"ready\",\"pid\":%lu,\"relocations\":%lu,\"imports\":%lu,"
           "\"preferred_base\":268435456,\"actual_base\":%lu,\"memory_type\":%lu,\"attach_returned\":true}\n",
           GetCurrentProcessId(),relocation_count,import_count,(DWORD)(ULONG_PTR)image,info.Type);
#ifdef FARMEX_SOURCE_LOADER_WORKER
    printf("{\"stage\":\"source_worker\",\"bytes\":431,\"patches\":0,\"worker_result\":%lu,\"real_system_loads\":%lu,\"real_symbol_resolutions\":%lu}\n",
           source_worker_result,source_load_calls,source_resolve_calls);
#endif
    fflush(stdout);getchar();
    cleanup();
    handle=OpenFileMappingA(FILE_MAP_READ,FALSE,map_name);
    if (handle) { CloseHandle(handle);return 9; }
    if (GetLastError()!=ERROR_FILE_NOT_FOUND) return 10;
    printf("{\"stage\":\"detached\",\"mapping_absent\":true}\n");return 0;
}
#endif
