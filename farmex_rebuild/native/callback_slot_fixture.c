/* Own x86 writable-slot experiment. No game PID, module loading or external IO.
 * Reuses our prior RET0 receiver/context wrapper, not vendor machine code.
 */
#define main context_callback_fixture_original_main
#include "context_callback_fixture.c"
#undef main

static DWORD own_table[64];
static DWORD table_slot_offset=0x8c;

static DWORD *computed_slot(void) {
    DWORD root,object,table;
    memcpy(&root,(void *)(ULONG_PTR)root_slot_address,4);
    memcpy(&object,(BYTE *)(ULONG_PTR)root+field_offset,4);
    memcpy(&table,(void *)(ULONG_PTR)object,4);
    return (DWORD *)(ULONG_PTR)(table+table_slot_offset);
}
static void replace_own_slot(DWORD *saved,DWORD *target,DWORD replacement) {
    /* Guarded source read/protection effects are not emulated here. */
    if(*saved==0)memcpy(saved,target,4);
    memcpy(target,&replacement,4);
}
static void attempt_own_install(BYTE *attempted,DWORD probe_eax,LONG age,DWORD replacement) {
    if(!*attempted) {
        if((probe_eax&255)==0 && age>90)
            replace_own_slot(&previous_callback,computed_slot(),replacement);
        *attempted=1;
    }
}
static int check_gate(const char *name,DWORD probe,LONG age,int install,DWORD original,DWORD replacement) {
    BYTE attempted=0;int ok;
    previous_callback=0;*computed_slot()=original;
    attempt_own_install(&attempted,probe,age,replacement);
    ok=attempted==1 && *computed_slot()==(install?replacement:original)
       && previous_callback==(install?original:0);
    printf("{\"case\":\"%s\",\"ok\":%d,\"attempted\":%u,\"slot\":%lu,\"saved\":%lu}\n",
           name,ok,(unsigned)attempted,*computed_slot(),previous_callback);
    return ok;
}
int main(void) {
    BYTE *receiver,*wrapper1,*wrapper2;DWORD object,table;BYTE attempted=0;int ok=1,local;
    if(sizeof(void *)!=4)return 2;
    receiver=make_receiver();wrapper1=make_wrapper();wrapper2=make_wrapper();
    if(!receiver || !wrapper1 || !wrapper2) {
        if(receiver)VirtualFree(receiver,0,MEM_RELEASE);
        if(wrapper1)VirtualFree(wrapper1,0,MEM_RELEASE);
        if(wrapper2)VirtualFree(wrapper2,0,MEM_RELEASE);
        return 3;
    }
    memset(first_arena,0,sizeof(first_arena));memset(second_arena,0,sizeof(second_arena));
    object=(DWORD)(ULONG_PTR)second_arena;table=(DWORD)(ULONG_PTR)own_table;
    memcpy(second_arena,&table,4);memcpy(first_arena+0x3b0,&object,4);
    own_root_value=(DWORD)(ULONG_PTR)first_arena;root_slot_address=(DWORD)(ULONG_PTR)&own_root_value;field_offset=0x3b0;
    local=computed_slot()==&own_table[0x8c/4];ok &= local;
    printf("{\"case\":\"root_object_table_slot\",\"ok\":%d,\"context_offset\":944,\"slot_offset\":140}\n",local);
    ok &= check_gate("age90_skips_but_marks_attempt",0,90,0,(DWORD)(ULONG_PTR)receiver,(DWORD)(ULONG_PTR)wrapper1);
    ok &= check_gate("age91_installs",0,91,1,(DWORD)(ULONG_PTR)receiver,(DWORD)(ULONG_PTR)wrapper1);
    ok &= check_gate("probe_lowAL_nonzero_skips",0x101,91,0,(DWORD)(ULONG_PTR)receiver,(DWORD)(ULONG_PTR)wrapper1);
    ok &= check_gate("probe_upper_only_is_zero_AL",0x100,91,1,(DWORD)(ULONG_PTR)receiver,(DWORD)(ULONG_PTR)wrapper1);
    ok &= check_gate("negative_age_skips",0,-1,0,(DWORD)(ULONG_PTR)receiver,(DWORD)(ULONG_PTR)wrapper1);
    previous_callback=0;*computed_slot()=(DWORD)(ULONG_PTR)receiver;
    attempt_own_install(&attempted,0,90,(DWORD)(ULONG_PTR)wrapper1);
    attempt_own_install(&attempted,0,91,(DWORD)(ULONG_PTR)wrapper1);
    local=attempted==1 && previous_callback==0 && *computed_slot()==(DWORD)(ULONG_PTR)receiver;ok &= local;
    printf("{\"case\":\"marked_attempt_does_not_retry\",\"ok\":%d}\n",local);
    previous_callback=0;replace_own_slot(&previous_callback,computed_slot(),(DWORD)(ULONG_PTR)wrapper1);
    local=previous_callback==(DWORD)(ULONG_PTR)receiver && *computed_slot()==(DWORD)(ULONG_PTR)wrapper1;ok &= local;
    if(local) {
        wrapper_address=*computed_slot();ok &= run_case("installed_slot_context_dispatch",first_arena,0x3b0,object);
    }
    replace_own_slot(&previous_callback,computed_slot(),(DWORD)(ULONG_PTR)wrapper2);
    local=previous_callback==(DWORD)(ULONG_PTR)receiver && *computed_slot()==(DWORD)(ULONG_PTR)wrapper2;ok &= local;
    printf("{\"case\":\"rehook_preserves_original\",\"ok\":%d}\n",local);
    if(local) {
        wrapper_address=*computed_slot();ok &= run_case("replaced_slot_context_dispatch",first_arena,0x3b0,object);
    }
    previous_callback=0;*computed_slot()=0;
    replace_own_slot(&previous_callback,computed_slot(),(DWORD)(ULONG_PTR)wrapper1);
    local=previous_callback==0 && *computed_slot()==(DWORD)(ULONG_PTR)wrapper1;ok &= local;
    printf("{\"case\":\"zero_original_no_invented_guard_no_dispatch\",\"ok\":%d}\n",local);
    field_offset=0x370;memcpy(first_arena+field_offset,&object,4);
    previous_callback=0;*computed_slot()=(DWORD)(ULONG_PTR)receiver;
    replace_own_slot(&previous_callback,computed_slot(),(DWORD)(ULONG_PTR)wrapper1);
    local=previous_callback==(DWORD)(ULONG_PTR)receiver && computed_slot()==&own_table[0x8c/4];ok &= local;
    if(local) {
        wrapper_address=*computed_slot();ok &= run_case("legacy_context_370_dispatch",first_arena,0x370,object);
    }
    VirtualFree(wrapper2,0,MEM_RELEASE);VirtualFree(wrapper1,0,MEM_RELEASE);VirtualFree(receiver,0,MEM_RELEASE);
    return ok?0:4;
}
