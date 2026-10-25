/* Own disposable x86 process, standard RTL only. No game or bot runtime. */
#define main previous_integer_fixture_main
#include "rtl_integer_fixture.c"
#undef main
__declspec(dllimport) UINT WINAPI GetACP(void);
__declspec(dllimport) DWORD WINAPI GetThreadLocale(void);
__declspec(dllimport) DWORD WINAPI GetUserDefaultLCID(void);

static void *upper_target,*conversion_target;
static unsigned short *unicode_output;
static unsigned char *ansi_output;
static const char *phase="load";
static unsigned long upper_before,upper_after,convert_before,convert_after;
typedef LONG (CALLBACK *UpperObserver)(PEXCEPTION_POINTERS);
typedef PVOID (WINAPI *AddUpperObserver)(ULONG,UpperObserver);

static LONG CALLBACK upper_exception(PEXCEPTION_POINTERS p) {
    printf("{\"event\":\"first_exception\",\"phase\":\"%s\",\"code\":%lu}\n",phase,p->ExceptionRecord->ExceptionCode);
    fflush(stdout);ExitProcess(0);return EXCEPTION_CONTINUE_SEARCH;
}

static int build_upper_input(const char *hex,unsigned long *storage,int wide) {
    unsigned n=strlen(hex),j;unsigned char *bytes=(unsigned char*)storage;
    if(n>12000||n%2||(wide&&n%4))return 0;
    memset(storage,0,8192);
    for(j=0;j<n;j+=2) {
        int a,b;char x=hex[j],y=hex[j+1];
        a=x>='0'&&x<='9'?x-'0':x>='a'&&x<='f'?x-'a'+10:-1;
        b=y>='0'&&y<='9'?y-'0':y>='a'&&y<='f'?y-'a'+10:-1;
        if(a<0||b<0)return 0;bytes[12+j/2]=(unsigned char)(16*a+b);
    }
    storage[0]=wide?0x000204b0UL:0x00010000UL;
    storage[1]=0xffffffffUL;storage[2]=wide?n/4:n/2;
    text_ptr=n?(unsigned short*)(bytes+12):NULL;return 1;
}

static void invoke_upper(int wide) {
    void *out=wide?(void*)&unicode_output:(void*)&ansi_output;
    __asm__ __volatile__(
        "pushl %%ebx\n pushl %%esi\n pushl %%edi\n"
        "movl %%esp,%0\n movl %2,%%eax\n movl %3,%%edx\n call *%4\n"
        "movl %%esp,%1\n popl %%edi\n popl %%esi\n popl %%ebx\n"
        : "=m"(upper_before),"=m"(upper_after)
        : "m"(text_ptr),"m"(out),"m"(upper_target)
        : "eax","ecx","edx","memory","cc");
}

static void invoke_conversion(void) {
    void *out=&ansi_output;
    __asm__ __volatile__(
        "pushl %%ebx\n pushl %%esi\n pushl %%edi\n"
        "movl %%esp,%0\n movl %2,%%eax\n movl %3,%%edx\n xorl %%ecx,%%ecx\n call *%4\n"
        "movl %%esp,%1\n popl %%edi\n popl %%esi\n popl %%ebx\n"
        : "=m"(convert_before),"=m"(convert_after)
        : "m"(out),"m"(unicode_output),"m"(conversion_target)
        : "eax","ecx","edx","memory","cc");
}

static void print_hex(const unsigned char *p,unsigned n) {
    unsigned i;for(i=0;i<n;i++)printf("%02x",p[i]);
}

int main(int argc,char **argv) {
    HMODULE module;char loaded[MAX_PATH];int wide;unsigned long storage[2048];
    unsigned long units,bytes;unsigned short *default_cp;void (*initialize)(void);AddUpperObserver observer;
    if(argc!=4||sizeof(void*)!=4)return 2;
    if(strcmp(argv[2],"query")==0)wide=1;
    else if(strcmp(argv[2],"ansi")==0)wide=0;
    else return 12;
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    module=LoadLibraryExA(argv[1],NULL,LOAD_WITH_ALTERED_SEARCH_PATH);if(!module)return 3;
    GetModuleFileNameA(module,loaded,sizeof(loaded));if(lstrcmpiA(loaded,argv[1])!=0)return 6;
    upper_target=(void*)GetProcAddress(module,wide?
      "@System@Sysutils@AnsiUpperCase$qqrx20System@UnicodeString":
      "@System@Ansistrings@AnsiUpperCase$qqrx27System@%AnsiStringT$us$i0$%");
    conversion_target=(void*)GetProcAddress(module,"@System@@LStrFromUStr$qqrr27System@%AnsiStringT$us$i0$%x20System@UnicodeStringus");
    default_cp=(unsigned short*)GetProcAddress(module,"@System@DefaultSystemCodePage");
    if(!upper_target||!conversion_target||!default_cp)return 4;
    if(!build_upper_input(argv[3],storage,wide))return 7;
    observer=(AddUpperObserver)GetProcAddress(GetModuleHandleA("kernel32.dll"),"AddVectoredExceptionHandler");
    if(!observer||!observer(1,upper_exception))return 9;
    initialize=(void(*)(void))GetProcAddress(module,"Initialize");if(!initialize)return 11;
    phase="initialize";initialize();phase="upper";invoke_upper(wide);
    if(upper_before!=upper_after)return 5;
    if(wide){phase="conversion";invoke_conversion();if(convert_before!=convert_after)return 5;}
    units=unicode_output?((unsigned long*)unicode_output)[-1]:0;
    bytes=ansi_output?((unsigned long*)ansi_output)[-1]:0;
    if(units>4000||bytes>16000)return 13;
    printf("{\"event\":\"normal_return\",\"operation\":\"%s\",\"stack_unchanged\":true,\"unicode_hex\":\"",argv[2]);
    print_hex((unsigned char*)unicode_output,units*2);
    printf("\",\"ansi_hex\":\"");print_hex(ansi_output,bytes);
    printf("\",\"output_codepage\":%u,\"rtl_default_codepage\":%u,\"acp\":%u,\"thread_lcid\":%lu,\"user_lcid\":%lu}\n",
      ansi_output?((unsigned short*)ansi_output)[-6]:0,*default_cp,GetACP(),GetThreadLocale(),GetUserDefaultLCID());
    fflush(stdout);ExitProcess(0);return 0;
}
