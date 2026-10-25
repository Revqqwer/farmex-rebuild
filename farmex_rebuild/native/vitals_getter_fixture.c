/* Execute pinned getter/scalar bodies on owned pages only. No target arguments. */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include "guarded_scalar_templates.h"
#include "vitals_getter_templates.h"

typedef unsigned int (__cdecl *Getter)(void);
static unsigned char *data_page;
static unsigned calls,real_calls,deny_call,trace[8];

static void put(unsigned offset,unsigned value) { memcpy(data_page+offset,&value,4); }
static BOOL WINAPI owned_protect(LPVOID address,SIZE_T size,DWORD flags,PDWORD old) {
 unsigned a=(unsigned)address,b=(unsigned)data_page;
 if(calls>=8 || size!=4 || flags!=PAGE_EXECUTE_READWRITE)ExitProcess(71);
 trace[calls++]=a;
 if(calls==deny_call)return 0;
 /* Invalid synthesized addresses are recorded but never passed to Windows. */
 if(a<b || a-b>4092)return 0;
 real_calls++;
 return VirtualProtect(address,size,flags,old);
}

/* Relative CALL operands depend on the allocated clone's address. */
static unsigned char *make_helper(void) {
 unsigned char *p;unsigned delta,i;DWORD old;
 p=(unsigned char *)VirtualAlloc(NULL,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);
 if(!p)ExitProcess(15);
 memcpy(p,dword_read_code,sizeof(dword_read_code));
 delta=(unsigned)owned_protect-((unsigned)p+31);memcpy(p+27,&delta,4);
 for(i=0;i<sizeof(dword_read_code);i++)if((i<27 || i>30) && p[i]!=dword_read_code[i])ExitProcess(16);
 if(!VirtualProtect(p,4096,PAGE_EXECUTE_READ,&old) ||
    !FlushInstructionCache(GetCurrentProcess(),p,sizeof(dword_read_code)))ExitProcess(17);
 return p;
}

static unsigned char *make_getter(unsigned index,unsigned char *helper) {
 unsigned char *p;unsigned i;DWORD old;
 p=(unsigned char *)VirtualAlloc(NULL,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);
 if(!p)ExitProcess(18);
 memcpy(p,vitals_getter_code[index],30);
 { unsigned values[4]={(unsigned)data_page,(unsigned)helper-((unsigned)p+14),
                     (unsigned)(data_page+32+index*4),(unsigned)helper-((unsigned)p+27)};
   unsigned offsets[4]={5,10,17,23},j,allowed;
   for(i=0;i<4;i++)memcpy(p+offsets[i],values+i,4);
   for(i=0;i<30;i++) {
    allowed=0;for(j=0;j<4;j++)if(i>=offsets[j] && i<offsets[j]+4)allowed=1;
    if(!allowed && p[i]!=vitals_getter_code[index][i])ExitProcess(19);
   }
 }
 if(!VirtualProtect(p,4096,PAGE_EXECUTE_READ,&old) ||
    !FlushInstructionCache(GetCurrentProcess(),p,30))ExitProcess(20);
 return p;
}

static void begin(unsigned deny) {
 calls=real_calls=0;deny_call=deny;memset(trace,0,sizeof(trace));
 put(0,(unsigned)(data_page+16));put(16,(unsigned)(data_page+256));
 put(32,16);put(36,20);put(40,24);put(44,28);
 put(272,1234);put(276,4321);put(280,5678);put(284,8765);
 put(528,2234);put(532,5321);put(536,6678);put(540,9765);
}

static unsigned check(const char *name,unsigned value,unsigned expected,unsigned count,
                      unsigned real,const unsigned *addresses) {
 unsigned i;
 if(value!=expected || calls!=count || real_calls!=real)return 0;
 for(i=0;i<count;i++)if(trace[i]!=addresses[i])return 0;
 printf("{\"kind\":\"case\",\"case\":\"%s\",\"value\":%u,\"protect_attempts\":%u,\"real_owned_protect_calls\":%u,\"address_order_matches\":true,\"passed\":true}\n",
        name,value,calls,real_calls);
 return 1;
}

int main(int argc,char **argv) {
 unsigned char *helper,*code[4];Getter get[4];unsigned passed=0,i,value,b,addresses[4];
 unsigned expected[4]={1234,4321,5678,8765};
 const char *names[4]={"hp","hp_max","mp","mp_max"};
 (void)argv;if(argc!=1 || sizeof(void *)!=4)return 10;
 data_page=(unsigned char *)VirtualAlloc(NULL,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);
 if(!data_page)return 21;b=(unsigned)data_page;
 helper=make_helper();for(i=0;i<4;i++){code[i]=make_getter(i,helper);get[i]=(Getter)code[i];}
 printf("{\"kind\":\"templates\",\"source_bytes\":168,\"relocated_dword_operands\":17,\"nonrelocated_bytes_unchanged\":true,\"own_code_rx\":true}\n");
 for(i=0;i<4;i++) {
  begin(0);addresses[0]=b+16;addresses[1]=b+272+i*4;
  value=get[i]();passed+=check(names[i],value,expected[i],2,2,addresses);
 }
 begin(0);put(272,0xffffffff);addresses[0]=b+16;addresses[1]=b+272;
 value=get[0]();passed+=check("raw_high_bits",value,0xffffffff,2,2,addresses);
 begin(0);put(0,0);addresses[0]=16;
 value=get[0]();passed+=check("null_slot_still_adds_offset",value,0,1,0,addresses);
 begin(0);put(16,0);addresses[0]=b+16;addresses[1]=16;
 value=get[0]();passed+=check("zero_root_still_adds_offset",value,0,2,1,addresses);
 begin(1);addresses[0]=b+16;addresses[1]=16;
 value=get[0]();passed+=check("root_protect_failure_continues",value,0,2,0,addresses);
 begin(2);addresses[0]=b+16;addresses[1]=b+272;
 value=get[0]();passed+=check("field_protect_failure",value,0,2,1,addresses);
 begin(0);put(16,0xfffffff0);addresses[0]=b+16;
 value=get[0]();passed+=check("address_wraps_to_null",value,0,1,1,addresses);
 begin(0);put(32,0xfffffff0);put(240,999);addresses[0]=b+16;addresses[1]=b+240;
 value=get[0]();passed+=check("unsigned_offset_wraps_to_owned",value,999,2,2,addresses);
 begin(0);addresses[0]=b+16;addresses[1]=b+272;addresses[2]=b+16;addresses[3]=b+536;
 value=get[0]();if(value!=1234)return 72;put(16,b+512);
 value=get[2]();passed+=check("next_getter_rereads_root",value,6678,4,4,addresses);
 printf("{\"kind\":\"summary\",\"passed\":%u,\"external_process_access\":false,\"original_dll_loaded\":false,\"game_memory_reads\":0,\"game_memory_writes\":0,\"game_actions\":0,\"live_compatibility_verified\":false}\n",passed);
 for(i=0;i<4;i++)VirtualFree(code[i],0,MEM_RELEASE);
 VirtualFree(helper,0,MEM_RELEASE);VirtualFree(data_page,0,MEM_RELEASE);
 return passed==12?0:70;
}
