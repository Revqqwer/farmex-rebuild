/* Fixture-only relocated source shapes, own data/reader/RET4 or RET8 receivers.
 * No target PID, foreign handle, external module or game address is accepted.
 */
#include <windows.h>
#include <stdio.h>
#include <string.h>
#include "relog_selection_templates.h"

static DWORD slots[8],root_variable,guard_root[32],guard_base[32],direct_root[32],direct_object[32],vtable[32];
static DWORD item_address,flip_root,reader_calls,bad_reads;
static DWORD seen_context,seen_first,seen_second,seen_sp;
static DWORD owned_wrapper,owned_argument,before_sp,after_sp,before_bp,after_bp;
static DWORD after_eax,after_ebx,after_esi,after_edi;

static DWORD address(const void *p){return (DWORD)(ULONG_PTR)p;}
static int in_array(DWORD a,DWORD *p){return a>=address(p) && a<=address(p)+31*4 && ((a-address(p))&3)==0;}
static DWORD own_read(DWORD a){
  DWORD value;reader_calls++;
  if(a!=address(&root_variable) && !in_array(a,guard_root) && !in_array(a,guard_base) &&
     !in_array(a,direct_root) && !in_array(a,direct_object)){bad_reads++;return 0;}
  value=*(DWORD *)(ULONG_PTR)a;
  if(flip_root && a==item_address)root_variable=address(direct_root);
  return value;
}
static void put32(BYTE **p,DWORD value){memcpy(*p,&value,4);*p+=4;}
static void store(BYTE **p,BYTE modrm,DWORD *where){*(*p)++=0x89;*(*p)++=modrm;put32(p,address(where));}
static BYTE *allocate_code(void){return (BYTE *)VirtualAlloc(NULL,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);}
static int seal(BYTE *code,unsigned int size){
  DWORD old=0;
  return VirtualProtect(code,4096,PAGE_EXECUTE_READ,&old) && FlushInstructionCache(GetCurrentProcess(),code,size);
}
static BYTE *make_receiver(int argc,int clobber_edi){
  BYTE *code=allocate_code(),*p=code;if(!code)return NULL;
  store(&p,0x0d,&seen_context);store(&p,0x25,&seen_sp);
  *p++=0x8b;*p++=0x44;*p++=0x24;*p++=4;store(&p,0x05,&seen_first);
  if(argc==2){*p++=0x8b;*p++=0x54;*p++=0x24;*p++=8;store(&p,0x15,&seen_second);}
  *p++=0xb8;put32(&p,0xcafebabe);*p++=0xb9;put32(&p,0xcccccccc);
  *p++=0xba;put32(&p,0xdddddddd);*p++=0xbb;put32(&p,0xbad00bad);
  if(clobber_edi){*p++=0xbf;put32(&p,0xeeeeeeee);}
  *p++=0xbd;put32(&p,0x12345678);
  *p++=0xc2;*p++=(BYTE)(argc*4);*p++=0;
  if(!seal(code,(unsigned int)(p-code))){VirtualFree(code,0,MEM_RELEASE);return NULL;}
  return code;
}
static BYTE *make_wrapper(int kind){
  const RelogTemplate *t=&relog_templates[kind];BYTE *code=allocate_code();unsigned int i,j;DWORD value;
  if(!code)return NULL;memcpy(code,t->code,t->size);
  for(i=0;i<t->count;i++){
    const RelogFixup *f=&t->fixups[i];
    if(f->offset+4>t->size || f->kind>1 || f->slot>=8){VirtualFree(code,0,MEM_RELEASE);return NULL;}
    value=f->kind?address((const void *)own_read)-(address(code)+f->offset+4):address(&slots[f->slot]);
    memcpy(code+f->offset,&value,4);
  }
  for(i=0;i<t->size;i++){
    int relocated=0;
    for(j=0;j<t->count;j++)if(i>=t->fixups[j].offset && i<t->fixups[j].offset+4)relocated=1;
    if(!relocated && code[i]!=t->code[i]){VirtualFree(code,0,MEM_RELEASE);return NULL;}
  }
  if(!seal(code,t->size)){VirtualFree(code,0,MEM_RELEASE);return NULL;}
  return code;
}
#define INVOKE(CALL_TEXT) __asm__ __volatile__( \
  "pushl %%ebx\n pushl %%esi\n pushl %%edi\n" \
  "movl $0x44556677,%%ebx\n movl $0x55667788,%%esi\n movl $0x66778899,%%edi\n" \
  "movl %%esp,%0\n movl %%ebp,%2\n" CALL_TEXT \
  "movl %%esp,%1\n movl %%ebp,%3\n movl %%eax,%4\n" \
  "movl %%ebx,%5\n movl %%esi,%6\n movl %%edi,%7\n" \
  "popl %%edi\n popl %%esi\n popl %%ebx\n" \
  : "=m"(before_sp),"=m"(after_sp),"=m"(before_bp),"=m"(after_bp),"=m"(after_eax), \
    "=m"(after_ebx),"=m"(after_esi),"=m"(after_edi) \
  : "m"(owned_wrapper),"m"(owned_argument) : "eax","ecx","edx","memory","cc")
static void invoke(int has_argument){
  if(has_argument){INVOKE("pushl %9\n call *%8\n addl $4,%%esp\n");}
  else {INVOKE("call *%8\n");}
}
static int check_case(const char *name,int kind,DWORD argument,DWORD stride,int flip,DWORD item,
                      DWORD item_offset,DWORD virtual_offset,BYTE *wrapper,BYTE *receiver){
  DWORD expected_context,expected_first,expected_second,expected_delta,computed;int ok,registers;
  memset(guard_root,0,sizeof(guard_root));memset(guard_base,0,sizeof(guard_base));
  memset(direct_root,0,sizeof(direct_root));memset(direct_object,0,sizeof(direct_object));memset(vtable,0,sizeof(vtable));
  slots[0]=address(&root_variable);slots[1]=16;slots[2]=32;slots[3]=stride;
  slots[4]=virtual_offset;slots[5]=address(receiver);slots[6]=48;slots[7]=item_offset;
  guard_root[4]=address(guard_base);direct_root[4]=address(direct_object);
  guard_base[0]=direct_object[0]=address(vtable);vtable[virtual_offset/4]=address(receiver);
  flip_root=(DWORD)flip;reader_calls=bad_reads=0;seen_context=seen_first=seen_second=seen_sp=0;
  item_address=0;
  if(kind==0 || kind==2){
    computed=address(guard_base)+(kind==0?32+argument*stride:48);
    if(!in_array(computed,guard_base))return 0;
    item_address=computed;*(DWORD *)(ULONG_PTR)computed=item;root_variable=address(guard_root);
    expected_context=flip?address(direct_object):address(guard_base);
  }else{root_variable=address(direct_root);expected_context=address(direct_object);}
  direct_object[item_offset/4]=item;
  expected_first=kind==1?argument:item;expected_second=kind==1?0:(kind==0?0x10000000:1);
  expected_delta=kind==0?36:(kind==1?24:(kind==2?32:28));
  owned_wrapper=address(wrapper);owned_argument=argument;invoke(kind==0 || kind==1);
  registers=after_ebx==0x44556677 && after_esi==0x55667788 && after_edi==0x66778899;
  ok=seen_context==expected_context && seen_first==expected_first && seen_second==expected_second &&
     before_sp==after_sp && before_bp==after_bp && after_eax==0xcafebabe && registers &&
     before_sp-seen_sp==expected_delta && bad_reads==0 && reader_calls==(DWORD)((kind==0 || kind==2)?3:0);
  printf("{\"case\":\"%s\",\"kind\":%d,\"ok\":%d,\"argument\":%lu,\"stride\":%lu,"
         "\"fresh_root\":%d,\"context_matches\":%d,\"first_arg_matches\":%d,\"second_arg_matches\":%d,"
         "\"seen_first\":%lu,\"seen_second\":%lu,\"stack_balanced\":%d,\"frame_preserved\":%d,"
         "\"registers_restored\":%d,\"receiver_stack_delta\":%lu,\"return_eax\":%lu,"
         "\"reader_calls\":%lu,\"bad_reads\":%lu,\"owned_RET_bytes\":%d}\n",
         name,kind,ok,argument,stride,flip,seen_context==expected_context,seen_first==expected_first,
         seen_second==expected_second,seen_first,seen_second,before_sp==after_sp,before_bp==after_bp,
         registers,before_sp-seen_sp,after_eax,reader_calls,bad_reads,kind==1?4:8);
  return ok;
}
int main(void){
  BYTE *wrappers[4]={0},*receivers[4]={0};int i,ok=1;
  if(sizeof(void *)!=4)return 2;
  for(i=0;i<4;i++){
    receivers[i]=make_receiver(i==1?1:2,i==3);wrappers[i]=make_wrapper(i);
    if(!receivers[i] || !wrappers[i]){ok=0;break;}
  }
  if(ok){
    ok &= check_case("first_index0_shared_root",0,0,4,0,0x1111,32,20,wrappers[0],receivers[0]);
    ok &= check_case("first_index3_fresh_root",0,3,4,1,0x2222,32,20,wrappers[0],receivers[0]);
    ok &= check_case("first_wrapped_index",0,0xffffffff,4,1,0x3333,32,20,wrappers[0],receivers[0]);
    ok &= check_case("first_changed_stride",0,2,8,1,0x4444,32,24,wrappers[0],receivers[0]);
    ok &= check_case("second_index0",1,0,4,0,0,32,20,wrappers[1],receivers[1]);
    ok &= check_case("second_raw_FFFFFFFF",1,0xffffffff,4,0,0,32,20,wrappers[1],receivers[1]);
    ok &= check_case("confirm_shared_root",2,0,4,0,0x5555,32,20,wrappers[2],receivers[2]);
    ok &= check_case("confirm_fresh_root",2,0,4,1,0x6666,32,24,wrappers[2],receivers[2]);
    ok &= check_case("advance_item_A",3,0,4,0,0x7777,32,20,wrappers[3],receivers[3]);
    ok &= check_case("advance_changed_offsets",3,0,4,0,0x8888,36,24,wrappers[3],receivers[3]);
  }
  for(i=0;i<4;i++){if(wrappers[i])VirtualFree(wrappers[i],0,MEM_RELEASE);if(receivers[i])VirtualFree(receivers[i],0,MEM_RELEASE);}
  return ok?0:3;
}
