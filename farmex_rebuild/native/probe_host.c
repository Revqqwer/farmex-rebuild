/* Loads our DLL only into this own host. Does not open or modify the game. */
#include "vitals_bridge.h"
#include <stdio.h>
#include <string.h>

static BYTE arena[4096];
static DWORD root;

static void set_value(DWORD offset, DWORD value) { memcpy(arena + offset, &value, 4); }

static void report(const char *name, DWORD returned, FarmexVitals *s) {
    printf("{\"case\":\"%s\",\"returned\":%lu,\"status\":%lu,\"abi\":%lu,"
           "\"size\":%lu,\"pid\":%lu,\"bytes_read\":%lu,\"win_error\":%lu,"
           "\"failed_read_step\":%lu,\"hp\":%lu,\"hp_max\":%lu,\"mp\":%lu,\"mp_max\":%lu}\n",
           name, returned, s->status, s->abi_version, s->struct_size, s->process_id,
           s->bytes_read, s->win_error, s->failed_read_step, s->hp, s->hp_max, s->mp, s->mp_max);
}

int main(int argc, char **argv) {
    HMODULE module;
    FarmexObserveProc production;
    FarmexFixtureProc fixture;
    FarmexFixtureProc refreshed_fixture;
    FarmexIdentityFixtureProc identity;
    BYTE wrong_digest[32];
    static const BYTE empty_digest[32]={0xe3,0xb0,0xc4,0x42,0x98,0xfc,0x1c,0x14,0x9a,0xfb,0xf4,0xc8,0x99,0x6f,0xb9,0x24,
      0x27,0xae,0x41,0xe4,0x64,0x9b,0x93,0x4c,0xa4,0x95,0x99,0x1b,0x78,0x52,0xb8,0x55};
    static const BYTE abc_digest[32]={0xba,0x78,0x16,0xbf,0x8f,0x01,0xcf,0xea,0x41,0x41,0x40,0xde,0x5d,0xae,0x22,0x23,
      0xb0,0x03,0x61,0xa3,0x96,0x17,0x7a,0x9c,0xb4,0x10,0xff,0x61,0xf2,0x00,0x15,0xad};
    static const BYTE stream_digest[32]={0xac,0x72,0x11,0x2c,0x83,0x2f,0xa4,0x68,0x3b,0x15,0xeb,0xff,0x51,0xa8,0xf5,0xf2,
      0xca,0x08,0x22,0x6c,0x0d,0x59,0xbd,0xb9,0xac,0x73,0x9c,0x2c,0xdc,0x28,0xa0,0x5c};
    static const BYTE game_digest[32]={0xca,0x69,0xce,0xce,0xbd,0xef,0xd8,0x2b,0x40,0x9c,0xa8,0xcf,0x04,0x16,0x55,0xda,
      0x53,0xcb,0x97,0x11,0x3b,0x06,0x8a,0x08,0x6c,0x5f,0x7a,0x6e,0xf7,0xe9,0x52,0xa9};
    FarmexVitals s;
    DWORD r;
    if (argc != 2) { fprintf(stderr, "Expected exact own DLL path\n"); return 2; }
    module = LoadLibraryA(argv[1]);
    if (!module) { fprintf(stderr, "LoadLibrary error%lu\n", GetLastError()); return 3; }
    production = (FarmexObserveProc)GetProcAddress(module, "FarmexObserve");
    fixture = (FarmexFixtureProc)GetProcAddress(module, "FarmexObserveFixture");
    refreshed_fixture = (FarmexFixtureProc)GetProcAddress(module, "FarmexObserveRefreshedFixture");
    identity = (FarmexIdentityFixtureProc)GetProcAddress(module,"FarmexIdentityFixture");
    if (!production || !fixture || !refreshed_fixture || !identity) { fprintf(stderr, "Missing own exports\n"); FreeLibrary(module); return 4; }
    root = (DWORD)(ULONG_PTR)arena;
    set_value(0x6d8, 250); set_value(0x6d4, 500);
    set_value(0xbf0, 100); set_value(0xbec, 300);
    set_value(0xd60, 110); set_value(0xd5c, 310);
    r = fixture((DWORD)(ULONG_PTR)&root, 1, &s, sizeof(s)); report("fixture_us", r, &s);
    r = fixture((DWORD)(ULONG_PTR)&root, 2, &s, sizeof(s)); report("fixture_steam", r, &s);
    r = refreshed_fixture((DWORD)(ULONG_PTR)&root, 1, &s, sizeof(s)); report("refreshed_fixture_us", r, &s);
    r = refreshed_fixture((DWORD)(ULONG_PTR)&root, 2, &s, sizeof(s)); report("refreshed_fixture_steam", r, &s);
    r = production(1, &s, sizeof(s)); report("production_wrong_process", r, &s);
    root = 3;
    r = fixture((DWORD)(ULONG_PTR)&root, 1, &s, sizeof(s)); report("invalid_root", r, &s);
    root = (DWORD)(ULONG_PTR)arena;
    r = fixture(1, 1, &s, sizeof(s)); report("invalid_slot", r, &s);
    set_value(0x6d8, 501);
    r = fixture((DWORD)(ULONG_PTR)&root, 1, &s, sizeof(s)); report("invalid_vitals", r, &s);
    r = fixture((DWORD)(ULONG_PTR)&root, 9, &s, sizeof(s)); report("invalid_profile", r, &s);
    memset(&s, 0, sizeof(s));
    r = fixture((DWORD)(ULONG_PTR)&root, 1, &s, sizeof(s)-1); report("invalid_output_size", r, &s);
    r=identity(1,empty_digest,0,&s,sizeof(s));report("identity_empty",r,&s);
    r=identity(2,abc_digest,3,&s,sizeof(s));report("identity_abc",r,&s);
    memcpy(wrong_digest,abc_digest,32);wrong_digest[0]^=1;
    r=identity(2,wrong_digest,3,&s,sizeof(s));report("identity_wrong_hash",r,&s);
    r=identity(2,abc_digest,4,&s,sizeof(s));report("identity_wrong_size",r,&s);
    r=identity(3,abc_digest,3,&s,sizeof(s));report("identity_missing",r,&s);
    r=identity(4,stream_digest,65537,&s,sizeof(s));report("identity_stream",r,&s);
    r=identity(5,game_digest,7008392,&s,sizeof(s));report("identity_game_file",r,&s);
    r=identity(9,abc_digest,3,&s,sizeof(s));report("identity_invalid_kind",r,&s);
    r=identity(2,NULL,3,&s,sizeof(s));report("identity_null_digest",r,&s);
    FreeLibrary(module);
    return 0;
}
