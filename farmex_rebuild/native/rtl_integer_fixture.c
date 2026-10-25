/* Own x86 process only. Calls pinned standard RTL export, never a game PID.
 * Caller must validate the module hash and inspected register ABI first.
 * Input is an immutable Delphi UnicodeString with static refcount=-1.
 */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static void *target;
static unsigned short *text_ptr;
static unsigned long out_low,out_high,result_eax,before_sp,after_sp;
static unsigned long result_pair[2];
static void *output_ptr;

static void invoke_try(void) {
    __asm__ __volatile__(
      "pushl %%ebx\n pushl %%esi\n pushl %%edi\n"
      "movl %%esp,%0\n movl %3,%%eax\n movl %4,%%edx\n call *%5\n"
      "movl %%eax,%2\n movl %%esp,%1\n"
      "popl %%edi\n popl %%esi\n popl %%ebx\n"
      : "=m"(before_sp),"=m"(after_sp),"=m"(result_eax)
      : "m"(text_ptr),"m"(output_ptr),"m"(target)
      : "eax","ecx","edx","memory","cc");
}

int main(int argc,char **argv) {
    HMODULE module;char loaded[MAX_PATH];unsigned i,j,len;
    unsigned char storage[8192];unsigned long *header=(unsigned long*)storage;
    const char *cases[]={"","0","+0","-0"," 5","5 ","\t5","\n5","$10","0x10","0X10","x10","X10",
      "-$10","+$10","-0x10","0x-10","$-10","ffffffffffffffff","$ffffffffffffffff","0xffffffffffffffff",
      "-9223372036854775808","9223372036854775807","9223372036854775808","18446744073709551615",
      "-18446744073709551615","0x8000000000000000","-0x8000000000000000","0x10000000000000000",
      "++5","0x","$","0000000000000000000000000000000000000000000000000000000005","1_000","- 5","+ 5",
      "5\t","5\n","$FFFFFFFFFFFFFFFE","-0xFFFFFFFFFFFFFFFF","+$FFFFFFFFFFFFFFFF","-0x8000000000000001",
      "  $10","  +5","0XfF","0b101","%101","&17","0o17"};
    if (argc!=2||sizeof(void*)!=4)return 2;
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    module=LoadLibraryExA(argv[1],NULL,LOAD_WITH_ALTERED_SEARCH_PATH);
    if (!module) {printf("{\"load_error\":%lu}\n",GetLastError());return 3;}
    GetModuleFileNameA(module,loaded,sizeof(loaded));
    if (lstrcmpiA(loaded,argv[1])!=0) {printf("{\"loaded_path_mismatch\":true}\n");FreeLibrary(module);return 6;}
    target=(void*)GetProcAddress(module,"@System@Sysutils@TryStrToInt64$qqrx20System@UnicodeStringrj");
    if (!target)return 4;
    output_ptr=(void*)result_pair;
    for (i=0;i<sizeof(cases)/sizeof(cases[0])+3;i++) {
        memset(storage,0,sizeof(storage));text_ptr=(unsigned short*)(storage+12);
        len=i<sizeof(cases)/sizeof(cases[0])?strlen(cases[i]):1;
        if (i<sizeof(cases)/sizeof(cases[0]))for (j=0;j<len;j++)text_ptr[j]=(unsigned char)cases[i][j];
        else if (i==sizeof(cases)/sizeof(cases[0])) {text_ptr[0]='5';text_ptr[1]=0;text_ptr[2]='x';len=3;}
        else if (i==sizeof(cases)/sizeof(cases[0])+1)text_ptr[0]=0xff15;
        else text_ptr[0]=0x00a0;
        header[0]=0x000204b0UL;header[1]=0xffffffffUL;header[2]=len;
        result_pair[0]=0x89abcdefUL;result_pair[1]=0x01234567UL;
        invoke_try();out_low=result_pair[0];out_high=result_pair[1];
        printf("{\"case\":%u,\"utf16_hex\":\"",i);
        for(j=0;j<len;j++)printf("%02x%02x",text_ptr[j]&255,text_ptr[j]>>8);
        printf("\",\"eax\":%lu,\"accepted_al\":%u,\"result_hex\":\"%08lx%08lx\",\"stack_unchanged\":%s}\n",
          result_eax,(unsigned)(result_eax&255),out_high,out_low,before_sp==after_sp?"true":"false");
        if(before_sp!=after_sp)return 5;
    }
    FreeLibrary(module);return 0;
}
