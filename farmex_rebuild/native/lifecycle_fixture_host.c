/* Own DLL + own process only. Exercises Windows loader attach/detach, not
 * manual mapping or game loading. Keep basename farmex_probe_host.exe. */
#include "shared_vitals.h"
#include <stdio.h>
#include <string.h>
static BYTE arena[4096];
static DWORD root;
static HMODULE module;
static FarmexPublishFixtureProc publish;
static FarmexClosePublisherProc close_pub;
static char name[128];

static int load(const char *path) {
    module=LoadLibraryA(path);
    if (!module) return 0;
    publish=(FarmexPublishFixtureProc)GetProcAddress(module,"FarmexPublishVitalsFixture");
    close_pub=(FarmexClosePublisherProc)GetProcAddress(module,"FarmexClosePublishedVitals");
    return publish && close_pub;
}
static int absent(void) {
    HANDLE h=OpenFileMappingA(FILE_MAP_READ,FALSE,name);
    if (h) { CloseHandle(h); return 0; }
    return GetLastError()==ERROR_FILE_NOT_FOUND;
}
static int frame(DWORD sequence) {
    HANDLE h;FarmexSharedVitals *v;int ok;
    h=OpenFileMappingA(FILE_MAP_READ,FALSE,name);
    if (!h) return 0;
    v=(FarmexSharedVitals *)MapViewOfFile(h,FILE_MAP_READ,0,0,84);
    if (!v) { CloseHandle(h); return 0; }
    ok=v->magic==FARMEX_FRAME_MAGIC && v->abi_version==1 && v->frame_size==84 &&
       v->sequence==sequence && v->producer_pid==GetCurrentProcessId() &&
       v->source_kind==FARMEX_SOURCE_FIXTURE && v->payload_size==52 &&
       v->reserved==0 && v->payload.status==0 && v->payload.bytes_read==24 &&
       v->payload.hp==250 && v->payload.hp_max==500 &&
       v->payload.mp==100 && v->payload.mp_max==300;
    UnmapViewOfFile(v);CloseHandle(h);return ok;
}
static int check(const char *label,int ok) {
    printf("{\"case\":\"%s\",\"passed\":%s,\"pid\":%lu}\n",
           label,ok?"true":"false",GetCurrentProcessId());
    fflush(stdout);return ok;
}
int main(int argc,char **argv) {
    DWORD value,status;HANDLE held;int i;
    if (argc!=3 || sizeof(void *)!=4 || strlen(argv[2])!=32) return 2;
    for(i=0;i<32;i++) if (!strchr("0123456789abcdef",argv[2][i])) return 2;
    sprintf(name,"Local\\FarmexVitals.%lu.%s",GetCurrentProcessId(),argv[2]);
    root=(DWORD)(ULONG_PTR)arena;
    value=250;memcpy(arena+0x6d8,&value,4);
    value=500;memcpy(arena+0x6d4,&value,4);
    value=100;memcpy(arena+0xbf0,&value,4);
    value=300;memcpy(arena+0xbec,&value,4);
    if (!load(argv[1])) return 3;
    if (!check("attach_no_publication",absent())) return 4;
    status=publish((DWORD)(ULONG_PTR)&root,1,name);
    if (!check("initial_publish",status==0 && frame(2))) return 5;
    status=publish((DWORD)(ULONG_PTR)&root,1,name);
    if (!check("repeat_publish",status==0 && frame(4))) return 6;
    close_pub();close_pub();
    if (!check("idempotent_close",absent())) return 7;
    status=publish((DWORD)(ULONG_PTR)&root,1,name);
    if (!check("republish_after_close",status==0 && frame(2))) return 8;
    if (!FreeLibrary(module)) return 9;module=NULL;
    if (!check("detach_cleans_publication",absent())) return 10;
    if (!load(argv[1])) return 11;
    status=publish((DWORD)(ULONG_PTR)&root,1,name);
    if (!check("reattach_reinitializes_lock",status==0 && frame(2))) return 12;
    held=OpenFileMappingA(FILE_MAP_READ,FALSE,name);if (!held) return 13;
    if (!FreeLibrary(module)) return 14;module=NULL;
    if (!check("reader_retains_old_frame",frame(2))) return 15;
    if (!load(argv[1])) return 16;
    status=publish((DWORD)(ULONG_PTR)&root,1,name);
    if (!check("reattach_rejects_retained_mapping",status==FARMEX_IPC_EXISTS && frame(2))) return 17;
    CloseHandle(held);
    if (!check("last_reader_releases_mapping",absent())) return 18;
    status=publish((DWORD)(ULONG_PTR)&root,1,name);
    if (!check("retry_after_reader_release",status==0 && frame(2))) return 19;
    if (!FreeLibrary(module)) return 20;
    if (!check("final_detach_cleanup",absent())) return 21;
    return 0;
}
