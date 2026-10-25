# SMerchant rota seçimi ve yerel import bağı

19 Ekim güncellemesi: Input/factory/plan artık SMerchant veya BMerchant
kind'ini ve doğru global adresini taşır. Ayrı BUY source failure API'si
[BUY_FAILURE.md](BUY_FAILURE.md) içinde; SELL UI bağı
[SELL_BANK_ROUTE_UI.md](SELL_BANK_ROUTE_UI.md) içindedir. Aşağıdaki yalnız-SELL
ve UI-yok notları önceki aşamayı anlatır. Native helper/start/live açık.

Sonraki start bağı: `start_execution` ve ayrı prestart span gözlemi, normal
başlatma yardımcısının reset/saat/taze count/active sırasını kendi state'inde bağlar.
Import ready ile start completion ayrıdır. [ROUTE_START_STATE.md](ROUTE_START_STATE.md).

18 Ekim 2026: `merchant_bank_route.py`, mevcut global-route seçicisi ile yerel
source-route importer'ını SELL başarısızlık dalına isteğe bağlı bağlar. Yeni bir
native rota motoru değildir. Hareket, banka/NPC işlemi, dosya yazma veya oyun
bağlantısı yapılmaz. Workbench için yeni giriş kontrolleri henüz eklenmedi.

`MerchantBankRouteInputs.filename_ansi`, gözlenen global005698bc ANSI dosya
adıdır. `SMerchant` adı doğrudan bu dalı seçer; panel combo ItemIndex'i veya
profile Unicode text'i bunun yerine konmaz. Dosya adı eksikse bilinmiyor,
bilinen boş bytes ise unselected yoludur. İkisi başarı değildir.

Nonempty dosya adı için route-object +57c alanının ayrı ANSI prefix gözlemi ve
kendi yerel `WindowsNameCodec` bağlamı gerekir. Prefix ile filename kaynak gibi
doğrudan birleştirilir. Yerel importer yalnız açık yolun Count/Value ve ROUTE
alanlarını okur; klasör taraması yapmaz. İsimlerin yol güvenliği, codepage ve
satır bütçesi mevcut importer'ın kendi kurallarıdır; kaynak RTL'nin tam emülasyonu
değildir. `SupplyRouteState` burada kendi bookkeeping nesnesidir; SMerchant dalı
cyclic sayaçları okumaz/değiştirmez. Varsayılan0değerleri native counter gözlemi
olarak yorumlanmaz.

`plan_merchant_bank_route.ready`, yalnız yerel dosyadaki desteklenen satırların
kendi RouteStep nesnelerine aktarılmış olmasıdır. Native loader/helper return,
route durum alanları veya oyun başarısı değildir. Empty/missing dosya, nonpositive
count, desteklenmeyen satır veya kendi row-budget aşımı ready üretmez. Sonraki
çalışma ilk üç kaynak hata dalının normal caller sırasını ayrı gözlemlerle
modeller; helper iç etkileri ve kendi unsupported/budget gap'leri açık kalır.

`SellFailureObservation.route_inputs`, bank dalının iki status span'ı tamamlanınca
bu planı çalıştırır. Önceki header/alarm/policy/status gap'lerinde yerel dosyaya
erişilmez. Bound import eksikken `route_span_returned=True` bile bunu atlayamaz.
Tersine import ready olsa da ayrı route string/call/cleanup normal dönüşü gerekir.
Bu iki gate native helper'ın bütün etkilerini doğrulamaz. Prefix phase0/gate yazıları
eksik sonraki gözlemde prospective kalır; accepted runner erken ilerlemez.

## Kanıt

`work/audit_merchant_bank_route.py`, eski004ebca0/güncel004ebcbc fonksiyonlarında
toplam **3076 çıkarılmış talimat kaydını** disk baytlarıyla doğruladı. Bu sayı
3076talimatın semantiğinin çözüldüğünü göstermez. Semantik scope, SMerchant
literal/global copy dalı ile +57c prefix ve Count/Value okuma caller'ıdır.
Global005698bc, literalSMerchant, prefix+57c ve signed nonpositive count branch'i
ayrı kontrol edilir. RTL string/helper gövdeleri, native phase/reset yazıları,
tam hata/cleanup akışı ve loaded-runtime ABI eşdeğerliği kanıtlanmadı.
Rapor `outputs/FarmexBot_SMerchant_rota_bagi_kod_kaniti.json`.
Ghidra statik kanıtıdır; REA Evidence değildir. Eski auditlerde aynı fonksiyonun
baytları bulunduğundan bu kayıt sayısı benzersiz toplam kapsama eklenmez.

## Doğrulama

8 yeni test dahil **2001 yerel test geçti** (6.988 saniye). Yalnız kendi geçici
dizinlerindeki route fixture'larıyla dosya seçimi, eksik prefix/codec, Bekle ve
Koordinat satırları, missing/nonpositive/unsupported/budget gap'leri, erken dosya
erişimini atlama ve bağımsız dış helper dönüşü koşulu sınandı. Orijinal kullanıcı
rota/settings dosyaları okunmadı. UI değişmedi; UI smoke tekrar çalıştırılmadı.
Gerçek route/helper/NPC/banka etkileri ve canlı uyumluluk açık kalır.

## Kaynak hata caller'ı

`complete` ve `ready` ayrıdır. Yerel dosya seçimi üç kaynak hata yolundan birini
gösterirse plan `stop_required=True` olur, fakat ayrı dönüşler tamamlanmadan
`complete=False` kalır. Boş filename hiçbir prefix/codec/dosya okuması istemez.
Missing dosya ile signed Count<=0 ayrı error-message construction span'larıdır.

| Dal | Mesaj hazırlama span'ı |
|---|---|
| Unselected | 004ed23d..004ed2c9 |
| File missing | 004ed0cf..004ed214 |
| Nonpositive count | 004ecf79..004ed0be |

`error_message_returned` sonrasında yalnız nonempty dosya yollarında
`path_cleanup_returned` gerekir (004ed217..004ed22c). Sonra ayrı
`error_stop_returned` gözlemi 004ed2d3 stop callsite'ını, ardından
`error_notification_returned` 004ed2db..004ed336 span'ını ve
`error_final_cleanup_returned` 004ed339..004ed38a span'ını tamamlar. Sonraki
receipt önceki eksik adımı atlayamaz. Gerçek stop/bildirim/cleanup çalıştırılmaz;
bunlar kendi koşullu normal caller planımızdır. Hata metni RTL gibi üretilmez.

Tam hata planı `ready=False,complete=True` döner; geçerli rota gibi başlatılmaz.
Parent SELL failure caller'ı yine ayrı dış route-span dönüşünü ister. Ancak
ondan sonra prefix phase0/gate yazılarını kendi accepted state'ine taşır ve
`bank_route_load_failed` kendi stop politikasını uygular. Bank-route niyeti
üretilmez. Native global-stop alanları veya helper yan etkileri taklit edilmez.
Eksik dönüşte accepted phase2 korunur; source prefix yazıları prospective'tir.

Unsupported yerel satır ve kendi row-budget limiti, bu kaynak hata dallarıyla
eşitlenmez. Tüm hata receipt'leri verilse bile bu durumlar açık gap kalır.
Raw satırların native loader'a yerleştirilmesi/sonraki yürütmesi, success phase
başlatma alanları, fault ve unwind hâlâ ayrı çözümleme gerektirir.

Audit'e empty/FileExists/count branch hedefleri, path cleanup, stop, bildirim ve
final cleanup anchor'ları eklendi. **3076**çıkarılmış talimat baytı sayısı aynı
fonksiyonlara aittir; yeni benzersiz kapsam olarak toplanmaz. Normal hata caller
sırası genişledi, tam helper semantiği sertifikalanmadı.
6 yeni testle **2007 yerel test geçti** (6.972 saniye). Kendi geçici rota
dosyalarıyla Count0/ffffffff, missing/unselected, receipt önceliği, unsupported
gap ve parent stop bağları sınandı. UI değişmedi, UI smoke tekrarlanmadı.
