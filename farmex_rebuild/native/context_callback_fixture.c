/* Own x86 callback-context fixture. No game address, process handle or loader.
 * Reconstructs the 0046eca8 register/stack shape with our own data and receiver.
 */
#include <windows.h>
#include <stdio.h>
#include <string.h>

static DWORD root_slot_address, field_offset, previous_callback;
static DWORD own_root_value, wrapper_address;
static DWORD seen_context, seen_ebx, seen_sp;
static DWORD before_sp,after_sp,before_bp,after_bp,before_flags,after_flags;
static DWORD after_eax,after_ecx,after_edx,after_ebx;
static BYTE first_arena[1024],second_arena[1024];

static void put32(BYTE **p,DWORD value) { memcpy(*p,&value,4);*p+=4; }
static void store(BYTE **p,BYTE modrm,DWORD *destination) {
    *(*p)++=0x89;*(*p)++=modrm;put32(p,(DWORD)(ULONG_PTR)destination);
}
static BYTE *make_receiver(void) {
    BYTE *code=(BYTE *)VirtualAlloc(NULL,4096,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);
    BYTE *p=code;
    if (!code) return NULL;
    store(&p,0x0d,&seen_context);store(&p,0x1d,&seen_ebx);store(&p,0x25,&seen_sp);
    *p++=0xb8;put32(&p,0xaaaaaaaa);*p++=0xb9;put32(&p,0xbbbbbbbb);
    *p++=0xba;put32(&p,0xcccccccc);*p++=0xbb;put32(&p,0xdddddddd);
    *p++=0xf9; /* STC, so preservation cannot be inferred accidentally. */
    *p++=0xc3; /* Own receiver contract RET0; unknown vendor ABI is not proven. */
    FlushInstructionCache(GetCurrentProcess(),code,(SIZE_T)(p-code));
    return code;
}
static BYTE *make_wrapper(void) {
    BYTE *code=(BYTE *)VirtualAlloc(NULL,4096,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);
    BYTE *p=code;
    if (!code) return NULL;
    *p++=0x55;*p++=0x8b;*p++=0xec;*p++=0x53; /* PUSH EBP;MOV EBP,ESP;PUSH EBX */
    *p++=0xa1;put32(&p,(DWORD)(ULONG_PTR)&root_slot_address);
    *p++=0x8b;*p++=0x08;                     /* ECX=[root-slot address] */
    *p++=0xa1;put32(&p,(DWORD)(ULONG_PTR)&field_offset);
    *p++=0x8b;*p++=0x0c;*p++=0x08;         /* ECX=[root value+offset] */
    *p++=0xa1;put32(&p,(DWORD)(ULONG_PTR)&previous_callback);
    *p++=0xff;*p++=0xd0;                    /* CALL EAX, no pushed arguments */
    *p++=0x5b;*p++=0x5d;*p++=0xc3;
    FlushInstructionCache(GetCurrentProcess(),code,(SIZE_T)(p-code));
    return code;
}
static void invoke_wrapper(void) {
    __asm__ __volatile__(
      "pushl %%ebx\n movl $0x11111111,%%ebx\n"
      "movl %%esp,%0\n movl %%ebp,%2\n clc\n pushfl\n popl %4\n"
      "call *%10\n pushfl\n popl %5\n"
      "movl %%esp,%1\n movl %%ebp,%3\n"
      "movl %%eax,%6\n movl %%ecx,%7\n movl %%edx,%8\n movl %%ebx,%9\n"
      "popl %%ebx\n"
      : "=m"(before_sp),"=m"(after_sp),"=m"(before_bp),"=m"(after_bp),
        "=m"(before_flags),"=m"(after_flags),"=m"(after_eax),"=m"(after_ecx),
        "=m"(after_edx),"=m"(after_ebx)
      : "m"(wrapper_address)
      : "eax","ecx","edx","memory","cc");
}
static int run_case(const char *name,BYTE *arena,DWORD offset,DWORD value) {
    int ok;
    memset(arena,0x5a,1024);memcpy(arena+offset,&value,4);
    own_root_value=(DWORD)(ULONG_PTR)arena;
    root_slot_address=(DWORD)(ULONG_PTR)&own_root_value;field_offset=offset;
    seen_context=seen_ebx=seen_sp=0;
    invoke_wrapper();
    ok=seen_context==value && seen_ebx==0x11111111 && after_ebx==0x11111111;
    ok=ok && before_sp==after_sp && before_bp==after_bp && before_sp-seen_sp==16;
    ok=ok && after_eax==0xaaaaaaaa && after_ecx==0xbbbbbbbb && after_edx==0xcccccccc;
    ok=ok && (before_flags&1)==0 && (after_flags&1)==1;
    printf("{\"case\":\"%s\",\"ok\":%d,\"field_offset\":%lu,\"seen_context\":%lu,"
           "\"seen_ebx\":%lu,\"after_ebx\":%lu,\"stack_before\":%lu,\"stack_after\":%lu,"
           "\"receiver_stack\":%lu,\"frame_before\":%lu,\"frame_after\":%lu,"
           "\"flags_before\":%lu,\"flags_after\":%lu,\"after_eax\":%lu,"
           "\"after_ecx\":%lu,\"after_edx\":%lu}\n",
           name,ok,offset,seen_context,seen_ebx,after_ebx,before_sp,after_sp,seen_sp,
           before_bp,after_bp,before_flags,after_flags,after_eax,after_ecx,after_edx);
    return ok;
}
int main(void) {
    BYTE *receiver,*wrapper;int ok=1;
    if(sizeof(void *)!=4) return 2;
    receiver=make_receiver();wrapper=make_wrapper();
    if(!receiver || !wrapper) {
        if(receiver) VirtualFree(receiver,0,MEM_RELEASE);
        if(wrapper) VirtualFree(wrapper,0,MEM_RELEASE);
        return 3;
    }
    previous_callback=(DWORD)(ULONG_PTR)receiver;wrapper_address=(DWORD)(ULONG_PTR)wrapper;
    ok &= run_case("field_zero",first_arena,0,0x12345678);
    ok &= run_case("field_eight",first_arena,8,0x87654321);
    ok &= run_case("unaligned_field",first_arena,3,0xfedcba98);
    ok &= run_case("changed_root",second_arena,8,0x10203040);
    ok &= run_case("source_field_3b0",second_arena,0x3b0,0x76543210);
    VirtualFree(wrapper,0,MEM_RELEASE);VirtualFree(receiver,0,MEM_RELEASE);
    return ok?0:4;
}
