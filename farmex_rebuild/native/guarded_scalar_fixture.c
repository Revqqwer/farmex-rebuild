/* Original pinned scalar instructions, owned pages/API shims only; no arguments. */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include "guarded_scalar_templates.h"

static unsigned char *owned_data;
static unsigned protect_calls,real_protect_calls,copy_calls,forced_failure,upper_success;
typedef unsigned int (__cdecl *Reader)(unsigned int);
typedef unsigned int (__cdecl *Writer)(unsigned int,unsigned int);

static BOOL WINAPI owned_protect(LPVOID address,SIZE_T size,DWORD flags,PDWORD old) {
 unsigned long a=(unsigned long)address,b=(unsigned long)owned_data;
 protect_calls++;
 if(forced_failure)return 0;
 if(a<b || a+size>b+4096 || size>4 || flags!=PAGE_EXECUTE_READWRITE)ExitProcess(75);
 real_protect_calls++;
 if(!VirtualProtect(address,size,flags,old))return 0;
 return upper_success?(BOOL)0x12345601:1;
}

static void *__cdecl owned_copy(void *dest,const void *source,size_t length) {
 unsigned long a=(unsigned long)dest,b=(unsigned long)owned_data;
 if(a<b || a+length>b+4096 || length!=1)ExitProcess(76);
 copy_calls++;return memcpy(dest,source,length);
}

static unsigned char *clone_template(const struct ScalarTemplate *t) {
 unsigned char *p;unsigned i,j,target,delta,allowed;DWORD old;
 p=(unsigned char *)VirtualAlloc(NULL,4096,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
 if(!p)ExitProcess(11);memcpy(p,t->code,t->size);
 for(i=0;i<t->count;i++) {
  unsigned off=t->relocs[i].offset;
  if(off+5>t->size || p[off]!=0xe8 || t->relocs[i].kind>1)ExitProcess(12);
  target=(unsigned)(t->relocs[i].kind?(void *)owned_copy:(void *)owned_protect);
  delta=target-((unsigned)p+off+5);memcpy(p+off+1,&delta,4);
 }
 for(j=0;j<t->size;j++) {
  allowed=0;
  for(i=0;i<t->count;i++)if(j>t->relocs[i].offset && j<t->relocs[i].offset+5)allowed=1;
  if(!allowed && p[j]!=t->code[j])ExitProcess(13);
 }
 if(!VirtualProtect(p,4096,PAGE_EXECUTE_READ,&old))ExitProcess(14);
 if(!FlushInstructionCache(GetCurrentProcess(),p,t->size))ExitProcess(15);
 return p;
}

static void begin(unsigned failure,unsigned upper) {
 protect_calls=real_protect_calls=copy_calls=0;forced_failure=failure;upper_success=upper;
}

static unsigned check(const char *name,unsigned value,unsigned expected,unsigned protects,unsigned real,unsigned copies,unsigned first,int pointer) {
 if(value!=expected || protect_calls!=protects || real_protect_calls!=real || copy_calls!=copies)return 0;
 if(owned_data[0]!=first || owned_data[1]!=0x22 || owned_data[2]!=0x33 || owned_data[3]!=0x44)return 0;
 printf("{\"kind\":\"case\",\"case\":\"%s\",\"result_kind\":\"%s\",\"result\":%u,\"protect_calls\":%u,\"real_protect_calls\":%u,\"copy_calls\":%u,\"first_byte\":%u,\"neighbors_preserved\":true,\"passed\":true}\n",
  name,pointer?"owned_pointer":"dword",pointer?0:value,protect_calls,real_protect_calls,copy_calls,first);
 return 1;
}

int main(int argc,char **argv) {
 unsigned char *dc,*bc,*wc;Reader dword_read,byte_read;Writer byte_write;unsigned value,passed=0;
 (void)argv;if(argc!=1 || sizeof(void *)!=4)return 10;
 owned_data=(unsigned char *)VirtualAlloc(NULL,4096,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
 if(!owned_data)return 16;
 owned_data[0]=0x11;owned_data[1]=0x22;owned_data[2]=0x33;owned_data[3]=0x44;
 dc=clone_template(&dword_read_template);bc=clone_template(&byte_read_template);wc=clone_template(&byte_write_template);
 dword_read=(Reader)dc;byte_read=(Reader)bc;byte_write=(Writer)wc;
 printf("{\"kind\":\"templates\",\"count\":3,\"source_bytes\":140,\"relocations\":4,\"nonreloc_bytes_unchanged\":true,\"own_code_rx\":true}\n");
 begin(0,0);value=dword_read(0);passed+=check("dword_null",value,0,0,0,0,0x11,0);
 begin(0,0);value=byte_read(0);passed+=check("byte_null",value,0,0,0,0,0x11,0);
 begin(0,0);value=dword_read((unsigned)owned_data);passed+=check("dword_actual",value,0x44332211,1,1,0,0x11,0);
 begin(0,0);value=byte_read((unsigned)owned_data);passed+=check("byte_actual",value,0x11,1,1,0,0x11,0);
 begin(0,1);value=byte_read((unsigned)owned_data);passed+=check("byte_upper_success",value,0x12345611,1,1,0,0x11,0);
 begin(1,0);value=dword_read(1);passed+=check("dword_forced_failure",value,0,1,0,0,0x11,0);
 begin(1,0);value=byte_read(1);passed+=check("byte_forced_failure",value,0,1,0,0,0x11,0);
 begin(1,0);value=byte_write((unsigned)owned_data,0xfe);passed+=check("writer_forced_failure",value,0,1,0,0,0x11,0);
 begin(1,0);value=byte_write(0,0xfe);passed+=check("writer_null_forced_failure",value,0,1,0,0,0x11,0);
 begin(0,0);value=byte_write((unsigned)owned_data,0xabcd12fe);passed+=check("writer_actual",value,(unsigned)owned_data,1,1,1,0xfe,1);
 begin(0,0);value=byte_read((unsigned)owned_data);passed+=check("byte_after_write",value,0xfe,1,1,0,0xfe,0);
 begin(0,0);value=dword_read((unsigned)owned_data);passed+=check("dword_after_write",value,0x443322fe,1,1,0,0xfe,0);
 printf("{\"kind\":\"summary\",\"passed\":%u,\"external_process_access\":false,\"original_dll_loaded\":false}\n",passed);
 VirtualFree(dc,0,MEM_RELEASE);VirtualFree(bc,0,MEM_RELEASE);VirtualFree(wc,0,MEM_RELEASE);VirtualFree(owned_data,0,MEM_RELEASE);
 return passed==12?0:70;
}
