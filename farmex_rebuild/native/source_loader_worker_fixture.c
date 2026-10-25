/* Original431-byte worker, owned synthetic image and API shims only. No args. */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include "source_loader_worker_template.h"

typedef struct WorkerContext {
 DWORD image,nt,relocs,imports;
 HMODULE (WINAPI *load)(LPCSTR);
 FARPROC (WINAPI *symbol)(HMODULE,LPCSTR);
} WorkerContext;
typedef DWORD (WINAPI *Worker)(WorkerContext *);
static BYTE *image;
static unsigned load_calls,symbol_calls,entry_calls,ordinal_calls,name_calls;
static unsigned fail_load,fail_symbol,entry_result,entry_arguments_valid;
static HMODULE fake_module=(HMODULE)0x12340000;

static void own_export(void) {}
static BOOL WINAPI own_entry(HINSTANCE module,DWORD reason,LPVOID reserved) {
 entry_calls++;
 entry_arguments_valid=(module==(HINSTANCE)image && reason==1 && reserved==NULL);
 return (BOOL)entry_result;
}
static HMODULE WINAPI own_load(LPCSTR name) {
 load_calls++;
 if(name!=(LPCSTR)(image+0x740) || strcmp(name,"fixture.dll"))ExitProcess(71);
 return fail_load?NULL:fake_module;
}
static FARPROC WINAPI own_symbol(HMODULE module,LPCSTR name) {
 symbol_calls++;
 if(module!=fake_module)ExitProcess(72);
 if((DWORD)name==42)ordinal_calls++;
 else {
  if(name!=(LPCSTR)(image+0x702) || strcmp(name,"fixture_symbol"))ExitProcess(73);
  name_calls++;
 }
 return fail_symbol?NULL:(FARPROC)own_export;
}
static void reset_image(WorkerContext *context,DWORD delta) {
 IMAGE_NT_HEADERS32 *nt;BYTE *entry;DWORD function;
 memset(image,0,4096);
 load_calls=symbol_calls=entry_calls=ordinal_calls=name_calls=0;
 fail_load=fail_symbol=0;entry_result=1;entry_arguments_valid=0;
 nt=(IMAGE_NT_HEADERS32 *)(image+0x80);
 nt->Signature=IMAGE_NT_SIGNATURE;nt->FileHeader.Machine=IMAGE_FILE_MACHINE_I386;
 nt->OptionalHeader.Magic=IMAGE_NT_OPTIONAL_HDR32_MAGIC;
 nt->OptionalHeader.ImageBase=(DWORD)image-delta;
 context->image=(DWORD)image;context->nt=(DWORD)nt;
 context->relocs=(DWORD)(image+0x300);context->imports=(DWORD)(image+0x400);
 context->load=own_load;context->symbol=own_symbol;
 strcpy((char *)(image+0x740),"fixture.dll");
 *(WORD *)(image+0x700)=0x1234;strcpy((char *)(image+0x702),"fixture_symbol");
 /* Owned synthetic entry jumps to own C callback solely to inspect its args. */
 entry=image+0x800;entry[0]=0xb8;function=(DWORD)own_entry;
 memcpy(entry+1,&function,4);entry[5]=0xff;entry[6]=0xe0;
}
static void enable_entry(void) {
 ((IMAGE_NT_HEADERS32 *)(image+0x80))->OptionalHeader.AddressOfEntryPoint=0x800;
}
static void import_table(int ordinal) {
 IMAGE_IMPORT_DESCRIPTOR *d=(IMAGE_IMPORT_DESCRIPTOR *)(image+0x400);
 d[0].OriginalFirstThunk=0x500;d[0].Name=0x740;d[0].FirstThunk=0x600;
 *(DWORD *)(image+0x500)=ordinal?0x8000002a:0x700;
}
static void reloc_table(WORD first,WORD second) {
 IMAGE_BASE_RELOCATION *r=(IMAGE_BASE_RELOCATION *)(image+0x300);
 r->VirtualAddress=0x900;r->SizeOfBlock=12;
 *(WORD *)(image+0x308)=first;*(WORD *)(image+0x30a)=second;
 *(DWORD *)(image+0x904)=0x12345678;
 *(DWORD *)(image+0x908)=0x22446688;
}
static unsigned check(const char *name,DWORD result,DWORD expected,unsigned loads,unsigned symbols,unsigned entries,DWORD target,DWORD iat) {
 if(result!=expected || load_calls!=loads || symbol_calls!=symbols || entry_calls!=entries ||
    (entries && !entry_arguments_valid) || *(DWORD *)(image+0x904)!=target || *(DWORD *)(image+0x600)!=iat)return 0;
 printf("{\"kind\":\"case\",\"case\":\"%s\",\"result\":%u,\"loads\":%u,\"symbols\":%u,\"ordinal_calls\":%u,\"name_calls\":%u,\"entry_calls\":%u,\"entry_arguments_valid\":%s,\"target_dword\":%u,\"iat_matches_owned_export\":%s,\"passed\":true}\n",
  name,result,loads,symbols,ordinal_calls,name_calls,entries,entries?"true":"false",target,iat?"true":"false");
 return 1;
}
int main(int argc,char **argv) {
 BYTE *code;DWORD old,result;Worker worker;WorkerContext context;unsigned passed=0;
 (void)argv;if(argc!=1 || sizeof(void *)!=4 || sizeof(context)!=24)return 10;
 image=(BYTE *)VirtualAlloc(NULL,4096,MEM_RESERVE|MEM_COMMIT,PAGE_EXECUTE_READWRITE);
 code=(BYTE *)VirtualAlloc(NULL,4096,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
 if(!image || !code)return 11;
 memcpy(code,source_loader_worker_code,sizeof(source_loader_worker_code));
 if(memcmp(code,source_loader_worker_code,sizeof(source_loader_worker_code)))return 12;
 if(!VirtualProtect(code,4096,PAGE_EXECUTE_READ,&old) || !FlushInstructionCache(GetCurrentProcess(),code,sizeof(source_loader_worker_code)))return 13;
 worker=(Worker)code;
 printf("{\"kind\":\"worker\",\"instructions\":152,\"source_bytes\":431,\"patches\":0,\"exact_bytes\":true,\"code_rx\":true,\"owned_image_only\":true}\n");
 reset_image(&context,0);result=worker(&context);passed+=check("empty_directories_no_entry",result,1,0,0,0,0,0);
 reset_image(&context,0);enable_entry();result=worker(&context);passed+=check("entry_true",result,1,0,0,1,0,0);
 reset_image(&context,0);enable_entry();entry_result=0;result=worker(&context);passed+=check("entry_false",result,0,0,0,1,0,0);
 reset_image(&context,0);enable_entry();entry_result=0x12345678;result=worker(&context);passed+=check("entry_full_eax",result,0x12345678,0,0,1,0,0);
 reset_image(&context,0);import_table(0);enable_entry();fail_load=1;result=worker(&context);passed+=check("load_failure",result,0,1,0,0,0,0);
 reset_image(&context,0);import_table(0);enable_entry();fail_symbol=1;result=worker(&context);passed+=check("name_failure",result,0,1,1,0,0,0);
 reset_image(&context,0);import_table(1);enable_entry();fail_symbol=1;result=worker(&context);passed+=check("ordinal_failure",result,0,1,1,0,0,0);
 reset_image(&context,0);import_table(0);result=worker(&context);passed+=check("name_success",result,1,1,1,0,0,(DWORD)own_export);
 reset_image(&context,0);import_table(1);result=worker(&context);passed+=check("ordinal_success",result,1,1,1,0,0,(DWORD)own_export);
 reset_image(&context,0x1000);reloc_table(0x3004,0);result=worker(&context);passed+=check("highlow_positive_delta",result,1,0,0,0,0x12346678,0);
 reset_image(&context,0xfffff000);reloc_table(0x3004,0);result=worker(&context);passed+=check("highlow_negative_delta",result,1,0,0,0,0x12344678,0);
 reset_image(&context,0x1000);reloc_table(0x1004,0);result=worker(&context);passed+=check("type1_still_adds_dword",result,1,0,0,0,0x12346678,0);
 reset_image(&context,0x1000);reloc_table(0,0);result=worker(&context);passed+=check("zero_reloc_entries_skip",result,1,0,0,0,0x12345678,0);
 reset_image(&context,0);import_table(0);*(DWORD *)(image+0x400)=0;result=worker(&context);passed+=check("zero_oft_stops_descriptor",result,1,0,0,0,0,0);
 reset_image(&context,0x1000);reloc_table(0x3004,0);import_table(0);enable_entry();result=worker(&context);passed+=check("reloc_import_entry_chain",result,1,1,1,1,0x12346678,(DWORD)own_export);
 printf("{\"kind\":\"summary\",\"passed\":%u,\"original_dll_loaded\":false,\"external_process_access\":false,\"game_actions\":0}\n",passed);
 VirtualFree(code,0,MEM_RELEASE);VirtualFree(image,0,MEM_RELEASE);
 return passed==15?0:70;
}
