# Seçilen satış yuvasının tampon ve kuyruk planı

18 Ekim 2026: `merchant_sell_tail.py`, tamamlanmış bir `SellSelectionPlan` için
`00420aac/00420ca8` yardımcılarının kalan normal sırasını kendi state ve kuyruğu
üzerinde planlar. `work/audit_sell_tail.py`, iki ikilide654talimat kaydı,
28import çağrısı kimliği, iki14bayt başlangıç tamponu ve iki binary64 sabitini
diskten doğrular. Rapor `outputs/FarmexBot_satis_slot_tail_kod_kaniti.json`.
Bu654kayıt önceki seçim auditleriyle örtüşür; benzersiz toplama eklenmez.
Ghidra/import/data statik kanıtıdır; REA Evidence veya native CPU yürütmesi değildir.

`SellSlotFrame` explicit own `SellSlotState` ve `QueueState` alır; canlı nesne
adresi veya süreç handle'ı almaz. State varsayılanları kendi sıfır başlangıç
örneğidir, gerçek oyundan ölçüm değildir. Seçim unmatched/eksikse frame kurulmaz.
Normal sıra:

1. Seçilen mutlak slotun used byte'ı `+0x59+slot=1`, ardından pending `BYTE +0x28=1`.
2. Ayrı açık GetTickCount DWORD sonucu sıfır genişletilerek `QWORD +0x30` alanına yazılır.
3. `lowDWORD(full_quantity_DWORD*price_DWORD)` sıfır genişletilip `QWORD +0x98` alanına eklenir.
4. Kaynak total'i signed QWORD olarak x87'ye iki kez yükler, ikinci kopyayı
   binary64 `b81e85eb51b89e3f` (0.03) ile çarpar, FSUBP sonrası `__ftol` çağırır.
   EDX:EAX sonucu `QWORD +0xa0` alanına yazılır. Varsayılan yol bu sonucu **açık gözlem** olarak ister.
   Sonradan exact rational disk-CRT replay eklendi; [SELL_X87.md](SELL_X87.md).
   Açık CW/temiz bağlam gerektirir, native oyun bağlamını varsaymaz.
5. Beş ayrı `_memcpy` normal dönüşü sırasıyla4/2/4/1/1bayt alanlarını tamamlar.
6. `004c7710` için14bayt/delay0yerel enqueue planı üretilir. Ayrı gate ve queue
   tick gözlemleri kullanılır. Gate0yolunda tick gerekmez ve kayıt eklenmez.
7. Enqueue normal dönüşü ayrıca gözlenince prepared-slot `DWORD +0x84` bir artar;
   DWORD taşması korunur. Bilinen sonuç yalnız AL=1dir; tam EAX/sunucu ACK'i değildir.

## Tampon

Başlangıç `6803000000000000000000000000` her iki kaynakta aynıdır.

| Offset | Boyut | Alan |
| --- | --- | --- |
| 0 | 2 | 68 03 |
| 2 | 4 | Item DWORD |
| 6 | 2 | Adedin düşük WORD'u |
| 8 | 4 | Fiyatın düşük DWORD'u |
| 12 | 1 | Mutlak slot-14 (0..27) |
| 13 | 1 | Artıştan önceki prepared-slot DWORD'un düşük byte'ı |

Maliyet hesabı tam DWORD adedi kullanır; tampon düşük WORD alır. Bunlar aynı
değere zorlanmaz. Gate0olsa da helper normal dönünce prepared-slot artabilir ve
pending1kalır; yerel AL veya sayaç artışı gerçek gönderim/satış kanıtı değildir.

## Eksik gözlemler ve runner bağı

Kabul edilen state/queue girişte kalır; source prefix ayrı prospective alanlarda
gösterilir. Frame bilinen saat/ftol sonucunu ve tamamlanan kopyaları dondurur.
Enqueue kopyası tamamlanıp normal-return gözlemi eksik kalırsa sonraki step aynı
kayıt ID'sini korur; yeniden enqueue etmez. Tamamlanan frame tekrar çağrılınca
aynı sonucu verir. Bu kendi gözlem replay'imizin devamıdır; gerçek native thread
dondurma/devam etme, callback/heap eşzamanlılığı veya rollback değildir.

`MerchantSnapshot.sell_slot_execution`, mevcut typed SELL seçim yoluna bu
kararı bağlar. Seçim planı ve giriş pazar-yuva sayacı snapshot'la eşleşmelidir.
Eksik frame yanında opaque `sell_slot_helper_returned` verilip bypass yapılamaz.
Caller index'i ancak frame tamamlanınca ilerler. Item timestamp explicit tail
damgasından alınır; dış runner'ın tüm SELL timeout/source-clock davranışı bu
bağla çözülmüş sayılmaz. Kaynak saat ile monoton demo saati eşlemesi ayrı konudur.

QueueSample içinde yalnız enqueue gate/tick kullanılır; sender dönüşü veya ACK
üretilmez. Kuyruk drain edilmez, native fonksiyon çağrılmaz, gerçek belleğe veya
oyuna veri yazılmaz. Workbench henüz tail gözlemleri için kontrol sunmaz; yeni
bağ API düzeyindedir. Gerçek envanter/runtime/x87 bağlamı, native heap ve canlı uyumluluk açıktır.

15yeni test; pending/clock sırası, FTOL gap,14bayt layout, beş bağımsız kopya,
cached enqueue, gate0, eksik tick/gate, frozen veri, DWORD sayaç taşması, runner
beklemesi, uyuşmayan pazar sayacı, sıfır gözlemler ve son çanta slotunu kapsar.
Tam birim çalıştırmasında **1841 test geçti** (7.560 saniye).
Önceki maliyet ve hazırlık gizli UI kontrolleri yeniden geçti. Bu değişiklikte
UI düzenlenmedi; genel smoke son maliyet-modu aşamasındaki kayıttır.
