/* Own32-bit ABI-shape fixture. No process selection, injection or game IO.
 * The allocated callback only records register/stack values into this host.
 * It deliberately clobbers registers/CF and returns with RET8.
 */
#include <windows.h>
#include <stdio.h>
#include <string.h>

static DWORD seen_ecx, seen_first, seen_second, seen_sp;
static DWORD target, context, first_arg, second_arg, preserve;
static DWORD before_sp, after_sp, before_flags, after_flags;
static DWORD after_eax, after_ecx, after_edx, after_ebx, after_esi, after_edi;

static void dword(BYTE **p, DWORD value) { memcpy(*p,&value,4); *p += 4; }
static void store(BYTE **p, BYTE modrm, DWORD *destination) {
    *(*p)++=0x89; *(*p)++=modrm; dword(p,(DWORD)(ULONG_PTR)destination);
}
static void mov_imm(BYTE **p, BYTE opcode, DWORD value) { *(*p)++=opcode; dword(p,value); }

static BYTE *make_own_callback(void) {
    BYTE *code=(BYTE *)VirtualAlloc(NULL,4096,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE);
    BYTE *p=code;
    if (!code) return NULL;
    store(&p,0x0d,&seen_ecx);             /* MOV [ownDWORD],ECX */
    *p++=0x8b;*p++=0x44;*p++=0x24;*p++=0x04;
    store(&p,0x05,&seen_first);           /* [ESP+4] first argument */
    *p++=0x8b;*p++=0x44;*p++=0x24;*p++=0x08;
    store(&p,0x05,&seen_second);
    store(&p,0x25,&seen_sp);             /* MOV [ownDWORD],ESP */
    mov_imm(&p,0xb8,0xaaaaaaaa);mov_imm(&p,0xb9,0xbbbbbbbb);
    mov_imm(&p,0xba,0xcccccccc);mov_imm(&p,0xbb,0xdddddddd);
    mov_imm(&p,0xbe,0xeeeeeeee);mov_imm(&p,0xbf,0xffffffff);
    *p++=0xf9;                           /* STC */
    *p++=0xc2;*p++=0x08;*p++=0x00;      /* RET8 */
    FlushInstructionCache(GetCurrentProcess(),code,(SIZE_T)(p-code));
    return code;
}

static void invoke_own_callback(void) {
    __asm__ __volatile__(
      "pushl %%ebx\n pushl %%esi\n pushl %%edi\n"
      "movl $0x66666666,%%eax\n movl $0x22222222,%%ecx\n"
      "movl $0x55555555,%%edx\n movl $0x11111111,%%ebx\n"
      "movl $0x33333333,%%esi\n movl $0x44444444,%%edi\n"
      "movl %%esp,%0\n cmpl $0,%10\n je 1f\n"
      "pushfl\n popl %2\n pusha\n pushfl\n"
      "movl %11,%%ecx\n pushl %13\n pushl %12\n call *%14\n"
      "popfl\n popa\n jmp 2f\n"
      "1: pushfl\n popl %2\n"
      "movl %11,%%ecx\n pushl %13\n pushl %12\n call *%14\n"
      "2: pushfl\n popl %3\n movl %%esp,%1\n"
      "movl %%eax,%4\n movl %%ecx,%5\n movl %%edx,%6\n"
      "movl %%ebx,%7\n movl %%esi,%8\n movl %%edi,%9\n"
      "popl %%edi\n popl %%esi\n popl %%ebx\n"
      : "=m"(before_sp),"=m"(after_sp),"=m"(before_flags),"=m"(after_flags),
        "=m"(after_eax),"=m"(after_ecx),"=m"(after_edx),"=m"(after_ebx),
        "=m"(after_esi),"=m"(after_edi)
      : "m"(preserve),"m"(context),"m"(first_arg),"m"(second_arg),"m"(target)
      : "eax","ecx","edx","memory","cc");
}

static int run_case(const char *name,DWORD ctx,DWORD first,DWORD second,DWORD save) {
    int ok;
    context=ctx;first_arg=first;second_arg=second;preserve=save;
    seen_ecx=seen_first=seen_second=seen_sp=0;
    invoke_own_callback();
    ok=seen_ecx==ctx && seen_first==first && seen_second==second && before_sp==after_sp;
    ok=ok && before_sp-seen_sp==(save?48:12);
    if (save) ok=ok && before_flags==after_flags && after_eax==0x66666666 &&
      after_ecx==0x22222222 && after_edx==0x55555555 && after_ebx==0x11111111 &&
      after_esi==0x33333333 && after_edi==0x44444444;
    else ok=ok && (after_flags&1)==1 && (before_flags&1)==0 && after_eax==0xaaaaaaaa &&
      after_ecx==0xbbbbbbbb && after_edx==0xcccccccc && after_ebx==0xdddddddd &&
      after_esi==0xeeeeeeee && after_edi==0xffffffff;
    printf("{\"case\":\"%s\",\"ok\":%d,\"ecx\":%lu,\"arg1\":%lu,\"arg2\":%lu,"
      "\"stack_before\":%lu,\"stack_after\":%lu,\"receiver_stack\":%lu,"
      "\"flags_before\":%lu,\"flags_after\":%lu,\"preserve\":%lu}\n",
      name,ok,seen_ecx,seen_first,seen_second,before_sp,after_sp,seen_sp,before_flags,after_flags,save);
    return ok;
}

int main(void) {
    BYTE *code;
    int ok=1;
    if (sizeof(void *)!=4) { fprintf(stderr,"Own32-bit fixture required\n");return 2; }
    code=make_own_callback();
    if (!code) { fprintf(stderr,"Own allocation failed%lu\n",GetLastError());return 3; }
    target=(DWORD)(ULONG_PTR)code;
    ok &= run_case("vip_slot",0x12345678,0x87654321,0x04000000,0);
    ok &= run_case("inn_slot_preserve",0x12345678,0x87654321,0x04000000,1);
    ok &= run_case("dialog_button",0x12345678,0xabcd,1,0);
    ok &= run_case("page_button",0x12345678,0xabce,1,0);
    VirtualFree(code,0,MEM_RELEASE);
    return ok?0:4;
}
