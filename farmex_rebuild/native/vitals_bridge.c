/* Read-only own-process bridge. No injector, hooks, privilege changes or actions. */
#include "vitals_bridge.h"
#include "image_identity.h"
#include "shared_vitals.h"
#include <string.h>

static int process_name_matches(const char *expected, int full_path) {
    char name[32768];
    DWORD n = GetModuleFileNameA(NULL, name, sizeof(name));
    char *base;
    if (!n || n >= sizeof(name)) return 0;
    if (full_path) return _stricmp(name, expected) == 0;
    base = strrchr(name, '\\');
    return _stricmp(base ? base + 1 : name, expected) == 0;
}

static int read_dword(DWORD address, DWORD *value, FarmexVitals *out, DWORD step) {
    SIZE_T count = 0;
    BOOL ok = ReadProcessMemory(GetCurrentProcess(), (LPCVOID)(ULONG_PTR)address,
                                value, 4, &count);
    out->bytes_read += count > 4 ? 4 : count;
    if (!ok || count != 4) {
        out->status = FARMEX_READ_ERROR;
        out->win_error = ok ? ERROR_PARTIAL_COPY : GetLastError();
        out->failed_read_step = step;
        return 0;
    }
    return 1;
}

static DWORD read_vitals(DWORD slot, DWORD profile, DWORD refreshed, FarmexVitals *out) {
    DWORD root, repeated, hp, hp_max, mp, mp_max;
    DWORD mp_offset = !refreshed && profile == 1 ? 0xbf0 : 0xd60;
    if (!read_dword(slot, &root, out, 1)) return out->status;
    if (root < 0x10000 || root > 0xffff0000 || (root & 3))
        return out->status = FARMEX_INVALID_ROOT;
    if (!read_dword(root + 0x6d8, &hp, out, 2) ||
        !read_dword(root + 0x6d4, &hp_max, out, 3) ||
        !read_dword(root + mp_offset, &mp, out, 4) ||
        !read_dword(root + mp_offset - 4, &mp_max, out, 5) ||
        !read_dword(slot, &repeated, out, 6)) return out->status;
    if (root != repeated) return out->status = FARMEX_ROOT_CHANGED;
    if (!hp_max || !mp_max || hp_max >= 10000000 || mp_max >= 10000000 ||
        hp > hp_max || mp > mp_max) return out->status = FARMEX_INVALID_VITALS;
    out->hp = hp;
    out->hp_max = hp_max;
    out->mp = mp;
    out->mp_max = mp_max;
    return out->status = FARMEX_CANDIDATE;
}

static int initialize(DWORD profile, FarmexVitals *out, DWORD size) {
    if (!out || size != sizeof(FarmexVitals)) return 0;
    memset(out, 0, sizeof(FarmexVitals));
    out->abi_version = FARMEX_ABI_VERSION;
    out->struct_size = sizeof(FarmexVitals);
    out->status = FARMEX_INVALID_ARGUMENT;
    out->process_id = GetCurrentProcessId();
    out->timestamp_ms = GetTickCount();
    out->profile = profile;
    return sizeof(void *) == 4 && (profile == 1 || profile == 2);
}

__declspec(dllexport) DWORD __cdecl FarmexObserve(DWORD profile, FarmexVitals *out, DWORD size) {
    IMAGE_DOS_HEADER *dos;
    IMAGE_NT_HEADERS *nt;
    DWORD identity, refreshed = 0;
    static const BYTE expected_game_sha256[32]={
        0xad,0xec,0xcd,0xc6,0x68,0x14,0x42,0x2e,0x47,0xff,0xc6,0x6b,0x9a,0x56,0x59,0xa2,
        0xf9,0x48,0x7a,0xad,0x6d,0x4a,0x52,0x89,0xa7,0x82,0x61,0xd9,0x4a,0x3e,0x70,0x0a};
    static const BYTE refreshed_game_sha256[32]={
        0xca,0x69,0xce,0xce,0xbd,0xef,0xd8,0x2b,0x40,0x9c,0xa8,0xcf,0x04,0x16,0x55,0xda,
        0x53,0xcb,0x97,0x11,0x3b,0x06,0x8a,0x08,0x6c,0x5f,0x7a,0x6e,0xf7,0xe9,0x52,0xa9};
    if (!initialize(profile, out, size)) return FARMEX_INVALID_ARGUMENT;
    if (!process_name_matches("C:\\NTTGame\\KnightOnlineEn\\KnightOnLine.exe", 1))
        return out->status = FARMEX_WRONG_PROCESS;
    dos = (IMAGE_DOS_HEADER *)GetModuleHandleA(NULL);
    if ((DWORD)(ULONG_PTR)dos != 0x400000 || dos->e_magic != IMAGE_DOS_SIGNATURE ||
        dos->e_lfanew < 0 || dos->e_lfanew > 0x100000)
        return out->status = FARMEX_UNSUPPORTED_IMAGE;
    nt = (IMAGE_NT_HEADERS *)((BYTE *)dos + dos->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE || nt->FileHeader.Machine != 0x14c ||
        nt->OptionalHeader.Magic != 0x10b || nt->OptionalHeader.ImageBase != 0x400000 ||
        (nt->OptionalHeader.DllCharacteristics & 0x40))
        return out->status = FARMEX_UNSUPPORTED_IMAGE;
    identity=farmex_check_image_file("C:\\NTTGame\\KnightOnlineEn\\KnightOnLine.exe",
        expected_game_sha256,7009936,&out->win_error,&out->failed_read_step);
    if (identity==FARMEX_IMAGE_HASH_MISMATCH) {
        identity=farmex_check_image_file("C:\\NTTGame\\KnightOnlineEn\\KnightOnLine.exe",
            refreshed_game_sha256,7008392,&out->win_error,&out->failed_read_step);
        if (identity==FARMEX_CANDIDATE) refreshed=1;
    }
    if (identity!=FARMEX_CANDIDATE) return out->status=identity;
    return read_vitals(refreshed ? (profile == 1 ? 0x11289c0 : 0x11e9638) :
                       (profile == 1 ? 0x1115574 : 0x11ea638), profile, refreshed, out);
}

/* Own-host hashing fixture: fixed sibling files or exact selected Game file,
 * disk only. Never selects/opens a game process or reads its memory. */
__declspec(dllexport) DWORD __cdecl FarmexIdentityFixture(DWORD file_kind,const BYTE *digest,DWORD expected_size,
                                                        FarmexVitals *out,DWORD size) {
    char path[32768];char *base;DWORD n;
    if (!initialize(1,out,size)) return FARMEX_INVALID_ARGUMENT;
    if (!process_name_matches("farmex_probe_host.exe",0)) return out->status=FARMEX_WRONG_PROCESS;
    if (!digest || file_kind<1 || file_kind>5) return out->status=FARMEX_INVALID_ARGUMENT;
    if (file_kind==5) return out->status=farmex_check_image_file(
        "C:\\NTTGame\\KnightOnlineEn\\KnightOnLine.exe",digest,expected_size,&out->win_error,&out->failed_read_step);
    n=GetModuleFileNameA(NULL,path,sizeof(path));
    if (!n || n>=sizeof(path)) return out->status=FARMEX_INVALID_ARGUMENT;
    base=strrchr(path,'\\');
    if (!base || (base-path)+32>=sizeof(path)) return out->status=FARMEX_INVALID_ARGUMENT;
    strcpy(base+1,file_kind==1?"farmex_empty_fixture.bin":file_kind==2?"farmex_image_fixture.bin":
                  file_kind==3?"farmex_missing_fixture.bin":"farmex_stream_fixture.bin");
    return out->status=farmex_check_image_file(path,digest,expected_size,&out->win_error,&out->failed_read_step);
}

/* Fixture entry is restricted to our own named test host, never the game. */
__declspec(dllexport) DWORD __cdecl FarmexObserveFixture(DWORD slot, DWORD profile, FarmexVitals *out, DWORD size) {
    if (!initialize(profile, out, size)) return FARMEX_INVALID_ARGUMENT;
    if (!process_name_matches("farmex_probe_host.exe", 0))
        return out->status = FARMEX_WRONG_PROCESS;
    return read_vitals(slot, profile, 0, out);
}

/* Current-source offsets, restricted to the same own fixture host. */
__declspec(dllexport) DWORD __cdecl FarmexObserveRefreshedFixture(DWORD slot, DWORD profile, FarmexVitals *out, DWORD size) {
    if (!initialize(profile, out, size)) return FARMEX_INVALID_ARGUMENT;
    if (!process_name_matches("farmex_probe_host.exe", 0))
        return out->status = FARMEX_WRONG_PROCESS;
    return read_vitals(slot, profile, 1, out);
}

BOOL WINAPI DllMain(HINSTANCE module, DWORD reason, LPVOID reserved) {
    if (reason == DLL_PROCESS_ATTACH) { DisableThreadLibraryCalls(module);farmex_init_publisher(); }
    if (reason == DLL_PROCESS_DETACH) farmex_finish_publisher();
    return TRUE;
}
