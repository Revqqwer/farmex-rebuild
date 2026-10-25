/* Extends the fixed-case own fixture with UTF16 hex stdin and Code capture. */
#define main fixed_case_main
#include "rtl_integer_fixture.c"
#undef main

static void *val_target,*code_ptr;
static unsigned long val_code,val_low,val_high,val_before,val_after;
static void invoke_val(void) {
    __asm__ __volatile__(
      "pushl %%ebx\n pushl %%esi\n pushl %%edi\n"
      "movl %%esp,%0\n movl %4,%%eax\n movl %5,%%edx\n call *%6\n"
      "movl %%eax,%2\n movl %%edx,%3\n movl %%esp,%1\n"
      "popl %%edi\n popl %%esi\n popl %%ebx\n"
      : "=m"(val_before),"=m"(val_after),"=m"(val_low),"=m"(val_high)
      : "m"(text_ptr),"m"(code_ptr),"m"(val_target)
      : "eax","ecx","edx","memory","cc");
}
static int nibble(char c) {
    if(c>='0'&&c<='9')return c-'0';
    if(c>='a'&&c<='f')return c-'a'+10;
    return -1;
}
int main(int argc,char **argv) {
    HMODULE module;char loaded[MAX_PATH],line[16384];unsigned long storage[4096];
    unsigned case_id=0,n,j,k,byte_value,is_null;
    unsigned char *data=(unsigned char*)storage;
    if(argc!=2||sizeof(void*)!=4)return 2;
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    module=LoadLibraryExA(argv[1],NULL,LOAD_WITH_ALTERED_SEARCH_PATH);if(!module)return 3;
    GetModuleFileNameA(module,loaded,sizeof(loaded));if(lstrcmpiA(loaded,argv[1])!=0)return 6;
    target=(void*)GetProcAddress(module,"@System@Sysutils@TryStrToInt64$qqrx20System@UnicodeStringrj");
    val_target=(void*)GetProcAddress(module,"@System@@ValInt64$qqrx20System@UnicodeStringri");
    if(!target||!val_target)return 4;
    output_ptr=(void*)result_pair;code_ptr=(void*)&val_code;
    while(fgets(line,sizeof(line),stdin)) {
        n=strcspn(line,"\r\n");line[n]=0;is_null=strcmp(line,"null")==0;
        if(!is_null&&(n%4||n>16000))return 7;
        memset(storage,0,sizeof(storage));
        if(!is_null)for(j=0;j<n;j+=2) {
            int a=nibble(line[j]),b=nibble(line[j+1]);if(a<0||b<0)return 8;
            data[12+j/2]=(unsigned char)(16*a+b);
        }
        storage[0]=0x000204b0UL;storage[1]=0xffffffffUL;storage[2]=n/4;
        text_ptr=is_null?NULL:(unsigned short*)(data+12);
        result_pair[0]=0x89abcdefUL;result_pair[1]=0x01234567UL;
        invoke_try();val_code=0xabcdef01UL;invoke_val();
        printf("{\"case\":%u,\"accepted_al\":%u,\"try_result_hex\":\"%08lx%08lx\",\"val_result_hex\":\"%08lx%08lx\",\"code\":%lu,\"stack_unchanged\":%s}\n",
          case_id++,(unsigned)(result_eax&255),result_pair[1],result_pair[0],val_high,val_low,val_code,
          before_sp==after_sp&&val_before==val_after?"true":"false");
        if(before_sp!=after_sp||val_before!=val_after)return 5;
    }
    FreeLibrary(module);return 0;
}
