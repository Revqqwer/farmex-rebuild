/* Disposable own x86 process. Standard RTL calls only; no game process access.
 * First-exception observer exits this process, never redirects or resumes it.
 */
#define main previous_integer_fixture_main
#include "rtl_integer_fixture.c"
#undef main
/* Minimal pinned TCC Windows headers omit these zero-argument declarations. */
__declspec(dllimport) UINT WINAPI GetACP(void);
__declspec(dllimport) DWORD WINAPI GetThreadLocale(void);
__declspec(dllimport) DWORD WINAPI GetUserDefaultLCID(void);

static unsigned short *second_text;
static const char *operation;
static const char *phase="load";
static int initialized;
typedef LONG (CALLBACK *CompareObserver)(PEXCEPTION_POINTERS);
typedef PVOID (WINAPI *AddCompareObserver)(ULONG,CompareObserver);

static LONG CALLBACK observe_compare_exception(PEXCEPTION_POINTERS p) {
    printf("{\"event\":\"first_exception\",\"operation\":\"%s\",\"phase\":\"%s\",\"initialized\":%s,\"exception_code\":%lu}\n",
        operation,phase,initialized?"true":"false",p->ExceptionRecord->ExceptionCode);
    fflush(stdout);ExitProcess(0);return EXCEPTION_CONTINUE_SEARCH;
}

static int build_text(const char *hex,unsigned long *storage,unsigned short **out) {
    unsigned n,j;unsigned char *data=(unsigned char*)storage;
    if(strcmp(hex,"-")==0){*out=NULL;return 1;}
    n=strlen(hex);if(n%4||n>16000)return 0;
    memset(storage,0,8192);
    for(j=0;j<n;j+=2){
        int a,b;char x=hex[j],y=hex[j+1];
        a=x>='0'&&x<='9'?x-'0':x>='a'&&x<='f'?x-'a'+10:-1;
        b=y>='0'&&y<='9'?y-'0':y>='a'&&y<='f'?y-'a'+10:-1;
        if(a<0||b<0)return 0;data[12+j/2]=(unsigned char)(16*a+b);
    }
    storage[0]=0x000204b0UL;storage[1]=0xffffffffUL;storage[2]=n/4;
    *out=(unsigned short*)(data+12);return 1;
}

static void invoke_compare(void) {
    __asm__ __volatile__(
      "pushl %%ebx\n pushl %%esi\n pushl %%edi\n"
      "movl %%esp,%0\n movl %3,%%eax\n movl %4,%%edx\n call *%5\n"
      "movl %%eax,%2\n movl %%esp,%1\n"
      "popl %%edi\n popl %%esi\n popl %%ebx\n"
      : "=m"(before_sp),"=m"(after_sp),"=m"(result_eax)
      : "m"(text_ptr),"m"(second_text),"m"(target)
      : "eax","ecx","edx","memory","cc");
}

int main(int argc,char **argv) {
    HMODULE module;char loaded[MAX_PATH];const char *export_name;
    unsigned long first_storage[2048],second_storage[2048];
    void (*initialize)(void);AddCompareObserver observer;
    if(argc!=5||sizeof(void*)!=4)return 2;
    operation=argv[2];
    if(strcmp(operation,"compare")==0)export_name="@System@Sysutils@CompareText$qqrx20System@UnicodeStringt1";
    else if(strcmp(operation,"ansi")==0)export_name="@System@Sysutils@AnsiCompareText$qqrx20System@UnicodeStringt1";
    else if(strcmp(operation,"int")==0)export_name="@System@Sysutils@StrToInt$qqrx20System@UnicodeString";
    else return 12;
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    module=LoadLibraryExA(argv[1],NULL,LOAD_WITH_ALTERED_SEARCH_PATH);if(!module)return 3;
    GetModuleFileNameA(module,loaded,sizeof(loaded));if(lstrcmpiA(loaded,argv[1])!=0)return 6;
    target=(void*)GetProcAddress(module,export_name);if(!target)return 4;
    if(!build_text(argv[3],first_storage,&text_ptr)||!build_text(argv[4],second_storage,&second_text))return 7;
    observer=(AddCompareObserver)GetProcAddress(GetModuleHandleA("kernel32.dll"),"AddVectoredExceptionHandler");
    if(!observer||!observer(1,observe_compare_exception))return 9;
    initialize=(void(*)(void))GetProcAddress(module,"Initialize");if(!initialize)return 11;
    phase="initialize";initialize();initialized=1;
    phase="call";invoke_compare();
    printf("{\"event\":\"normal_return\",\"operation\":\"%s\",\"initialized\":true,\"eax\":%lu,\"signed_eax\":%ld,\"stack_unchanged\":%s,\"acp\":%u,\"thread_lcid\":%lu,\"user_lcid\":%lu}\n",
        operation,result_eax,(long)result_eax,before_sp==after_sp?"true":"false",GetACP(),GetThreadLocale(),GetUserDefaultLCID());
    fflush(stdout);ExitProcess(before_sp==after_sp?0:5);return 0;
}
