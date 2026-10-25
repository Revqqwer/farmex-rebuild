/* Own x86 standard RTL StrToFloat followed by source-shaped FSTP32. */
#define main previous_integer_fixture_main
#include "rtl_integer_fixture.c"
#undef main
__declspec(dllimport) UINT WINAPI GetACP(void);
__declspec(dllimport) DWORD WINAPI GetThreadLocale(void);
__declspec(dllimport) DWORD WINAPI GetUserDefaultLCID(void);
static unsigned long float_bits,case_index;
static unsigned short control_before,control_after,status_before,status_after;
static const char *phase="load";
typedef LONG (CALLBACK *FloatObserver)(PEXCEPTION_POINTERS);
typedef PVOID (WINAPI *AddFloatObserver)(ULONG,FloatObserver);

static LONG CALLBACK float_exception(PEXCEPTION_POINTERS p) {
    printf("{\"event\":\"first_exception\",\"index\":%lu,\"phase\":\"%s\",\"code\":%lu}\n",
        case_index,phase,p->ExceptionRecord->ExceptionCode);
    fflush(stdout);ExitProcess(0);return EXCEPTION_CONTINUE_SEARCH;
}

static int build_float_input(const char *hex,unsigned long *storage) {
    unsigned n=strlen(hex),j;unsigned char *bytes=(unsigned char*)storage;
    if(n>12000||n%4)return 0;
    memset(storage,0,8192);
    for(j=0;j<n;j+=2) {
        int a,b;char x=hex[j],y=hex[j+1];
        a=x>='0'&&x<='9'?x-'0':x>='a'&&x<='f'?x-'a'+10:-1;
        b=y>='0'&&y<='9'?y-'0':y>='a'&&y<='f'?y-'a'+10:-1;
        if(a<0||b<0)return 0;bytes[12+j/2]=(unsigned char)(16*a+b);
    }
    storage[0]=0x000204b0UL;storage[1]=0xffffffffUL;storage[2]=n/4;
    text_ptr=n?(unsigned short*)(bytes+12):NULL;return 1;
}

static void invoke_float(void) {
    __asm__ __volatile__(
        "pushl %%ebx\n pushl %%esi\n pushl %%edi\n"
        "movl %%esp,%0\n fnstcw %3\n fnstsw %5\n"
        "movl %7,%%eax\n call *%8\n fstps %2\n"
        "fnstcw %4\n fnstsw %6\n movl %%esp,%1\n"
        "popl %%edi\n popl %%esi\n popl %%ebx\n"
        : "=m"(before_sp),"=m"(after_sp),"=m"(float_bits),
          "=m"(control_before),"=m"(control_after),"=m"(status_before),"=m"(status_after)
        : "m"(text_ptr),"m"(target)
        : "eax","ecx","edx","memory","cc");
}

static int run_case(const char *hex) {
    unsigned long storage[2048];
    if(!build_float_input(hex,storage))return 7;
    phase="StrToFloat_FSTP32";invoke_float();
    printf("{\"event\":\"normal_return\",\"index\":%lu,\"bits\":%lu,\"control_before\":%u,\"control_after\":%u,\"status_before\":%u,\"status_after\":%u,\"stack_unchanged\":%s,\"acp\":%u,\"thread_lcid\":%lu,\"user_lcid\":%lu}\n",
        case_index,float_bits,control_before,control_after,status_before,status_after,
        before_sp==after_sp?"true":"false",GetACP(),GetThreadLocale(),GetUserDefaultLCID());
    fflush(stdout);case_index++;return before_sp==after_sp?0:5;
}

int main(int argc,char **argv) {
    HMODULE module;char loaded[MAX_PATH],line[16010];int code;
    void (*initialize)(void);AddFloatObserver observer;
    if(argc!=3||sizeof(void*)!=4)return 2;
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    module=LoadLibraryExA(argv[1],NULL,LOAD_WITH_ALTERED_SEARCH_PATH);if(!module)return 3;
    GetModuleFileNameA(module,loaded,sizeof(loaded));if(lstrcmpiA(loaded,argv[1])!=0)return 6;
    target=(void*)GetProcAddress(module,"@System@Sysutils@StrToFloat$qqrx20System@UnicodeString");if(!target)return 4;
    observer=(AddFloatObserver)GetProcAddress(GetModuleHandleA("kernel32.dll"),"AddVectoredExceptionHandler");
    if(!observer||!observer(1,float_exception))return 9;
    initialize=(void(*)(void))GetProcAddress(module,"Initialize");if(!initialize)return 11;
    phase="initialize";initialize();
    if(strcmp(argv[2],"--stream")!=0)return run_case(argv[2]);
    while(fgets(line,sizeof(line),stdin)) {
        line[strcspn(line,"\r\n")]=0;
        code=run_case(line);if(code)return code;
    }
    return 0;
}
