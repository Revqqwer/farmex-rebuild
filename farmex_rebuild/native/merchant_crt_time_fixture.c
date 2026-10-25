/* Own CRT localtime/%i reference only; never executes a bot helper. */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef int *(__cdecl *local_fn)(const long *);
typedef int (__cdecl *print_fn)(char *,const char *,...);
int main(int argc,char **argv){
    HMODULE dll;char loaded[MAX_PATH],formatted[256];long epoch;
    int *ptr,tmv[9],n;local_fn local;print_fn format;
    if(argc!=3||sizeof(void*)!=4)return 2;
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    dll=LoadLibraryExA(argv[1],NULL,LOAD_WITH_ALTERED_SEARCH_PATH);if(!dll)return 3;
    GetModuleFileNameA(dll,loaded,sizeof(loaded));if(lstrcmpiA(loaded,argv[1])!=0)return 4;
    local=(local_fn)GetProcAddress(dll,"_localtime");format=(print_fn)GetProcAddress(dll,"_sprintf");
    if(!local||!format)return 5;
    epoch=(long)strtoul(argv[2],NULL,10);ptr=local(&epoch);
    if(!ptr){printf("{\"epoch_dword\":%lu,\"localtime_null\":true}\n",(unsigned long)epoch);return 0;}
    memcpy(tmv,ptr,sizeof(tmv));
    n=format(formatted,"%i.%i.%i  %i-%i-%i",tmv[3],tmv[4],(int)((unsigned)tmv[5]+1900u),tmv[2],tmv[1],tmv[0]);
    if(n<0||n>=sizeof(formatted))return 6;
    printf("{\"epoch_dword\":%lu,\"localtime_null\":false,\"tm\":[%d,%d,%d,%d,%d,%d,%d,%d,%d],\"formatted\":\"%s\"}\n",
      (unsigned long)epoch,tmv[0],tmv[1],tmv[2],tmv[3],tmv[4],tmv[5],tmv[6],tmv[7],tmv[8],formatted);
    return 0;
}
