/* One-way own-process HP/MP publication. No game loader or command channel. */
#include "shared_vitals.h"
#include <stdio.h>
#include <string.h>
extern DWORD __cdecl FarmexObserve(DWORD,FarmexVitals *,DWORD);
extern DWORD __cdecl FarmexObserveFixture(DWORD,DWORD,FarmexVitals *,DWORD);
static HANDLE mapping=NULL;
static FarmexSharedVitals *view=NULL;
static char bound_name[128];
static CRITICAL_SECTION publisher_lock;
typedef char frame_size_is_84[(sizeof(FarmexSharedVitals)==84)?1:-1];

static int valid_name(const char *name) {
    char prefix[64];size_t n,i;
    if (!name) return 0;
    sprintf(prefix,"Local\\FarmexVitals.%lu.",GetCurrentProcessId());
    n=strlen(prefix);
    if (strlen(name)!=n+32 || strncmp(name,prefix,n)) return 0;
    for (i=n;i<n+32;i++) if (!strchr("0123456789abcdef",name[i])) return 0;
    return 1;
}

void farmex_init_publisher(void) { InitializeCriticalSection(&publisher_lock); }
void farmex_close_publisher(void) {
    EnterCriticalSection(&publisher_lock);
    if (view) UnmapViewOfFile(view);
    if (mapping) CloseHandle(mapping);
    view=NULL;mapping=NULL;bound_name[0]=0;
    LeaveCriticalSection(&publisher_lock);
}
void farmex_finish_publisher(void) { farmex_close_publisher();DeleteCriticalSection(&publisher_lock); }
__declspec(dllexport) void __cdecl FarmexClosePublishedVitals(void) { farmex_close_publisher(); }

static DWORD publish(const char *name,DWORD origin,FarmexVitals *payload) {
    DWORD previous,next;
    if (!valid_name(name)) return FARMEX_IPC_BAD_NAME;
    EnterCriticalSection(&publisher_lock);
    if (mapping && strcmp(name,bound_name)) { LeaveCriticalSection(&publisher_lock);return FARMEX_IPC_BAD_NAME; }
    if (!mapping) {
        mapping=CreateFileMappingA(INVALID_HANDLE_VALUE,NULL,PAGE_READWRITE,0,4096,name);
        if (!mapping) { LeaveCriticalSection(&publisher_lock);return FARMEX_IPC_ERROR; }
        if (GetLastError()==ERROR_ALREADY_EXISTS) {
            CloseHandle(mapping);mapping=NULL;LeaveCriticalSection(&publisher_lock);return FARMEX_IPC_EXISTS;
        }
        view=(FarmexSharedVitals *)MapViewOfFile(mapping,FILE_MAP_WRITE,0,0,4096);
        if (!view) { CloseHandle(mapping);mapping=NULL;LeaveCriticalSection(&publisher_lock);return FARMEX_IPC_ERROR; }
        strcpy(bound_name,name);
    }
    previous=(DWORD)view->sequence;
    /* InterlockedExchange supplies the full fence before/after the payload. */
    InterlockedExchange(&view->sequence,(LONG)((previous+1)|1));
    view->magic=FARMEX_FRAME_MAGIC;view->abi_version=FARMEX_FRAME_ABI;view->frame_size=sizeof(*view);
    view->producer_pid=GetCurrentProcessId();view->source_kind=origin;view->payload_size=sizeof(*payload);view->reserved=0;
    memcpy(&view->payload,payload,sizeof(*payload));
    next=((DWORD)view->sequence+1)&~1u;
    InterlockedExchange(&view->sequence,(LONG)(next?next:2));
    LeaveCriticalSection(&publisher_lock);
    return payload->status;
}
__declspec(dllexport) DWORD __cdecl FarmexPublishVitals(DWORD profile,const char *name) {
    FarmexVitals payload;
    DWORD status;
    if (!valid_name(name)) return FARMEX_IPC_BAD_NAME;
    status=FarmexObserve(profile,&payload,sizeof(payload));
    /* No publication when process/image/identity was not accepted. */
    if (status==1 || status==2 || status==7 || status==8 || status==9) return status;
    return publish(name,FARMEX_SOURCE_GAME_CANDIDATE,&payload);
}
__declspec(dllexport) DWORD __cdecl FarmexPublishVitalsFixture(DWORD slot,DWORD profile,const char *name) {
    FarmexVitals payload;
    DWORD status;
    if (!valid_name(name)) return FARMEX_IPC_BAD_NAME;
    status=FarmexObserveFixture(slot,profile,&payload,sizeof(payload));
    if (status==FARMEX_WRONG_PROCESS || status==FARMEX_INVALID_ARGUMENT) return status;
    return publish(name,FARMEX_SOURCE_FIXTURE,&payload);
}
