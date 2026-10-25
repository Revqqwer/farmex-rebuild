/* Own x86 process and own output files only; never loads the bot or game.
 * Compare pinned CC32260MT _Fiopen modes2/0x82, fwrite and fclose.
 * This does not execute the source C++ ostream wrappers.
 */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern UINT WINAPI GetACP(void);
typedef void *(__cdecl *open_fn)(const char *,int,int);
typedef unsigned (__cdecl *write_fn)(const void *,unsigned,unsigned,void *);
typedef int (__cdecl *close_fn)(void *);
static int nibble(char c){return c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:-1;}
int main(int argc,char **argv){
    HMODULE dll;char loaded[MAX_PATH],output[MAX_PATH],*slash;
    unsigned char payload[2048];unsigned n,j,written;int mode,closed;
    open_fn open_file;write_fn write_file;close_fn close_file;void *file;
    if(argc!=5||sizeof(void*)!=4)return 2;
    if(strchr(argv[2],'\\')||strchr(argv[2],'/')||strchr(argv[2],':')||strstr(argv[2],".."))return 7;
    mode=atoi(argv[3]);if(mode!=2&&mode!=130)return 8;
    n=strlen(argv[4]);if(n%2||n>4096)return 9;
    for(j=0;j<n;j+=2){int a=nibble(argv[4][j]),b=nibble(argv[4][j+1]);if(a<0||b<0)return 10;payload[j/2]=16*a+b;}
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    dll=LoadLibraryExA(argv[1],NULL,LOAD_WITH_ALTERED_SEARCH_PATH);if(!dll)return 3;
    GetModuleFileNameA(dll,loaded,sizeof(loaded));if(lstrcmpiA(loaded,argv[1])!=0)return 4;
    open_file=(open_fn)GetProcAddress(dll,"@std@_Fiopen$qpxc23std@%_Iosb$i%@_Openmodei");
    write_file=(write_fn)GetProcAddress(dll,"_fwrite");close_file=(close_fn)GetProcAddress(dll,"_fclose");
    if(!open_file||!write_file||!close_file)return 5;
    if(!GetModuleFileNameA(NULL,output,sizeof(output)))return 11;
    slash=strrchr(output,'\\');if(!slash||strlen(argv[2])+strlen(output)>=MAX_PATH)return 12;
    strcpy(slash+1,argv[2]);
    file=open_file(output,mode,0x1b6);
    if(!file){printf("{\"opened\":false,\"mode\":%d}\n",mode);return 6;}
    written=write_file(payload,1,n/2,file);closed=close_file(file);
    printf("{\"opened\":true,\"mode\":%d,\"requested\":%u,\"written\":%u,\"close\":%d,\"ACP\":%u}\n",mode,n/2,written,closed,GetACP());
    return written==n/2&&closed==0?0:13;
}
