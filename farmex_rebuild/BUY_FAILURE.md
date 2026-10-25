# BUY başarısızlık dalı ve192slot sayımı

19 Ekim banka eşya okuma modeli: Sıralı guarded pointer okumaları, DWORD taşması ve unsigned varyant hesabı 192 slot sayacına ve BUY failure API zincirine bağlandı. **2493 test geçti (6.745 saniye)**; gizli arayüz regresyonu 1037 kontrol/11 form/18 sekmede geçti. İki sürümde mevcut 960 talimatlık kapsam yeniden doğrulandı. Native helper ve canlı oyun uyumluluğu açık. Ayrıntı: [BANK_ITEM_READER.md](BANK_ITEM_READER.md).

Güncelleme: Default-off BUY failure JSON/lazy factory ve BMerchant rolü
denetlenen yerel RoutePage aktarımı bağlandı. [BUY_FAILURE_UI.md](BUY_FAILURE_UI.md)
güncel UI kapsamıdır. Aşağıdaki UI-yok notları API aşamasına aittir;
native/start/clock/oyun uyumluluğu hâlâ açıktır.

19 Ekim2026. `merchant_buy_failure.py`,4220c8 caller'ının **setup sonucu1
dalına ulaşıldıktan sonraki**4224b4..422a52normal akışını modeller. Önceki
status/prefix ve hazırlık yardımcısının kendisi bu entry varsayımına dahil
edilmez. Native/oyun IO yoktur.

## SELL ile farklar

BUY önce42070c envanter sayımını **yeniden** çağırır; önceki hazırlığın count
sonucu kullanılmaz. Raw DWORD veya ayrı MerchantInventoryObservation girdisi
alınır, normal-return receipt'i ayrıca gerekir. Count ve+120threshold signed
karşılaştırılır. Count<=threshold ise+124alarm BYTE okunur; nonzero için ayrı
alarm span dönüşü gerekir. Count büyükse alarm BYTE/span tüketilmez.

Üç bağımsız+11cpolicy okuması0stop/1disconnect/2bank dallarını seçer.
Stop: notification sonra stop. Disconnect: stop,disconnect,notification.
Bank dalında SELL'in+90BYTE gate'i kullanılmaz: context5690e0ile46ff6c
çağrılır. EAX bir azaltılır ve **signed JL** ile bank-unavailable seçilir.
Unavailable yolu **stop sonra notification** sırasındadır; SELL'in burada
notification-before-stop sırası kopyalanmadı.

Raw helper EAX için low32DEC tam uygulanır.0->FFFFFFFFunavailable,
1->0available;80000000->7FFFFFFFavailable. Son anormal örnek normal
192slot helper'ının üretebileceği count değildir; caller instruction
semantiği raw gözlem için test edilmiştir, ulaşılabilir native count iddiası
değildir. Bound normal helper yalnız0..192üretir.

Başarılı bank yolunda+58gerekirse1yapılır,+4phase0planlanır; iki ayrı
bank string/UI span'ı ardından BMerchant route/string/cleanup span'ı gelir.
Detaylı route inputs/factory varsa BMerchant kind'i zorunludur. Ready import
ve complete alt model dış normal dönüşün yerine geçmez. Gap'te accepted
phase2,prospective phase0/yazımlar ayrı kalır; bu native rollback değildir.

## Sayaç ve veri kaynağı

`merchant_bank_count.py`,46ff6c'nin0..191inclusive döngüsünü modeller.
Her46fed8helper çağrısının normal dönüşü ve full EAX sonucu ayrı sağlanır.
Yalnız gözlenen0artırır; eksik value/return0sayılmaz ve prefix nihai count
değildir. Hiç erken çıkış veya192.slot çağrısı üretilmez.

Alt46fed8gövdesi de diskte kayıt altındadır: global553e80/+5540bc/+5540c0,
taze guarded DWORD okumaları,slot*4,nonzero pointer'da60/64alanları ve
base+remainder1000birleşimi içerir. Bu ayrıntılı memory/helper davranışı
yeni sayaç modeli tarafından uygulanmış sayılmaz. Kaynak guarded read
başarısızlığının0döndürmesi sayaca etki edebilir; zero-result sayımı gerçek
bankada boş slot bulunduğuna veya sağlıklı bellek okumaya eşdeğer değildir.

## Ortak rota API ve runner bağı

MerchantBankRouteInputs/factory artık SMerchant(default,eski uyum) veya
BMerchant kind'i taşır. BMerchant source filename global569908; SMerchant
5698bcdir. Bütün sonuç/error/gap planları doğru kind/global etiketini korur.
SELL caller BMerchant girdisini,BUY caller SMerchant girdisini ulaşılan bank
span'ında reddeder. Paylaşılan dosya importer/error/start bileşenleri native
byte kanıtı ortak caller içinde bulunduğu için yeniden kullanılır.

MerchantSnapshot.buy_failure_inputs isteğe bağlı API bağıdır. Reached BUY
setup_result1olduğunda legacy bank bool'u bypass olarak kullanamaz; yeni
planın tüm normal-return gereksinimleri uygulanır. Complete bank yolunda own
phase0/setup gate/restart ve yalnız BMerchant load_bank_route intent'i döner.
BUY UI parser/factory/RoutePage handoff bu aşamada **henüz bağlı değildir**;
mevcut SELL UI otomatik olarak BUY davranışı sayılmadı.

12yeni test192sınırı,zero/nonzero/prefix,ayrı helper return,signed alarm,
policy önceliği,DEC wrap,stop-before-notification,prospective state,
fresh inventory,bound count conflicts,BMerchant own dosya import ve runner
gate'lerini sınar. Kod kanıtı `outputs/FarmexBot_alis_basarisizlik_kod_kaniti.json`;
üretici `work/audit_buy_failure.py`. İki korunmuş sürümde960instruction
kaydı doğrulandı; slot helper kaydı bu sayıya dahil olsa da semantiği tamamlandı
sayılmaz. Ghidra/disk kanıtıdır,REA Evidence değildir. Native/helper/heap/VCL
ve canlı uyumluluk hâlâ doğrulanmadı.
