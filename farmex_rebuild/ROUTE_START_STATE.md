# Rota başlatma yardımcısının durum yazıları

Sonraki dış kapı bağı: Kendi start state'inin561f6creset0değeri explicit
post-enable gözlemi olarak [MERCHANT_CALLBACK.md](MERCHANT_CALLBACK.md) adapter'ına
verildiğinde pazar phase tick'i bastırılır. Otomatik native global bağlantısı değildir.

18 Ekim 2026: `route_start_state.py`, güncel `004ead88` / eski `004ead6c`
yardımcısının normal yolunu kendi immutable mapping state'i üzerinde modeller.
Oyun belleği, işlem veya hareket API'sine erişmez. Eksik yardımcı dönüşleri ve
saat/sayaç değerleri dışarıdan verilen gözlemlerdir; başarısızlık/fault emüle edilmez.

Sıra: `004ca4c4(561ef8,0)` için normal dönüş → dört doğrudan global reset →
`00464714` normal dönüş → 38 object-field reset → GetTickCount → sıfır genişletilmiş
saatin +5e0/+5e4 alanlarına iki DWORD yazısı → taze DWORD count+88 okuması →
count'un +5f0 alanına yazılması → BYTE +5d9=1. Bu modelde son byte aktif işaretidir;
gerçek rota/hareket başladığının kanıtı değildir.

Global561f6c/56204c byte0,56203c/562040 DWORD0 doğrudan kaynak yazılarıdır.
Object resetleri kaynakta görülen BYTE/DWORD genişlikleriyle saklanır. Özellikle
+618=14, +654=13, +5ec/+690=ffffffff korunur; generic sıfır-reset ile değiştirilmez.
Saat öncesi +5e0/+5e4 zaten0yazılır, sonra taze saatle yeniden yazılır. +5f0 da
önce0, en sonda taze count değeri olur. Order-sensitive write listesi iki yazıyı
ayrı kaydeder. Bu global'ların dış callback gate etkileri henüz otomatik bağlanmaz.

`RouteStartFrame` bilinen tick/count'u aynı invocation'da değiştirmez, tamamlanan
helper prefix'lerini ve resetleri sonraki gap'te tekrarlamaz. Accepted state entry'de
kalır; prospective mapping ön yazıları gösterir. Complete frame idempotent'tir.
Kaynağın kendi eski count alanı yeni okuma yerine kullanılmaz. Fresh count0bile
helper sonunda +5d9=1 üretebilir; kaynakta olmayan positive-count guard eklenmez.

Mapping'de doğrudan yazılmayan kendi alanlar korunur; bu, opaque helper'ların gerçek
bellekte başka alan değiştirmediği anlamına gelmez. Bütün process/global state veya
CPU-register emülasyonu değildir. Source helper'ın normal return'üne ulaşan kendi
planı, native helper'ın gerçekten döndüğünü kanıtlamaz.

## SMerchant import bağı

`MerchantBankRouteInputs.start_execution`, bu typed kararı isteğe bağlı bağlar.
Başarı dosyası hazır olduktan sonra önce ayrı `prestart_span_returned` gerekir:
004ecd9e..004eced3 içindeki ilk query, çoklu string/array copy, classifier ve
544/548 sonucu yazıları opaque span'dır. Bu yardımcıların anlamları veya sonuçları
uygulanmaz. Sonra entry count+88 yerel imported count'la eşleşmelidir; eksik frame
bitmiş sayılmaz. Son fresh count farklıysa concurrency bridge açık gap kalır.
Standalone starter bu değişimi planlayabilir; yerel imported dataset ile otomatik
eşitlemez. `ready=True` import'u, `complete=False` henüz tamamlanmamış start bağını
aynı kararda gösterebilir.

Tam start modeli olsa bile parent SELL failure'ın dış route/string/helper dönüşü
ayrıca gerekir. Bound start eksikliği opaque dönüş örneğiyle atlanamaz. Start modeli
verilmezse önceki açık opaque helper yolu ayrı devam eder; onun native init alanları
doğrulanmış sayılmaz. Workbench için yeni start gözlem kontrolleri yoktur.

## Kanıt ve test

`work/audit_route_start_state.py`, iki sabit hash'li dosyada **198 talimat kaydını**
baytlarıyla doğrular. Saatten önceki store'lar basit register/constant takibiyle
assembly'den bağımsız çıkarılır; 42global/object reset yazısı model listesiyle
sıra/genişlik/değer bazında eşleşir. Helper callsite'ları, GetTickCount import
kimliği, zero-extension, fresh count ve final active yazısı ayrı kontrol edilir.
Rapor `outputs/FarmexBot_rota_baslatma_durum_kod_kaniti.json`.
Ghidra/disk statik kanıtıdır; REA Evidence veya native yürütme değildir. Diğer
auditlerde örtüşen kayıtlar benzersiz toplam veya tam-fonksiyon sertifikası sayılmaz.

8 yeni test dahil **2015 yerel test geçti** (7.066 saniye). İki helper gate'i,
partial reset/saat/sayaç, tekrarsız prefix, immutable state, farklı taze count,
Count0davranışı ve kendi geçici dosyasıyla typed import bağı sınandı. UI değişmedi;
UI smoke tekrarlanmadı. Native route state, dış callback gate'leri, yardımcı iç
etkileri ve canlı uyumluluk açık kalır.
