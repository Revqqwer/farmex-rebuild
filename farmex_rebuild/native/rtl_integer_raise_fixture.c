/* Own disposable process: observe StrToInt64's first exception, then exit.
 * Does not redirect EIP, resume an exception, unwind bot code, or access PIDs.
 */
#define main fixed_case_main
#include "rtl_integer_fixture.c"
#undef main
static void *str_target;
static unsigned long str_low,str_high,str_before,str_after;
static unsigned long rtl_base,rtl_size;
static const char *phase="load";
static int initialized;
typedef LONG (CALLBACK *ObserverFn)(PEXCEPTION_POINTERS);
typedef PVOID (WINAPI *AddObserverFn)(ULONG,ObserverFn);
static LONG CALLBACK observe_exception(PEXCEPTION_POINTERS info) {
    unsigned long address=(unsigned long)info->ExceptionRecord->ExceptionAddress;
    printf("{\"event\":\"first_exception\",\"phase\":\"%s\",\"initialized\":%s,\"exception_code\":%lu,\"exception_address\":%lu,\"parameters\":%lu,\"exception_rva\":",
      phase,initialized?"true":"false",info->ExceptionRecord->ExceptionCode,address,info->ExceptionRecord->NumberParameters);
    if(address>=rtl_base&&address-rtl_base<rtl_size)printf("%lu",address-rtl_base);else printf("null");
    if(info->ExceptionRecord->ExceptionCode==0xc0000005UL&&info->ExceptionRecord->NumberParameters>=2)
        printf(",\"access_operation\":%lu,\"fault_address\":%lu",info->ExceptionRecord->ExceptionInformation[0],info->ExceptionRecord->ExceptionInformation[1]);
    printf("}\n");
    fflush(stdout);ExitProcess(0);return EXCEPTION_CONTINUE_SEARCH;
}
static void invoke_str(void) {
    __asm__ __volatile__(
      "pushl %%ebx\n pushl %%esi\n pushl %%edi\n"
      "movl %%esp,%0\n movl %4,%%eax\n call *%5\n"
      "movl %%eax,%2\n movl %%edx,%3\n movl %%esp,%1\n"
      "popl %%edi\n popl %%esi\n popl %%ebx\n"
      : "=m"(str_before),"=m"(str_after),"=m"(str_low),"=m"(str_high)
      : "m"(text_ptr),"m"(str_target)
      : "eax","ecx","edx","memory","cc");
}
int main(int argc,char **argv) {
    HMODULE module;char loaded[MAX_PATH];unsigned long storage[4096];AddObserverFn add_observer;
    unsigned n,j;unsigned char *data=(unsigned char*)storage;
    if((argc!=3&&argc!=4)||sizeof(void*)!=4)return 2;
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    module=LoadLibraryExA(argv[1],NULL,LOAD_WITH_ALTERED_SEARCH_PATH);if(!module)return 3;
    rtl_base=(unsigned long)module;
    rtl_size=((IMAGE_NT_HEADERS*)((unsigned char*)module+((IMAGE_DOS_HEADER*)module)->e_lfanew))->OptionalHeader.SizeOfImage;
    GetModuleFileNameA(module,loaded,sizeof(loaded));if(lstrcmpiA(loaded,argv[1])!=0)return 6;
    str_target=(void*)GetProcAddress(module,"@System@Sysutils@StrToInt64$qqrx20System@UnicodeString");if(!str_target)return 4;
    n=strlen(argv[2]);if(n%4||n>16000)return 7;
    memset(storage,0,sizeof(storage));
    for(j=0;j<n;j+=2) {
        int a,b;char x=argv[2][j],y=argv[2][j+1];
        a=x>='0'&&x<='9'?x-'0':x>='a'&&x<='f'?x-'a'+10:-1;
        b=y>='0'&&y<='9'?y-'0':y>='a'&&y<='f'?y-'a'+10:-1;
        if(a<0||b<0)return 8;data[12+j/2]=(unsigned char)(16*a+b);
    }
    storage[0]=0x000204b0UL;storage[1]=0xffffffffUL;storage[2]=n/4;
    text_ptr=(unsigned short*)(data+12);
    add_observer=(AddObserverFn)GetProcAddress(GetModuleHandleA("kernel32.dll"),"AddVectoredExceptionHandler");
    if(!add_observer||!add_observer(1,observe_exception))return 9;
    if(argc==4) {
        void (*initialize)(void);
        if(strcmp(argv[3],"initialize")!=0)return 10;
        initialize=(void(*)(void))GetProcAddress(module,"Initialize");if(!initialize)return 11;
        phase="initialize";initialize();initialized=1;
    }
    phase="parse";
    invoke_str();
    printf("{\"event\":\"normal_return\",\"initialized\":%s,\"result_hex\":\"%08lx%08lx\",\"stack_unchanged\":%s}\n",initialized?"true":"false",str_high,str_low,str_before==str_after?"true":"false");
    fflush(stdout);ExitProcess(str_before==str_after?0:5);return 0;
}
