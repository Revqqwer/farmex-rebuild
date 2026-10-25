# Satış hazırlığı result1 başarısızlık dalı

Sonraki bound rota bağı: `route_inputs`, ayrı gözlenen SMerchant filename/prefix
ve kendi codec'iyle yerel importer'ı çalıştırır. Yerel import ve dış span dönüşü
ayrı gerekir; native yürütme değildir. [MERCHANT_BANK_ROUTE.md](MERCHANT_BANK_ROUTE.md).
Aşağıdaki1993test sayısı ilk failure caller değişikliğinin tarihsel sonucudur.

18 Ekim 2026: `merchant_sell_failure.py`, erişilmiş setup-result1 için
`00421353..0042171f` caller dalını verilen normal dönüşlerle planlar.
Başka result değerleri, native yardımcı etkileri veya exception/unwind modellenmez.
`MerchantSnapshot.sell_failure_inputs` bağı yalnız SELL aşama2/setup-result1'de
tüketilir. Workbench için yeni gözlem kontrolleri henüz eklenmedi.

Önce iki ayrı status string/gösterim span'ı normal dönmelidir. Ardından alarm
BYTE +d8 okunur; nonzero ise alarm/string/cleanup span'ı ayrıca normal dönmelidir.
Bu ön adımlar eksikken politika alanına erişilmez. Coin alarmı +e0 ayrı prefix'tir.

Politika DWORD +d4 tek kez okunup saklanmaz: kaynak önce taze read0ile0'ı,
gerekirse taze read1ile1'i, sonra taze read2ile2'yi karşılaştırır. Bu nedenle
`policy_results` üçe kadar bağımsız ordered DWORD gözlemidir. Eksik sonraki
okuma önceki değerle doldurulmaz. Aynı değeri üç kez vermek kendi fixture'ın
sabit politika varsayımıdır; native eşzamanlılık garantisi değildir.

| Seçilen dal | Normal dönüş sırası |
|---|---|
| İlk okuma0 | Bildirim/string cleanup → stop helper |
| İlk0değil, ikinci1 | Stop helper → disconnect helper → bildirim/string cleanup |
| İlk0değil, ikinci1değil, üçüncü2 | Aşağıdaki BYTE90/58 dalları |
| Üçüncü de2değil | Phase yazısı/stop planlamadan normal çıkış |

Politika2'de status BYTE +90 nonzero ise ayrı bildirim span'ından sonra stop
gözlemi gerekir; +58 okunmaz. `bank_unavailable_stop_returned` kendi branch
etiketidir; +90'ın bütün producer/anlamı bu çalışmayla kanıtlanmaz.

Status0ise setup gate BYTE +58 okunur, yalnız0ise1yazılır; phase DWORD +4=0
bundan sonra, status/route işlemlerinden önce yazılır. İki bank-status span'ı ve
ayrı route string/call/cleanup span'ı gerekir. Route literal'ı diskten `SMerchant`
olarak doğrulandı; güncel callsite `004ebcbc(5687a8,...)` için plandır. Bu helper'ın
gerçek rota yüklemesi, gezinmesi veya banka işlemi uygulanmaz.

Eksik gözlemde ön yazılar `prospective_phase_dword`, `prospective_setup_gate_byte`
ve `writes` içinde görünür; runner accepted phase2/gate'i erken değiştirmez.
Bu kendi kabul politikasıdır: source stop/global/route helper'larının daha önce
oluşmuş iç yan etkilerini emüle ettiğimiz anlamına gelmez. Plan bir invocation
içindir; native callback askıya alınmaz/devam ettirilmez.

Bound runner +58 gerçekten okununca kendi setup gate'iyle tutarlılık ister;
legacy `bank_route_allowed` aynı anda verilirse reddeder. Eksik span'da eski
failure-policy yoluna düşmez. Tam route span dönüşü kendi phase0/restart ve
`load_bank_route('SMerchant')` niyetini üretir. Stop/disconnect sonuçlarında kendi
runner stop politikası uygulanır. Niyetler oyun veya bağlantı eylemi değildir.
Tanınmayan ordered politika dizisi `unresolved` kalır, otomatik stop yapılmaz.

## Kanıt ve test

`work/audit_sell_failure.py`, eski ve güncel sabit hash'li dosyalarda **498
talimat kaydının** baytlarını doğruladı. Üç ayrı politika CMP, status/gate, phase
yazısı, stop/disconnect/message sırası ve route literal'ı ayrı anchor'lardır.
Eski route hedefi004ebca0, güncel004ebcbc'dir. Caller karşılaştırmasında opaque
route rolüyle normalize edilir; helper gövdelerinin/ABI'sinin eşdeğerliği iddia
edilmez. Unicode wrapper'lar da opaque kalır. Rapor:
`outputs/FarmexBot_satis_basarisizlik_kod_kaniti.json`.
Ghidra statik kanıtıdır; REA Evidence veya native yürütme değildir. Örtüşen
kayıtlar benzersiz fonksiyon tamamlanma sayısı olarak eklenmez.

10 yeni test dahil **1993 yerel test geçti** (6.796 saniye). Header/alarm önceliği,
stop/disconnect sırası, değişebilen politika okumaları, bilinmeyen politika,
BYTE90 nonzero, conditional gate store, prospective phase0, route gap'i ve runner
legacy bypass reddi sınandı. UI değiştirilmedi; UI smoke tekrar çalıştırılmadı.
Yerel geniş başarı senaryosu bu failure branch'ini çalıştırmış sayılmaz.
Gerçek alarm, stop, disconnect, route etkileri ve canlı uyumluluk açık kalır.
