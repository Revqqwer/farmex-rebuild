#ifndef FARMEX_SHARED_VITALS_H
#define FARMEX_SHARED_VITALS_H
#include "vitals_bridge.h"
#define FARMEX_FRAME_MAGIC 0x31565846
#define FARMEX_FRAME_ABI 1
#define FARMEX_SOURCE_FIXTURE 1
#define FARMEX_SOURCE_GAME_CANDIDATE 2
#define FARMEX_IPC_ERROR 10
#define FARMEX_IPC_EXISTS 11
#define FARMEX_IPC_BAD_NAME 12
typedef struct FarmexSharedVitals {
    DWORD magic,abi_version,frame_size;
    volatile LONG sequence;
    DWORD producer_pid,source_kind,payload_size,reserved;
    FarmexVitals payload;
} FarmexSharedVitals;
typedef DWORD (__cdecl *FarmexPublishProc)(DWORD,const char *);
typedef DWORD (__cdecl *FarmexPublishFixtureProc)(DWORD,DWORD,const char *);
typedef void (__cdecl *FarmexClosePublisherProc)(void);
void farmex_close_publisher(void);
void farmex_init_publisher(void);
void farmex_finish_publisher(void);
#endif
