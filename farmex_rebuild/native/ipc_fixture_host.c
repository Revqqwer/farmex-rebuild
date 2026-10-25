/* Own host for cross-bitness shared frames; output is always a fixture.
 * Build with the exact basename farmex_probe_host.exe in a separate test dir.
 */
#include "shared_vitals.h"
#include <stdio.h>
#include <string.h>
static BYTE arena[4096];static DWORD root;
static FarmexPublishFixtureProc fixture;
static char map_name[128];
static void set_value(DWORD offset,DWORD value) { memcpy(arena+offset,&value,4); }
static DWORD WINAPI writer(LPVOID unused) {
    int i;for (i=0;i<128;i++) if (fixture((DWORD)(ULONG_PTR)&root,1,map_name)) return 1;
    return 0;
}
int main(int argc,char **argv) {
    HMODULE dll;FarmexPublishProc production;FarmexClosePublisherProc close_pub;
    HANDLE existing=NULL,edit_handle=NULL,threads[2];FarmexSharedVitals *edit=NULL;
    DWORD status,profile=1;int i;
    if (argc!=4 || sizeof(void *)!=4 || strlen(argv[2])!=32) return 2;
    sprintf(map_name,"Local\\FarmexVitals.%lu.%s",GetCurrentProcessId(),argv[2]);
    dll=LoadLibraryA(argv[1]);if (!dll) return 3;
    fixture=(FarmexPublishFixtureProc)GetProcAddress(dll,"FarmexPublishVitalsFixture");
    production=(FarmexPublishProc)GetProcAddress(dll,"FarmexPublishVitals");
    close_pub=(FarmexClosePublisherProc)GetProcAddress(dll,"FarmexClosePublishedVitals");
    if (!fixture || !production || !close_pub) { FreeLibrary(dll);return 4; }
    root=(DWORD)(ULONG_PTR)arena;set_value(0x6d8,250);set_value(0x6d4,500);
    set_value(0xbf0,100);set_value(0xbec,300);set_value(0xd60,110);set_value(0xd5c,310);
    if (!strcmp(argv[3],"normal_steam")) profile=2;
    if (!strcmp(argv[3],"duplicate")) {
        existing=CreateFileMappingA(INVALID_HANDLE_VALUE,NULL,PAGE_READWRITE,0,4096,map_name);
        edit=(FarmexSharedVitals *)MapViewOfFile(existing,FILE_MAP_WRITE,0,0,4096);
        if (!edit) return 5;edit->magic=0xabcdef01;UnmapViewOfFile(edit);edit=NULL;
    }
    if (!strcmp(argv[3],"bad_name")) map_name[strlen(map_name)-1]='g';
    if (!strcmp(argv[3],"production_block")) status=production(1,map_name);
    else if (!strcmp(argv[3],"read_error")) status=fixture(1,profile,map_name);
    else status=fixture((DWORD)(ULONG_PTR)&root,profile,map_name);
    if (!strcmp(argv[3],"concurrent")) {
        for (i=0;i<2;i++) { threads[i]=CreateThread(NULL,0,writer,NULL,0,NULL);if (!threads[i]) return 6; }
        WaitForMultipleObjects(2,threads,TRUE,INFINITE);
        for (i=0;i<2;i++) { DWORD code;GetExitCodeThread(threads[i],&code);CloseHandle(threads[i]);if (code) return 7; }
    }
    if (!status) {
        edit_handle=OpenFileMappingA(FILE_MAP_WRITE,FALSE,map_name);
        edit=(FarmexSharedVitals *)MapViewOfFile(edit_handle,FILE_MAP_WRITE,0,0,4096);
        if (!edit) return 8;
        if (!strcmp(argv[3],"odd_sequence")) InterlockedExchange(&edit->sequence,3);
        else if (!strcmp(argv[3],"wrong_magic")) edit->magic=0;
        else if (!strcmp(argv[3],"wrong_origin")) edit->source_kind=2;
        else if (!strcmp(argv[3],"wrong_profile")) edit->payload.profile=2;
        else if (!strcmp(argv[3],"wrong_size")) edit->payload_size=51;
        else if (!strcmp(argv[3],"wrong_pid")) edit->payload.process_id++;
        else if (!strcmp(argv[3],"stale")) edit->payload.timestamp_ms-=5000;
        else if (!strcmp(argv[3],"error_leak")) edit->payload.status=3;
        UnmapViewOfFile(edit);CloseHandle(edit_handle);
    }
    printf("{\"pid\":%lu,\"publisher_status\":%lu,\"profile\":%lu}\n",GetCurrentProcessId(),status,profile);
    fflush(stdout);
    getchar(); /* Parent owns this hidden host and releases it after reading. */
    close_pub();if (existing) CloseHandle(existing);FreeLibrary(dll);return 0;
}
