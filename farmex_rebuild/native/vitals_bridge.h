#ifndef FARMEX_VITALS_BRIDGE_H
#define FARMEX_VITALS_BRIDGE_H
#include <windows.h>

/* Fixed32-bit ABI. Values remain candidates until independent verification. */
typedef struct FarmexVitals {
    DWORD abi_version;
    DWORD struct_size;
    DWORD status;
    DWORD win_error;
    DWORD bytes_read;
    DWORD process_id;
    DWORD timestamp_ms;
    DWORD profile;
    DWORD failed_read_step;
    DWORD hp;
    DWORD hp_max;
    DWORD mp;
    DWORD mp_max;
} FarmexVitals;

#define FARMEX_ABI_VERSION 1
#define FARMEX_CANDIDATE 0
#define FARMEX_WRONG_PROCESS 1
#define FARMEX_UNSUPPORTED_IMAGE 2
#define FARMEX_READ_ERROR 3
#define FARMEX_INVALID_ROOT 4
#define FARMEX_INVALID_VITALS 5
#define FARMEX_ROOT_CHANGED 6
#define FARMEX_INVALID_ARGUMENT 7
#define FARMEX_IMAGE_HASH_MISMATCH 8
#define FARMEX_IMAGE_HASH_ERROR 9

typedef DWORD (__cdecl *FarmexObserveProc)(DWORD, FarmexVitals *, DWORD);
typedef DWORD (__cdecl *FarmexFixtureProc)(DWORD, DWORD, FarmexVitals *, DWORD);
typedef DWORD (__cdecl *FarmexIdentityFixtureProc)(DWORD, const BYTE *, DWORD, FarmexVitals *, DWORD);
#endif
