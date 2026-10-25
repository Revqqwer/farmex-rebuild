/* Own hidden x86 ListView + pinned standard RTL reference, no game HWND/PID. */
#define main previous_integer_fixture_main
#include "rtl_integer_fixture.c"
#undef main

typedef struct { DWORD size,classes; } OwnInit;
typedef struct { DWORD size,major,minor,build,platform; } OwnVersion;
typedef struct {
    UINT mask;int item,subitem;UINT state,state_mask;LPWSTR text;
    int text_max,image;LPARAM param;int indent,group_id;UINT columns;
    void *column_array,*formats;int group;
} OwnItem;
typedef struct { unsigned long storage[4][264];unsigned short *text[4]; } OwnRow;
typedef HWND (WINAPI *MakeWindow)(DWORD,LPCWSTR,LPCWSTR,DWORD,int,int,int,int,HWND,HMENU,HINSTANCE,LPVOID);
typedef LRESULT (WINAPI *Message)(HWND,UINT,WPARAM,LPARAM);
typedef BOOL (WINAPI *Destroy)(HWND);
typedef BOOL (WINAPI *Visible)(HWND);
typedef BOOL (WINAPI *InitControls)(OwnInit*);
typedef LONG (WINAPI *VersionQuery)(OwnVersion*);
typedef UINT (WINAPI *SystemDirectory)(LPSTR,UINT);
typedef DWORD (WINAPI *ModuleName)(HMODULE,LPWSTR,DWORD);
typedef LONG (CALLBACK *OwnObserver)(PEXCEPTION_POINTERS);
typedef PVOID (WINAPI *AddObserver)(ULONG,OwnObserver);
static OwnRow rows[64];static unsigned row_count,column,comparisons;
static void *compare_target,*ansi_target,*int_target,*int64_target;
static const char *phase="initialize";

static LONG CALLBACK observe(PEXCEPTION_POINTERS p) {
    printf("{\"event\":\"first_exception\",\"phase\":\"%s\",\"code\":%lu,\"column\":%u,\"comparisons\":%u,\"order_available\":false}\n",
        phase,p->ExceptionRecord->ExceptionCode,column,comparisons);
    fflush(stdout);ExitProcess(0);return EXCEPTION_CONTINUE_SEARCH;
}
static void gap(const char *name) {
    printf("{\"event\":\"scope_gap\",\"name\":\"%s\",\"comparisons\":%u,\"order_available\":false}\n",name,comparisons);
    fflush(stdout);ExitProcess(0);
}
static unsigned long call_one(void *fn,unsigned short *s) {
    target=fn;text_ptr=s;output_ptr=NULL;invoke_try();
    if(before_sp!=after_sp)ExitProcess(5);return result_eax;
}
static unsigned long price(unsigned short *s) {
    static unsigned long storage[264];unsigned short *clean=(unsigned short*)((unsigned char*)storage+12);
    unsigned n=s?((unsigned long*)s)[-1]:0,j,count=0;
    for(j=0;j<n;j++) {
        if(s[j]>127)gap("ANSI_conversion");
        if(s[j]!='.'&&(s[j]<'0'||s[j]>'9'))return 0;
    }
    if(n<=3)return call_one(int64_target,s);
    memset(storage,0,sizeof(storage));
    for(j=0;j<n;j++)if(s[j]!='.')clean[count++]=s[j];
    storage[0]=0x000204b0UL;storage[1]=0xffffffffUL;storage[2]=count;
    return call_one(int64_target,clean);
}
static int CALLBACK compare_rows(LPARAM first,LPARAM second,LPARAM parameter) {
    unsigned a=(unsigned)first-1,b=(unsigned)second-1;unsigned long x,y;
    comparisons++;phase="compare";
    if(a>=row_count||b>=row_count||parameter!=0)gap("own_token");
    if(column<2) {
        target=column?ansi_target:compare_target;text_ptr=rows[a].text[column];output_ptr=rows[b].text[column];
        invoke_try();if(before_sp!=after_sp)ExitProcess(5);return (int)result_eax;
    }
    if(column==2){x=call_one(int_target,rows[a].text[2]);y=call_one(int_target,rows[b].text[2]);}
    else if(column==3){x=price(rows[a].text[3]);y=price(rows[b].text[3]);}
    else {gap("unwritten_compare_result");return 0;}
    return (int)(x-y);
}
static int hex_value(char c){return c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:-1;}
static int read_text(OwnRow *row,unsigned field) {
    char line[2010];unsigned n,j;unsigned char *data=(unsigned char*)row->storage[field];
    if(!fgets(line,sizeof(line),stdin))return 0;
    n=strlen(line);while(n&&(line[n-1]=='\r'||line[n-1]=='\n'))line[--n]=0;
    if(n%4||n>2000)return 0;
    memset(data,0,sizeof(row->storage[field]));
    for(j=0;j<n;j+=2){int a=hex_value(line[j]),b=hex_value(line[j+1]);if(a<0||b<0)return 0;data[12+j/2]=(unsigned char)(16*a+b);}
    row->storage[field][0]=0x000204b0UL;row->storage[field][1]=0xffffffffUL;row->storage[field][2]=n/4;
    row->text[field]=(unsigned short*)(data+12);return 1;
}

int main(int argc,char **argv) {
    HMODULE rtl,user,controls,kernel;char loaded[MAX_PATH],system[MAX_PATH],path[MAX_PATH],line[80];
    WCHAR module_path[1024];OwnInit init;OwnVersion version;HWND parent,child;
    MakeWindow make;Message send;Destroy destroy;Visible visible;InitControls init_controls;
    VersionQuery query;SystemDirectory system_dir;ModuleName module_name;AddObserver add_observer;
    unsigned i,j;int ok,closed_child,closed_parent;unsigned order[64];void (*initialize)(void);
    if(argc!=3||sizeof(void*)!=4)return 2;
    column=strtoul(argv[2],NULL,10);
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    rtl=LoadLibraryExA(argv[1],NULL,LOAD_WITH_ALTERED_SEARCH_PATH);if(!rtl)return 3;
    GetModuleFileNameA(rtl,loaded,sizeof(loaded));if(lstrcmpiA(loaded,argv[1])!=0)return 6;
    compare_target=GetProcAddress(rtl,"@System@Sysutils@CompareText$qqrx20System@UnicodeStringt1");
    ansi_target=GetProcAddress(rtl,"@System@Sysutils@AnsiCompareText$qqrx20System@UnicodeStringt1");
    int_target=GetProcAddress(rtl,"@System@Sysutils@StrToInt$qqrx20System@UnicodeString");
    int64_target=GetProcAddress(rtl,"@System@Sysutils@StrToInt64$qqrx20System@UnicodeString");
    initialize=(void(*)(void))GetProcAddress(rtl,"Initialize");
    if(!compare_target||!ansi_target||!int_target||!int64_target||!initialize)return 4;
    kernel=GetModuleHandleA("kernel32.dll");
    add_observer=(AddObserver)GetProcAddress(kernel,"AddVectoredExceptionHandler");
    if(!add_observer||!add_observer(1,observe))return 9;initialize();
    if(!fgets(line,sizeof(line),stdin))return 7;row_count=strtoul(line,NULL,10);if(row_count>64)return 7;
    for(i=0;i<row_count;i++)for(j=0;j<4;j++)if(!read_text(&rows[i],j))return 7;
    system_dir=(SystemDirectory)GetProcAddress(kernel,"GetSystemDirectoryA");
    module_name=(ModuleName)GetProcAddress(kernel,"GetModuleFileNameW");
    if(!system_dir||!module_name||!system_dir(system,sizeof(system)))return 8;
    lstrcpyA(path,system);lstrcatA(path,"\\user32.dll");user=LoadLibraryA(path);
    lstrcpyA(path,system);lstrcatA(path,"\\comctl32.dll");controls=LoadLibraryA(path);
    if(!user||!controls)return 10;
    make=(MakeWindow)GetProcAddress(user,"CreateWindowExW");send=(Message)GetProcAddress(user,"SendMessageW");
    destroy=(Destroy)GetProcAddress(user,"DestroyWindow");visible=(Visible)GetProcAddress(user,"IsWindowVisible");
    init_controls=(InitControls)GetProcAddress(controls,"InitCommonControlsEx");query=(VersionQuery)GetProcAddress(controls,"DllGetVersion");
    if(!make||!send||!destroy||!visible||!init_controls||!query)return 11;
    init.size=sizeof(init);init.classes=1;if(!init_controls(&init))return 12;
    memset(&version,0,sizeof(version));version.size=sizeof(version);if(query(&version)!=0)return 13;
    if(!module_name(controls,module_path,1024))return 14;
    phase="control";parent=make(0,L"STATIC",L"",0x80000000UL,0,0,1,1,NULL,NULL,NULL,NULL);if(!parent)return 15;
    child=make(0,L"SysListView32",L"",0x40000001UL,0,0,1,1,parent,NULL,NULL,NULL);
    if(!child||visible(parent)||visible(child))return 16;
    for(i=0;i<row_count;i++) {
        OwnItem item;memset(&item,0,sizeof(item));item.mask=5;item.item=i;item.param=i+1;item.text=L"";
        if(send(child,0x104d,0,(LPARAM)&item)!=(LRESULT)i)return 17;
    }
    phase="sort";ok=send(child,0x1030,0,(LPARAM)compare_rows)!=0;
    if(send(child,0x1004,0,0)!=(LRESULT)row_count)return 18;
    for(i=0;i<row_count;i++) {
        OwnItem item;memset(&item,0,sizeof(item));item.mask=4;item.item=i;
        if(!send(child,0x104b,0,(LPARAM)&item))return 19;order[i]=(unsigned)item.param-1;
    }
    closed_child=destroy(child);closed_parent=destroy(parent);
    printf("{\"event\":\"sort_return\",\"sort_result\":%s,\"column\":%u,\"comparisons\":%u,\"cleanup_verified\":%s,\"item_size\":%u,\"comctl_version\":[%lu,%lu,%lu],\"comctl_path_hex\":\"",
        ok?"true":"false",column,comparisons,closed_child&&closed_parent?"true":"false",(unsigned)sizeof(OwnItem),version.major,version.minor,version.build);
    for(i=0;module_path[i];i++)printf("%02x%02x",module_path[i]&255,module_path[i]>>8);
    printf("\",\"order\":[");for(i=0;i<row_count;i++)printf("%s%u",i?",":"",order[i]);printf("]}\n");
    fflush(stdout);ExitProcess(ok&&closed_child&&closed_parent?0:20);return 0;
}
