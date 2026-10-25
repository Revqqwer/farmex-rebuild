# Kaynak satır başlatıcısı ve Town dalı

Sonraki ek: Town karşılaştırması false olduğunda typed Koordinat girdisiyle
ikinci dal artık aynı source API'sinde çalışır. Ayrıntı: SOURCE_ROUTE_COORDINATE.md.
Koordinat da false olduğunda typed `commands` girdisi Bekle ve Otur/Kalk
dallarını ekler; ayrıntı: SOURCE_ROUTE_COMMANDS.md.
Bu grup da false olduğunda typed `gates` girdisi Gate Skill/Open/Gate
dallarını ve local queue'yu ekler; ayrıntı: SOURCE_ROUTE_GATES.md.
Gate grubu da false olduğunda typed `delos` girdisi Delos Open/Gate ve origin
global/queue zincirini ekler; ayrıntı: SOURCE_ROUTE_DELOS.md.
Delos grubu da false olduğunda typed `finish`, Change Camp/NPC/son unknown
kontrollerini ve NPC alt motor bağını ekler; ayrıntı: SOURCE_ROUTE_FINISH.md.
Bu dosyadaki2099test sonucu önceki Town aşamasına aittir.

18 Ekim 2026. `source_route_step.py`, güncel004f276c/eski004f2750 yordamının
cursor prologue'u, ilk Town dalı ve taze index dönüşünü modeller. Diğer
komutların eski `special_routes.py` modelleri vardır; bu adım onların bütün
native caller/body yollarını yeni API'ye bağlamış sayılmaz. Genel RouteRunner
simülasyonu değiştirilmedi; yeni kaynak API'si henüz rota ekranında yoktur.

## Cursor ve dönen değer

Object BYTE5e8 sıfırsa taze count5f0'dan düşük32bitte1 çıkarılır, ayrı index5ec
ile karşılaştırılır. Eşitse yordam index'i tekrar okuyup döner. Count0için
ffffffff sınırı korunur; positive-count kuralı eklenmez. Eşit değilse INC'in
memory okuması için index yeniden örneklenir. Index+1,5e8=1,5f4=0,5f8=0,5fc=0
yazılır; ortak epilogue index'i tekrar okuyup döner. Aynı çağrıda komut gövdesi
başlatılmaz. Dönüş index'i bir işlem veya sunucu ACK'si değildir.

Girdiler `(offset,bit width,value)` biçiminde bağımsız sıralı okumalardır.
Own giriş map'i eksik taze okumaları kendiliğinden doldurmaz. Source native
concurrency modelini emüle etmeden farklı index okumaları korunur. Çıktı
state'i yalnız bilinen doğrudan yazıların kendi map üzerindeki projeksiyonudur;
fresh-read değeri veya opaque helper'ın bütün yan etkileri map'e mal edilmez.

## İlk Town karşılaştırması

5e8 nonzero ise004f27f9..004f2846 metin oluşturma/karşılaştırma/temizleme
span'ı için normal dönüş, saklanan EAX'in düşük byte'ı için ayrıca gözlem
gerekir. Kaynak PUSH EAX/POP ECX sonrası CL'yi test eder. Nonzero ilk Town
dalına girer. Zero durumunda kaynak diğer komutlara devam eder; typed
Koordinat girdisi yoksa API `needs_command_body` ile durur. Varsa ikinci
Koordinat dalını modeller; sonraki bilinmeyen komutu tamamlandı diye döndürmez.

Town için taze BYTE5f4 nonzero ise ayrı GetTickCount DWORD sıfırla genişletilir,
object5f8/5fc tam QWORD damga çıkarılır. Signed64 fark2000'e ulaşınca önce
5f4=0, sonra5e8=0 yazılır. Her iki wait/clear yolu index'i epilogue'da taze
okuyup normal dönebilir. Wait dönüşü satırın bitmiş olduğu anlamına gelmez;
dış caller ayrıca kendi taze5e8 okumasını yapar.

5f4 sıfırsa00464714 normal dönüşü ayrıca gerekir. MaxHP004611c0 EAX DWORD'u
50ile düşük32bitte çarpılır; signed32 ürün100'e IDIV ile sıfıra doğru bölünür.
HP004611a0 ayrı EAX gözlemidir ve signed karşılaştırılır. Python'un sınırsız
çarpımı veya floor division'ı bu işlemin yerine kullanılmaz. HP eşikten küçükse
Town çağrısı/saat/yazı yapılmaz, taze index döner. Eşitlik Town'a izin verir.

004c8604(00561ef8) normal dönüşü bağımsız gözlemdir. Sonraki ayrı clock5f8'e,
0ise5fc'ye yazılır; en son5f4=1 yazılır, taze index döner. Hiç gerçek Town,
paket, hook veya oyun çağrısı yapılmaz. Normal dönüş gözlemi helper'ın eylem
sonucunu veya native yan etkilerinin çözüldüğünü kanıtlamaz.

## İlerleme caller'ına bağ

`RouteProgressObservation.step_execution` typed kaynak planını alabilir.
Bu dal erişildiğinde ham `step_return_dword` ile birlikte kullanılması hatadır;
eksik plan legacy ham dönüşle bypass edilmez. Bilinen alt yazılar trace'de
korunur. Tam alt plandan yalnız helper EAX alınır; caller'ın count5f0 ve
processing5e8 okumaları **ayrı taze örneklerdir**. Böylece cursor_armed sonucu
count-1'e eşit olsa da processing1pazar çıkışına erken geçmeyi engeller.
Bound plan ve caller aynı own route object'e ait olma sözleşmesini kullanır;
native object kimliği/helper yan etkileri bu API tarafından gözlenmez.

Yerel bütünleşme testi RouteStart→cursor_armed→Town start→2000ms clear→
RouteProgress→mode reread→common tail→ayrı callback post-enable/helper dönüşü→
SELLphase1 zincirini kullanır. Bütün saatler, getter'lar, metin karşılaştırması,
helper dönüşleri ve callback örnekleri own fixture'dır; gerçek Town veya
canlı oyun uyumluluğu değildir.

## Kanıt ve kontrol

`work/audit_source_route_step.py`, eski/güncel hash'li dosyada **220 talimat
kaydının** baytlarını, cursor reset/store sırasını, CL testi, health IDIV,
2000ms signed clock dallarını, Town literali ve GetTickCount importunu doğrular.
Rapor: `outputs/FarmexBot_rota_satir_town_kod_kaniti.json`. Diğer auditlerle
örtüşen kayıtlar benzersiz kapsam veya tam fonksiyon sayısı değildir. Bu
Ghidra/disk kanıtıdır; REA Evidence değildir.

15 yeni test dahil ilgili75 test geçti. Tam Python kontrolünde **2099 test
geçti (6.905 saniye)**. Cursor wrap/taze index/eksik return,
metin/health/helper gap'leri, düşük32bit ürün/signed truncation,2000ms sınırı,
tam QWORD stamp, bound plan çatışması ve processing caller kapısı sınandı.
UI/native kaynak değişmedi; bu aşamada UI smoke/native fixture tekrarlanmadı.
Diğer komut gövdeleri, native helper etkileri, entry/reload kapsamları ve canlı
uyumluluk açık kalır.
