/* One self-contained x86 function. No globals, literals, CRT or direct calls.
 * Only the fixed own parent/child fixture uses the extracted bytes. */
#include "copied_worker.h"
#define FAIL(n) { c->status=(n); return (n); }
__declspec(dllexport) DWORD WINAPI FarmexOwnWorker(OwnWorkerContext *c) {
    BYTE *image,*base;DWORD i,j,k,delta,offset,rva,size,old,span,protection,value;
    IMAGE_NT_HEADERS32 *nt;IMAGE_SECTION_HEADER *sections;
    IMAGE_BASE_RELOCATION *block;WORD *words;
    IMAGE_IMPORT_DESCRIPTOR *desc;DWORD *lookup,*iat;
    IMAGE_EXPORT_DIRECTORY *exports;DWORD *names,*functions;WORD *ordinals;
    FARPROC address;FarmexPublishFixtureProc publish=NULL;OwnDllEntry entry;
    if(!c || c->magic!=0x31425746 || c->size!=sizeof(*c)) return 1;
    image=(BYTE *)c->image;
    if(c->command==1) {
        if(c->phase!=1) FAIL(2);
        nt=(IMAGE_NT_HEADERS32 *)(image+((IMAGE_DOS_HEADER *)image)->e_lfanew);
        entry=(OwnDllEntry)(image+nt->OptionalHeader.AddressOfEntryPoint);
        if(!entry((HINSTANCE)image,DLL_PROCESS_DETACH,NULL)) FAIL(3);
        for(i=2;i>0;i--) if(c->dependencies[i-1] && !c->free_library(c->dependencies[i-1])) FAIL(4);
        if(!c->free_memory(image,0,MEM_RELEASE)) FAIL(5);
        c->phase=2;c->status=0;return 0;
    }
    if(c->command || c->phase || !image || c->image==0x10000000) FAIL(6);
    for(i=0;i<0x5000;i++) if(image[i]!=c->expected_image[i]) FAIL(7);
    if(((IMAGE_DOS_HEADER *)image)->e_magic!=IMAGE_DOS_SIGNATURE) FAIL(8);
    value=((IMAGE_DOS_HEADER *)image)->e_lfanew;if(value>0x200-sizeof(*nt)) FAIL(9);
    nt=(IMAGE_NT_HEADERS32 *)(image+value);
    if(nt->Signature!=IMAGE_NT_SIGNATURE || nt->FileHeader.Machine!=IMAGE_FILE_MACHINE_I386 ||
       nt->OptionalHeader.Magic!=IMAGE_NT_OPTIONAL_HDR32_MAGIC || nt->FileHeader.NumberOfSections!=3 ||
       nt->OptionalHeader.SizeOfImage!=0x5000 || nt->OptionalHeader.SizeOfHeaders!=0x200 ||
       nt->OptionalHeader.DataDirectory[9].Size || nt->OptionalHeader.DataDirectory[13].Size ||
       nt->OptionalHeader.DataDirectory[14].Size) FAIL(10);
    delta=c->image-nt->OptionalHeader.ImageBase;
    rva=nt->OptionalHeader.DataDirectory[5].VirtualAddress;size=nt->OptionalHeader.DataDirectory[5].Size;offset=0;
    if(rva>0x5000 || size>0x5000-rva) FAIL(11);
    while(offset<size) {
        if(size-offset<8) FAIL(12);
        block=(IMAGE_BASE_RELOCATION *)(image+rva+offset);
        if(block->SizeOfBlock<8 || block->SizeOfBlock>size-offset || (block->SizeOfBlock&1)) FAIL(13);
        words=(WORD *)(block+1);
        for(j=0;j<(block->SizeOfBlock-8)/2;j++) {
            if(!words[j]) continue;
            if((words[j]>>12)!=IMAGE_REL_BASED_HIGHLOW) FAIL(14);
            value=block->VirtualAddress+(words[j]&0xfff);if(value>0x5000-4) FAIL(15);
            *(DWORD *)(image+value)+=delta;c->relocations++;
        }
        offset+=block->SizeOfBlock;
    }
    rva=nt->OptionalHeader.DataDirectory[1].VirtualAddress;size=nt->OptionalHeader.DataDirectory[1].Size;
    if(rva>0x5000 || size>0x5000-rva) FAIL(16);
    for(i=0;i<size/20;i++) {
        desc=(IMAGE_IMPORT_DESCRIPTOR *)(image+rva+20*i);
        if(!desc->OriginalFirstThunk) break;
        if(i>=2) FAIL(17);
        c->dependencies[i]=c->load_library(c->system_paths[i]);if(!c->dependencies[i]) FAIL(18);
        for(j=0;j<256;j++) {
            value=desc->OriginalFirstThunk+4*j;if(value>0x5000-4 || desc->FirstThunk+4*j>0x5000-4) FAIL(19);
            lookup=(DWORD *)(image+value);iat=(DWORD *)(image+desc->FirstThunk+4*j);
            if(!*lookup) break;
            if(*lookup&0x80000000) address=c->get_proc(c->dependencies[i],(LPCSTR)(*lookup&0xffff));
            else {
                if(*lookup>0x5000-3) FAIL(20);
                address=c->get_proc(c->dependencies[i],(LPCSTR)(image+*lookup+2));
            }
            if(!address) FAIL(21);*iat=(DWORD)address;c->imports++;
        }
        if(j==256) FAIL(22);
    }
    if(i!=2 || c->relocations!=116 || c->imports!=43) FAIL(23);
    sections=IMAGE_FIRST_SECTION(nt);
    if(!c->protect(image,0x5000,PAGE_NOACCESS,&old) || !c->protect(image,0x1000,PAGE_READONLY,&old)) FAIL(24);
    for(i=0;i<3;i++) {
        span=sections[i].Misc.VirtualSize>sections[i].SizeOfRawData?sections[i].Misc.VirtualSize:sections[i].SizeOfRawData;
        protection=(sections[i].Characteristics&IMAGE_SCN_MEM_EXECUTE)?PAGE_EXECUTE_READ:
                    ((sections[i].Characteristics&IMAGE_SCN_MEM_WRITE)?PAGE_READWRITE:PAGE_READONLY);
        if(!c->protect(image+sections[i].VirtualAddress,span,protection,&old)) FAIL(25);
    }
    if(!c->flush(c->current(),image,0x5000)) FAIL(26);
    entry=(OwnDllEntry)(image+nt->OptionalHeader.AddressOfEntryPoint);
    if(!entry((HINSTANCE)image,DLL_PROCESS_ATTACH,NULL)) FAIL(27);
    rva=nt->OptionalHeader.DataDirectory[0].VirtualAddress;size=nt->OptionalHeader.DataDirectory[0].Size;
    if(rva>0x5000-sizeof(*exports)) FAIL(28);
    exports=(IMAGE_EXPORT_DIRECTORY *)(image+rva);
    if(exports->NumberOfNames>64 || exports->NumberOfFunctions>64) FAIL(29);
    names=(DWORD *)(image+exports->AddressOfNames);functions=(DWORD *)(image+exports->AddressOfFunctions);
    ordinals=(WORD *)(image+exports->AddressOfNameOrdinals);
    for(i=0;i<exports->NumberOfNames;i++) {
        base=image+names[i];
        for(k=0;k<sizeof(c->export_name);k++) if(base[k]!=c->export_name[k] || !base[k]) break;
        if(k==sizeof(c->export_name) || base[k]!=c->export_name[k]) continue;
        value=functions[ordinals[i]];if(value>=rva && value-rva<size) FAIL(30);
        publish=(FarmexPublishFixtureProc)(image+value);break;
    }
    if(!publish || publish((DWORD)&c->fixture_root,1,c->mapping_name)) FAIL(31);
    c->phase=1;c->status=0;return 0;
}
__declspec(dllexport) DWORD WINAPI FarmexOwnWorkerEnd(void) { return 0; }
int main(void) { return 0; }
