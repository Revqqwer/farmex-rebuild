/* Only compiled into our hash-pinned sibling child; no arbitrary target API. */
#include "source_remote_context.h"
#include "source_loader_worker_template.h"
static int source_preflight_ready;
static DWORD source_fix_rva[512],source_fix_value[512],source_fix_count;
static DWORD source_iat_rva[256],source_lookup[256],source_dll[256],source_import_count;

static int source_private_page(LPVOID address,SIZE_T size,DWORD protection) {
 MEMORY_BASIC_INFORMATION p;
 return VirtualQuery(address,&p,sizeof(p)) && p.AllocationBase==address && p.BaseAddress==address &&
        p.RegionSize>=size && p.Type==MEM_PRIVATE && p.State==MEM_COMMIT && p.Protect==protection;
}
__declspec(dllexport) DWORD WINAPI FarmexSourcePreflight(LPVOID argument) {
 SourceRemoteContext *c=(SourceRemoteContext *)argument;IMAGE_DOS_HEADER *dos=(IMAGE_DOS_HEADER *)own_bridge_image;
 IMAGE_NT_HEADERS32 *nt=(IMAGE_NT_HEADERS32 *)(own_bridge_image+dos->e_lfanew);
 IMAGE_SECTION_HEADER *sections=IMAGE_FIRST_SECTION(nt);IMAGE_DATA_DIRECTORY dir;BYTE *expected;
 DWORD i,j,offset=0,delta,descriptors=0;HMODULE kernel=GetModuleHandleA("kernel32.dll");
 if(bootstrap_ready || source_preflight_ready || sizeof(*c)!=24 || argument!=(LPVOID)0x22000000 ||
    !source_private_page(argument,24,PAGE_READWRITE))return 60;
 if(c->image!=0x20000000 || c->nt!=c->image+dos->e_lfanew ||
    c->relocs!=c->image+nt->OptionalHeader.DataDirectory[5].VirtualAddress ||
    c->imports!=c->image+nt->OptionalHeader.DataDirectory[1].VirtualAddress)return 61;
 if(c->load!=(DWORD)GetProcAddress(kernel,"LoadLibraryA") || c->resolve!=(DWORD)GetProcAddress(kernel,"GetProcAddress"))return 62;
 if(!source_private_page((LPVOID)c->image,0x5000,PAGE_EXECUTE_READWRITE) ||
    !source_private_page((LPVOID)0x21000000,431,PAGE_EXECUTE_READ))return 63;
 if(memcmp((LPVOID)0x21000000,source_loader_worker_code,sizeof(source_loader_worker_code)))return 64;
 expected=(BYTE *)VirtualAlloc(NULL,0x5000,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);if(!expected)return 65;
 memcpy(expected,own_bridge_image,0x200);
 for(i=0;i<3;i++)memcpy(expected+sections[i].VirtualAddress,own_bridge_image+sections[i].PointerToRawData,sections[i].SizeOfRawData);
 j=memcmp(expected,(LPVOID)c->image,0x5000);VirtualFree(expected,0,MEM_RELEASE);if(j)return 66;
 image=(BYTE *)c->image;image_size=0x5000;delta=c->image-nt->OptionalHeader.ImageBase;
 dir=nt->OptionalHeader.DataDirectory[5];
 while(offset<dir.Size) {
  IMAGE_BASE_RELOCATION *r=(IMAGE_BASE_RELOCATION *)at(dir.VirtualAddress+offset,8);WORD *words;
  if(!r || r->SizeOfBlock<8 || r->SizeOfBlock>dir.Size-offset || (r->SizeOfBlock&1))return 67;
  words=(WORD *)at(dir.VirtualAddress+offset+8,r->SizeOfBlock-8);if(!words)return 67;
  for(j=0;j<(r->SizeOfBlock-8)/2;j++) {
   DWORD target,*value;if(!words[j])continue;
   if((words[j]>>12)!=IMAGE_REL_BASED_HIGHLOW || source_fix_count==512)return 67;
   target=r->VirtualAddress+(words[j]&0xfff);value=(DWORD *)at(target,4);if(!value)return 67;
   source_fix_rva[source_fix_count]=target;source_fix_value[source_fix_count++]=*value+delta;
  }
  offset+=r->SizeOfBlock;
 }
 if(!at(dir.VirtualAddress+dir.Size,4) || *(DWORD *)at(dir.VirtualAddress+dir.Size,4))return 67;
 dir=nt->OptionalHeader.DataDirectory[1];
 for(i=0;i<dir.Size/20;i++) {
  IMAGE_IMPORT_DESCRIPTOR *d=(IMAGE_IMPORT_DESCRIPTOR *)at(dir.VirtualAddress+i*20,20);
  const char *name;char actual[MAX_PATH],system[MAX_PATH];UINT length;HMODULE module;
  if(!d)return 68;if(!d->OriginalFirstThunk)break;
  name=string_at(d->Name);if(!name || (strcmp(name,"kernel32.dll") && strcmp(name,"msvcrt.dll")) || descriptors==2)return 68;
  module=GetModuleHandleA(name);length=GetSystemDirectoryA(system,MAX_PATH);
  if(!module || !length || length>MAX_PATH-16 || !GetModuleFileNameA(module,actual,MAX_PATH))return 68;
  strcat(system,"\\");strcat(system,name);if(_stricmp(actual,system))return 68;
  for(j=0;j<256;j++) {
   DWORD *lookup=(DWORD *)at(d->OriginalFirstThunk+4*j,4),*iat=(DWORD *)at(d->FirstThunk+4*j,4);
   if(!lookup || !iat)return 68;if(!*lookup)break;
   if(!(*lookup&IMAGE_ORDINAL_FLAG32) && !string_at(*lookup+2))return 68;
   if(source_import_count==256)return 68;
   source_iat_rva[source_import_count]=d->FirstThunk+4*j;
   source_lookup[source_import_count]=*lookup;source_dll[source_import_count++]=descriptors;
  }
  if(j==256)return 68;descriptors++;
 }
 if(i==dir.Size/20 || descriptors!=2 || source_fix_count!=116 || source_import_count!=43)return 69;
 source_preflight_ready=1;return 0;
}
__declspec(dllexport) DWORD WINAPI FarmexSourcePublish(LPVOID argument) {
 IMAGE_DOS_HEADER *dos=(IMAGE_DOS_HEADER *)own_bridge_image;
 IMAGE_NT_HEADERS32 *nt=(IMAGE_NT_HEADERS32 *)(own_bridge_image+dos->e_lfanew);
 IMAGE_SECTION_HEADER *sections=IMAGE_FIRST_SECTION(nt);FarmexFixtureProc fixture;FarmexObserveProc production;
 FarmexPublishFixtureProc publish;FarmexVitals snapshot;char nonce[33],name[128];DWORD i,value,old,span,protection,result;
 if(bootstrap_ready || !source_preflight_ready || argument!=(LPVOID)0x20000000 || image!=argument || memcmp(image,own_bridge_image,0x200))return 70;
 entry=(Entry)at(nt->OptionalHeader.AddressOfEntryPoint,1);if(!entry)return 71;
 attached=1; /* Source worker already called attach; never call it twice. */
 dependencies[0]=GetModuleHandleA("kernel32.dll");dependencies[1]=GetModuleHandleA("msvcrt.dll");dependency_count=2;
 for(i=0;i<source_fix_count;i++) {
  if(*(DWORD *)at(source_fix_rva[i],4)!=source_fix_value[i])return 72;relocation_count++;
 }
 for(i=0;i<source_import_count;i++) {
  DWORD v=source_lookup[i];LPCSTR n=(v&IMAGE_ORDINAL_FLAG32)?(LPCSTR)(v&0xffff):string_at(v+2);
  FARPROC expected=GetProcAddress(dependencies[source_dll[i]],n);
  if(!expected || *(DWORD *)at(source_iat_rva[i],4)!=(DWORD)expected)return 73;import_count++;
 }
 if(!VirtualProtect(image,image_size,PAGE_NOACCESS,&old) || !VirtualProtect(image,0x1000,PAGE_READONLY,&old))return 74;
 for(i=0;i<3;i++) {
  span=sections[i].Misc.VirtualSize>sections[i].SizeOfRawData?sections[i].Misc.VirtualSize:sections[i].SizeOfRawData;
  protection=(sections[i].Characteristics&IMAGE_SCN_MEM_EXECUTE)?PAGE_EXECUTE_READ:
             ((sections[i].Characteristics&IMAGE_SCN_MEM_WRITE)?PAGE_READWRITE:PAGE_READONLY);
  if(!VirtualProtect(image+sections[i].VirtualAddress,span,protection,&old))return 74;
 }
 if(!FlushInstructionCache(GetCurrentProcess(),image,image_size))return 74;
 if(GetEnvironmentVariableA("FARMEX_OWN_BOOTSTRAP_NONCE",nonce,sizeof(nonce))!=32)return 75;
 for(i=0;i<32;i++)if(!strchr("0123456789abcdef",nonce[i]))return 75;
 fixture=(FarmexFixtureProc)symbol("FarmexObserveFixture");production=(FarmexObserveProc)symbol("FarmexObserve");
 publish=(FarmexPublishFixtureProc)symbol("FarmexPublishVitalsFixture");if(!fixture || !production || !publish)return 76;
 root=(DWORD)arena;value=250;memcpy(arena+0x6d8,&value,4);value=500;memcpy(arena+0x6d4,&value,4);
 value=100;memcpy(arena+0xbf0,&value,4);value=300;memcpy(arena+0xbec,&value,4);
 result=fixture((DWORD)&root,1,&snapshot,sizeof(snapshot));
 if(result || snapshot.bytes_read!=24 || snapshot.hp!=250 || snapshot.mp!=100)return 77;
 result=production(1,&snapshot,sizeof(snapshot));if(result!=FARMEX_WRONG_PROCESS || snapshot.bytes_read)return 78;
 sprintf(name,"Local\\FarmexVitals.%lu.%s",GetCurrentProcessId(),nonce);
 if(publish((DWORD)&root,1,name))return 79;
 InterlockedExchange(&bootstrap_ready,1);return 0;
}
