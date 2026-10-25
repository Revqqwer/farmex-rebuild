/* Own initialized x86 process: stream immutable UTF16 inputs to ValLong.
 * Reuses only register-call plumbing; never accesses another process.
 */
#define main previous_integer_fixture_main
#include "rtl_integer_fixture.c"
#undef main

static unsigned long val_code;
static int nibble(char c) {
    return c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:-1;
}

int main(int argc,char **argv) {
    HMODULE module;char loaded[MAX_PATH],line[16008];unsigned long storage[2048];
    unsigned index=0,n,j;unsigned char *data=(unsigned char*)storage;
    void (*initialize)(void);
    if(argc!=2||sizeof(void*)!=4)return 2;
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    module=LoadLibraryExA(argv[1],NULL,LOAD_WITH_ALTERED_SEARCH_PATH);if(!module)return 3;
    GetModuleFileNameA(module,loaded,sizeof(loaded));if(lstrcmpiA(loaded,argv[1])!=0)return 6;
    target=(void*)GetProcAddress(module,"@System@@ValLong$qqrx20System@UnicodeStringri");if(!target)return 4;
    initialize=(void(*)(void))GetProcAddress(module,"Initialize");if(!initialize)return 11;
    initialize();output_ptr=(void*)&val_code;
    while(fgets(line,sizeof(line),stdin)) {
        n=strlen(line);while(n&&(line[n-1]=='\r'||line[n-1]=='\n'))line[--n]=0;
        memset(storage,0,sizeof(storage));
        if(strcmp(line,"-")==0)text_ptr=NULL;
        else {
            if(n%4||n>16000)return 7;
            for(j=0;j<n;j+=2) {
                int a=nibble(line[j]),b=nibble(line[j+1]);if(a<0||b<0)return 8;
                data[12+j/2]=(unsigned char)(16*a+b);
            }
            storage[0]=0x000204b0UL;storage[1]=0xffffffffUL;storage[2]=n/4;
            text_ptr=(unsigned short*)(data+12);
        }
        val_code=0xfeedfaceUL;invoke_try();
        printf("{\"case\":%u,\"eax\":%lu,\"code\":%lu,\"stack_unchanged\":%s}\n",
            index++,result_eax,val_code,before_sp==after_sp?"true":"false");
        if(before_sp!=after_sp)return 5;
    }
    fflush(stdout);ExitProcess(0);return 0;
}
