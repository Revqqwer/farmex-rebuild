/* Owned x86 sender-shape fixture. No PID, external handle, DLL or game address.
 * Exact26byte source template with only OUR slot/data/receiver addresses patched.
 * It tests the declared RET8 receiver contract, not the actual game's ABI.
 */
#include <windows.h>
#include <stdio.h>
#include <string.h>

static const BYTE source_template[26]={
  0x60,0x8b,0x0d,0,0,0,0,0x68,0,0,0,0,0x68,0,0,0,0,
  0xbf,0,0,0,0,0xff,0xd7,0x61,0xc3};
static DWORD own_context,stub_address;
static DWORD seen_context,seen_pointer,seen_length,seen_sp;
static DWORD before_sp,after_sp,before_bp,after_bp,before_flags,after_flags;
static DWORD after_eax,after_ecx,after_edx,after_ebx,after_esi,after_edi;
static BYTE own_payload[64];

static void put32(BYTE **p,DWORD value){memcpy(*p,&value,4);*p+=4;}
static void store(BYTE **p,BYTE modrm,DWORD *destination){
  *(*p)++=0x89;*(*p)++=modrm;put32(p,(DWORD)(ULONG_PTR)destination);
}
static BYTE *allocate_code(void){return (BYTE *)VirtualAlloc(NULL,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);}
static int protect_code(BYTE *code,DWORD protection){
  DWORD old=0;return VirtualProtect(code,4096,protection,&old)!=0;
}
static int seal(BYTE *code,SIZE_T size){
  return protect_code(code,PAGE_EXECUTE_READ) && FlushInstructionCache(GetCurrentProcess(),code,size);
}
static BYTE *receiver(int carry){
  BYTE *code=allocate_code(),*p=code;if(!code)return NULL;
  store(&p,0x0d,&seen_context);store(&p,0x25,&seen_sp);
  *p++=0x8b;*p++=0x54;*p++=0x24;*p++=0x04; /* EDX=[ESP+4], our payload */
  store(&p,0x15,&seen_pointer);
  *p++=0x8b;*p++=0x44;*p++=0x24;*p++=0x08; /* EAX=[ESP+8], our length */
  store(&p,0x05,&seen_length);
  *p++=0xb8;put32(&p,0xaaaaaaaa);*p++=0xb9;put32(&p,0xbbbbbbbb);
  *p++=0xba;put32(&p,0xcccccccc);*p++=0xbb;put32(&p,0xdddddddd);
  *p++=0xbe;put32(&p,0xeeeeeeee);*p++=0xbf;put32(&p,0xffffffff);
  *p++=0xbd;put32(&p,0x12345678); /* Even EBP is changed before source POPAD. */
  *p++=carry?0xf9:0xf8; /* STC/CLC exposes the missing PUSHFD/POPFD. */
  *p++=0xc2;*p++=8;*p++=0; /* Own callee pops the two pushed arguments. */
  if(!seal(code,(SIZE_T)(p-code))){VirtualFree(code,0,MEM_RELEASE);return NULL;}
  return code;
}
static int patch_owned_stub(BYTE *stub,DWORD length,BYTE *target){
  DWORD value;
  if(!protect_code(stub,PAGE_READWRITE))return 0;
  memcpy(stub,source_template,26);
  value=(DWORD)(ULONG_PTR)&own_context;memcpy(stub+3,&value,4);
  memcpy(stub+8,&length,4);
  value=(DWORD)(ULONG_PTR)own_payload;memcpy(stub+13,&value,4);
  value=(DWORD)(ULONG_PTR)target;memcpy(stub+18,&value,4);
  return seal(stub,26);
}
static void invoke_owned_stub(void){
  __asm__ __volatile__(
    "pushl %%ebx\n pushl %%esi\n pushl %%edi\n"
    "movl $0x11223344,%%eax\n movl $0x22334455,%%ecx\n movl $0x33445566,%%edx\n"
    "movl $0x44556677,%%ebx\n movl $0x55667788,%%esi\n movl $0x66778899,%%edi\n"
    "movl %%esp,%0\n movl %%ebp,%2\n clc\n pushfl\n popl %4\n"
    "call *%12\n pushfl\n popl %5\n"
    "movl %%esp,%1\n movl %%ebp,%3\n"
    "movl %%eax,%6\n movl %%ecx,%7\n movl %%edx,%8\n movl %%ebx,%9\n"
    "movl %%esi,%10\n movl %%edi,%11\n"
    "popl %%edi\n popl %%esi\n popl %%ebx\n"
    : "=m"(before_sp),"=m"(after_sp),"=m"(before_bp),"=m"(after_bp),
      "=m"(before_flags),"=m"(after_flags),"=m"(after_eax),"=m"(after_ecx),
      "=m"(after_edx),"=m"(after_ebx),"=m"(after_esi),"=m"(after_edi)
    : "m"(stub_address) : "eax","ecx","edx","memory","cc");
}
static int check_case(const char *name,BYTE *stub,BYTE *target,DWORD context,DWORD length,int carry){
  int ok;own_context=context;
  seen_context=seen_pointer=seen_length=seen_sp=0;
  if(!patch_owned_stub(stub,length,target))return 0;
  stub_address=(DWORD)(ULONG_PTR)stub;invoke_owned_stub();
  ok=seen_context==context && seen_pointer==(DWORD)(ULONG_PTR)own_payload && seen_length==length;
  ok=ok && before_sp==after_sp && before_bp==after_bp && before_sp-seen_sp==48;
  ok=ok && after_eax==0x11223344 && after_ecx==0x22334455 && after_edx==0x33445566;
  ok=ok && after_ebx==0x44556677 && after_esi==0x55667788 && after_edi==0x66778899;
  ok=ok && (before_flags&1)==0 && (after_flags&1)==(DWORD)carry;
  printf("{\"case\":\"%s\",\"ok\":%d,\"length\":%lu,\"seen_context\":%lu,"
    "\"seen_length\":%lu,\"pointer_matches\":%d,\"stack_balanced\":%d,"
    "\"frame_preserved\":%d,\"receiver_stack_delta\":%lu,\"registers_restored\":%d,"
    "\"carry_before\":%lu,\"carry_after\":%lu,\"owned_RET_bytes\":8}\n",
    name,ok,length,seen_context,seen_length,seen_pointer==(DWORD)(ULONG_PTR)own_payload,
    before_sp==after_sp,before_bp==after_bp,before_sp-seen_sp,
    after_eax==0x11223344 && after_ecx==0x22334455 && after_edx==0x33445566 &&
    after_ebx==0x44556677 && after_esi==0x55667788 && after_edi==0x66778899,
    before_flags&1,after_flags&1);
  return ok;
}
int main(void){
  BYTE *stub,*set_carry,*clear_carry;int ok=1;
  if(sizeof(void *)!=4)return 2;
  stub=allocate_code();set_carry=receiver(1);clear_carry=receiver(0);
  if(!stub || !set_carry || !clear_carry){
    if(stub)VirtualFree(stub,0,MEM_RELEASE);
    if(set_carry)VirtualFree(set_carry,0,MEM_RELEASE);
    if(clear_carry)VirtualFree(clear_carry,0,MEM_RELEASE);return 3;
  }
  memset(own_payload,0x5a,sizeof(own_payload));own_payload[0]=1;
  ok &= check_case("one_byte_owned_receiver",stub,set_carry,0x12345678,1,1);
  own_payload[0]=0;
  ok &= check_case("zero_context_and_zero_byte",stub,set_carry,0,1,1);
  ok &= check_case("thirty_eight_owned_bytes",stub,set_carry,0x87654321,38,1);
  ok &= check_case("empty_owned_payload",stub,set_carry,0x10203040,0,1);
  ok &= check_case("changed_slot_value",stub,set_carry,0xfedcba98,2,1);
  ok &= check_case("changed_receiver_clears_carry",stub,clear_carry,0x76543210,7,0);
  VirtualFree(clear_carry,0,MEM_RELEASE);VirtualFree(set_carry,0,MEM_RELEASE);VirtualFree(stub,0,MEM_RELEASE);
  return ok?0:4;
}
