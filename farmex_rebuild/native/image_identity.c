/* Exact on-disk identity only. No keys, process memory, persistence or actions. */
#include "image_identity.h"
#include "vitals_bridge.h"
#include <string.h>

/* CNG signatures follow Microsoft bcrypt.h docs; bundled TCC has no bcrypt.h. */
typedef LONG (WINAPI *OpenAlg)(void **,LPCWSTR,LPCWSTR,ULONG);
typedef LONG (WINAPI *FarmexCngGetProp)(void *,LPCWSTR,BYTE *,ULONG,ULONG *,ULONG);
typedef LONG (WINAPI *CreateHash)(void *,void **,BYTE *,ULONG,BYTE *,ULONG,ULONG);
typedef LONG (WINAPI *HashData)(void *,BYTE *,ULONG,ULONG);
typedef LONG (WINAPI *FinishHash)(void *,BYTE *,ULONG,ULONG);
typedef LONG (WINAPI *DestroyHash)(void *);
typedef LONG (WINAPI *CloseAlg)(void *,ULONG);

DWORD farmex_check_image_file(const char *path,const BYTE *expected,DWORD expected_size,
                              DWORD *win_error,DWORD *stage) {
    HANDLE file=INVALID_HANDLE_VALUE;
    HMODULE module=NULL;
    void *algorithm=NULL,*hash=NULL;
    BYTE *object=NULL,*buffer=NULL,digest[32];
    DWORD status=FARMEX_IMAGE_HASH_ERROR,n,read_count,total=0;
    ULONG object_size=0,digest_size=0,property_size=0;
    DWORD file_low,file_high=0;
    char system_path[MAX_PATH];
    OpenAlg open_alg;FarmexCngGetProp get_prop;CreateHash create_hash;HashData hash_data;
    FinishHash finish_hash;DestroyHash destroy_hash=NULL;CloseAlg close_alg=NULL;
    *win_error=0;*stage=20;
    if (!path || !expected) { *win_error=ERROR_INVALID_PARAMETER;return FARMEX_INVALID_ARGUMENT; }
    file=CreateFileA(path,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
    if (file==INVALID_HANDLE_VALUE) { *win_error=GetLastError();goto cleanup; }
    *stage=21;
    SetLastError(ERROR_SUCCESS);
    file_low=GetFileSize(file,&file_high);
    if (file_low==INVALID_FILE_SIZE && GetLastError()!=ERROR_SUCCESS) { *win_error=GetLastError();goto cleanup; }
    if (file_high || file_low!=expected_size || expected_size>16*1024*1024) {
        status=FARMEX_IMAGE_HASH_MISMATCH;goto cleanup;
    }
    *stage=22;
    n=GetSystemDirectoryA(system_path,sizeof(system_path));
    if (!n || n+12>=sizeof(system_path)) { *win_error=ERROR_INSUFFICIENT_BUFFER;goto cleanup; }
    strcat(system_path,"\\bcrypt.dll");
    module=LoadLibraryA(system_path);
    if (!module) { *win_error=GetLastError();goto cleanup; }
    open_alg=(OpenAlg)GetProcAddress(module,"BCryptOpenAlgorithmProvider");
    get_prop=(FarmexCngGetProp)GetProcAddress(module,"BCryptGetProperty");
    create_hash=(CreateHash)GetProcAddress(module,"BCryptCreateHash");
    hash_data=(HashData)GetProcAddress(module,"BCryptHashData");
    finish_hash=(FinishHash)GetProcAddress(module,"BCryptFinishHash");
    destroy_hash=(DestroyHash)GetProcAddress(module,"BCryptDestroyHash");
    close_alg=(CloseAlg)GetProcAddress(module,"BCryptCloseAlgorithmProvider");
    if (!open_alg || !get_prop || !create_hash || !hash_data || !finish_hash || !destroy_hash || !close_alg) {
        *win_error=ERROR_PROC_NOT_FOUND;goto cleanup;
    }
    *stage=23;
    if (open_alg(&algorithm,L"SHA256",L"Microsoft Primitive Provider",0)<0 ||
        get_prop(algorithm,L"ObjectLength",(BYTE *)&object_size,4,&property_size,0)<0 || property_size!=4 ||
        !object_size || object_size>1024*1024 ||
        get_prop(algorithm,L"HashDigestLength",(BYTE *)&digest_size,4,&property_size,0)<0 ||
        property_size!=4 || digest_size!=32) { *win_error=ERROR_GEN_FAILURE;goto cleanup; }
    object=(BYTE *)HeapAlloc(GetProcessHeap(),0,object_size);
    buffer=(BYTE *)HeapAlloc(GetProcessHeap(),0,65536);
    if (!object || !buffer) { *win_error=ERROR_NOT_ENOUGH_MEMORY;goto cleanup; }
    *stage=24;
    if (create_hash(algorithm,&hash,object,object_size,NULL,0,0)<0) { *win_error=ERROR_GEN_FAILURE;goto cleanup; }
    *stage=25;
    for (;;) {
        if (!ReadFile(file,buffer,65536,&read_count,NULL)) { *win_error=GetLastError();goto cleanup; }
        if (!read_count) break;
        if (read_count>expected_size-total) { status=FARMEX_IMAGE_HASH_MISMATCH;goto cleanup; }
        total+=read_count;
        if (hash_data(hash,buffer,read_count,0)<0) { *win_error=ERROR_GEN_FAILURE;goto cleanup; }
    }
    if (total!=expected_size) { status=FARMEX_IMAGE_HASH_MISMATCH;goto cleanup; }
    *stage=26;
    if (finish_hash(hash,digest,sizeof(digest),0)<0) { *win_error=ERROR_GEN_FAILURE;goto cleanup; }
    status=memcmp(digest,expected,32)==0?FARMEX_CANDIDATE:FARMEX_IMAGE_HASH_MISMATCH;
cleanup:
    if (hash && destroy_hash) destroy_hash(hash);
    if (object) HeapFree(GetProcessHeap(),0,object);
    if (buffer) HeapFree(GetProcessHeap(),0,buffer);
    if (algorithm && close_alg) close_alg(algorithm,0);
    if (module) FreeLibrary(module);
    if (file!=INVALID_HANDLE_VALUE) CloseHandle(file);
    if (status==FARMEX_CANDIDATE) *stage=0;
    return status;
}
