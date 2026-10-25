#ifndef FARMEX_COPIED_WORKER_H
#define FARMEX_COPIED_WORKER_H
#include "shared_vitals.h"
typedef HMODULE (WINAPI *OwnLoadLibrary)(LPCSTR);
typedef FARPROC (WINAPI *OwnGetProc)(HMODULE,LPCSTR);
typedef BOOL (WINAPI *OwnProtect)(LPVOID,SIZE_T,DWORD,PDWORD);
typedef BOOL (WINAPI *OwnFlush)(HANDLE,LPCVOID,SIZE_T);
typedef HANDLE (WINAPI *OwnCurrent)(void);
typedef BOOL (WINAPI *OwnFreeLibrary)(HMODULE);
typedef BOOL (WINAPI *OwnFree)(LPVOID,SIZE_T,DWORD);
typedef BOOL (WINAPI *OwnDllEntry)(HINSTANCE,DWORD,LPVOID);
typedef struct OwnWorkerContext {
    DWORD magic,size,command,phase,status,image,relocations,imports;
    OwnLoadLibrary load_library;OwnGetProc get_proc;OwnProtect protect;
    OwnFlush flush;OwnCurrent current;OwnFreeLibrary free_library;OwnFree free_memory;
    HMODULE dependencies[2];
    char system_paths[2][MAX_PATH];char export_name[40];char mapping_name[128];
    DWORD fixture_root;BYTE fixture_arena[4096];
    BYTE expected_image[0x5000];
} OwnWorkerContext;
#endif
