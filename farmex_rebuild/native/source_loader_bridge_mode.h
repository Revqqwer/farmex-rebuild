/* Only included by the pinned own bridge host under FARMEX_SOURCE_LOADER_WORKER. */
#include "source_loader_worker_template.h"
typedef struct OwnSourceContext {
 DWORD image,nt,relocs,imports;
 HMODULE (WINAPI *load)(LPCSTR);
 FARPROC (WINAPI *resolve)(HMODULE,LPCSTR);
} OwnSourceContext;
typedef DWORD (WINAPI *OwnSourceWorker)(OwnSourceContext *);
static DWORD source_worker_result,source_load_calls,source_resolve_calls;
static DWORD source_reloc_rva[512],source_reloc_expected[512],source_reloc_count;
static DWORD source_iat_rva[256],source_symbol[256],source_module_index[256],source_symbol_count;

static HMODULE WINAPI source_system_load(LPCSTR name) {
 char system_path[MAX_PATH];UINT length;HMODULE module;
 if((BYTE *)name<image || (BYTE *)name>=image+image_size ||
    !string_at((DWORD)((BYTE *)name-image)) ||
    (strcmp(name,"kernel32.dll") && strcmp(name,"msvcrt.dll")) || dependency_count==2)return NULL;
 length=GetSystemDirectoryA(system_path,MAX_PATH);
 if(!length || length>MAX_PATH-16)return NULL;
 strcat(system_path,"\\");strcat(system_path,name);
 module=LoadLibraryA(system_path);
 if(module) { dependencies[dependency_count++]=module;source_load_calls++; }
 return module;
}
static FARPROC WINAPI source_system_resolve(HMODULE module,LPCSTR name) {
 FARPROC address;
 if(dependency_count<1 || module!=dependencies[dependency_count-1])return NULL;
 if((DWORD)name>0xffff && ((BYTE *)name<image || (BYTE *)name>=image+image_size ||
    !string_at((DWORD)((BYTE *)name-image))))return NULL;
 address=GetProcAddress(module,name);
 if(address)source_resolve_calls++;
 return address;
}
static int prepare_original_source_worker(IMAGE_NT_HEADERS32 *nt,DWORD delta) {
 IMAGE_DATA_DIRECTORY rel=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_BASERELOC];
 IMAGE_DATA_DIRECTORY imp=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_IMPORT];
 OwnSourceContext context;OwnSourceWorker worker;BYTE *code;DWORD i,j,offset=0,old,descriptors=0;
 if(sizeof(context)!=24 || !nt->OptionalHeader.AddressOfEntryPoint ||
    !at(nt->OptionalHeader.AddressOfEntryPoint,1))return 28;
 while(offset<rel.Size) {
  IMAGE_BASE_RELOCATION *block=(IMAGE_BASE_RELOCATION *)at(rel.VirtualAddress+offset,8);WORD *words;
  if(!block || block->SizeOfBlock<8 || block->SizeOfBlock>rel.Size-offset || (block->SizeOfBlock&1))return 29;
  words=(WORD *)at(rel.VirtualAddress+offset+8,block->SizeOfBlock-8);if(!words)return 29;
  for(j=0;j<(block->SizeOfBlock-8)/2;j++) {
   DWORD rva,*target;if(!words[j])continue;
   if((words[j]>>12)!=IMAGE_REL_BASED_HIGHLOW || source_reloc_count==512)return 29;
   rva=block->VirtualAddress+(words[j]&0xfff);target=(DWORD *)at(rva,4);if(!target)return 29;
   source_reloc_rva[source_reloc_count]=rva;source_reloc_expected[source_reloc_count++]=*target+delta;
  }
  offset+=block->SizeOfBlock;
 }
 /* The source stops on block VirtualAddress0 rather than the directory size. */
 if(!at(rel.VirtualAddress+rel.Size,4) || *(DWORD *)at(rel.VirtualAddress+rel.Size,4))return 29;
 for(i=0;i<imp.Size/20;i++) {
  IMAGE_IMPORT_DESCRIPTOR *d=(IMAGE_IMPORT_DESCRIPTOR *)at(imp.VirtualAddress+20*i,20);const char *name;
  if(!d)return 30;if(!d->OriginalFirstThunk)break;
  name=string_at(d->Name);if(!name || (strcmp(name,"kernel32.dll") && strcmp(name,"msvcrt.dll")) || descriptors==2)return 30;
  for(j=0;j<256;j++) {
   DWORD *lookup=(DWORD *)at(d->OriginalFirstThunk+4*j,4),*iat=(DWORD *)at(d->FirstThunk+4*j,4);
   if(!lookup || !iat)return 30;if(!*lookup)break;
   if(!(*lookup&IMAGE_ORDINAL_FLAG32) && !string_at(*lookup+2))return 30;
   if(source_symbol_count==256)return 30;
   source_iat_rva[source_symbol_count]=d->FirstThunk+4*j;
   source_symbol[source_symbol_count]=*lookup;source_module_index[source_symbol_count++]=descriptors;
  }
  if(j==256)return 30;descriptors++;
 }
 if(i==imp.Size/20 || descriptors!=2 || source_reloc_count!=116 || source_symbol_count!=43)return 31;
 code=(BYTE *)VirtualAlloc(NULL,4096,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);if(!code)return 32;
 memcpy(code,source_loader_worker_code,sizeof(source_loader_worker_code));
 if(memcmp(code,source_loader_worker_code,sizeof(source_loader_worker_code)) ||
    !VirtualProtect(code,4096,PAGE_EXECUTE_READ,&old) ||
    !VirtualProtect(image,image_size,PAGE_EXECUTE_READWRITE,&old) ||
    !FlushInstructionCache(GetCurrentProcess(),code,sizeof(source_loader_worker_code)) ||
    !FlushInstructionCache(GetCurrentProcess(),image,image_size)) { VirtualFree(code,0,MEM_RELEASE);return 32; }
 context.image=(DWORD)image;context.nt=(DWORD)(image+((IMAGE_DOS_HEADER *)image)->e_lfanew);
 context.relocs=(DWORD)(image+rel.VirtualAddress);context.imports=(DWORD)(image+imp.VirtualAddress);
 context.load=source_system_load;context.resolve=source_system_resolve;
 worker=(OwnSourceWorker)code;source_worker_result=worker(&context);VirtualFree(code,0,MEM_RELEASE);
 if(source_worker_result!=1)return 33;
 entry=(Entry)at(nt->OptionalHeader.AddressOfEntryPoint,1);attached=1;
 for(i=0;i<source_reloc_count;i++) {
  if(*(DWORD *)at(source_reloc_rva[i],4)!=source_reloc_expected[i])return 34;
  relocation_count++;
 }
 if(dependency_count!=2 || source_load_calls!=2 || source_resolve_calls!=43)return 35;
 for(i=0;i<source_symbol_count;i++) {
  DWORD value=source_symbol[i];LPCSTR name=(value&IMAGE_ORDINAL_FLAG32)?(LPCSTR)(value&0xffff):string_at(value+2);
  FARPROC expected=GetProcAddress(dependencies[source_module_index[i]],name);
  if(!expected || *(DWORD *)at(source_iat_rva[i],4)!=(DWORD)expected)return 35;
  import_count++;
 }
 return 0;
}
