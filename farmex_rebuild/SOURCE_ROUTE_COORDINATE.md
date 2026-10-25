# Kaynak Koordinat satırı

18 Ekim 2026. `source_route_coordinate.py`, güncel004f276c içindeki ikinci
komut karşılaştırması004f28f9 ile Koordinat gövdesini modeller. İlk Town
karşılaştırmasının sonucu0ise `SourceRouteStepObservation.coordinate` üzerinden
aynı kaynak satır yürütücüsüne bağlanır. Town eşleşmişse bu girdi tüketilmez.
Koordinat da eşleşmezse parent'taki typed `commands` girdisiyle Bekle ve
Otur/Kalk dallarına geçilebilir; ayrıntı SOURCE_ROUTE_COMMANDS.md'dedir.
Girdi yoksa sonraki gövde açık kalır; tamamlanma veya processing temizliği
uydurulmaz.

## Komut ve hareket kapıları

004f28f9..004f2947 metin oluşturma/karşılaştırma/temizleme span'ının normal
dönüşü ve saklanan karşılaştırma AL değeri ayrı gözlemlerdir. Kaynak sonucu
PUSH EAX/POP EDX ile korur ve DL'yi test eder. Nonzero eşleşme ardından
global BYTE561f7e nonzero ise yordam taze index okuyup döner; processing'i
temizlemez. Root/koordinat parser'ı bu dalda çağrılmaz.

Aksi halde global553e7c→guarded DWORD root→taze offset554034→guarded DWORD
value zinciri vardır. Yalnız tam DWORD6 dönüşü bu erken dönüşü seçer.
Root null/failure0sonrasında offset ve ikinci getter atlanmaz; adres düşük32bitte
sarılır. Source guarded-reader provenance/eksik veri ayrımı korunur. Gerçek
VirtualProtect veya bellek okuması yapılmaz.

004f29a7..004f29da span'ında her eksen için index5ec yeniden okunur, string
yardımcısı çağrılır ve sonuç yerel float'a yazılır. Bu span için bağımsız
normal dönüş ve iki yerel32bit float bit deseni gerekir. Parser/locale,
FPU yuvarlaması veya doğru oyun koordinatı türetilmez. Bitler float'a çevrilip
yeniden paketlenmez; signed zero/NaN gibi ham desenler değiştirilmez.

Metric00460548 fiziksel olarak önce y, sonra x local float bitleriyle çağrılır.
Kaynak float2,0 ile FUCOMPP sonrasında `AH & 45hex` testini yapar. AH ayrı
gözlemdir; model metric formülünü veya FPU exception'larını emüle etmez.
Less/equal/unordered testinde yalnız object BYTE5e8=0 yazılır. Bu kaynak
kararı, gerçek hedefe varış veya oyun eylemi başarısı diye adlandırılmaz.
Greater sonucunda004646b4 hareket yardımcısının ayrı normal dönüşü gerekir;
processing açık kalır. Hiçbir gerçek hareket çağrısı yürütülmez.

Önemli caller farkı: metric ve movement **aynı yakalanmış yerel x/y float
bitlerini** kullanır. Arada index/string/koordinat tekrar okunmaz. Bu davranış,
global koordinatları hareket için yeniden okuyan `route_motion.py` ile
karıştırılmaz. Her erken/normal yolun source parent'ı index5ec'yi taze okur;
bu dönüş eksikse daha önceki processing clear yazısı yalnız prospective
state'de kalır. Clear dışındaki timestamp/started alanları kendiliğinden
sıfırlanmaz. Opaque yardımcıların diğer yan etkileri açık kalır.

## Bağ ve kontrol

Tam kaynak satır planı mevcut `RouteProgressObservation.step_execution`
tarafından tüketilir. Hareket yardımcısı normal dönse de caller'ın taze5e8
değeri1ise pazar çıkışına geçilmez. EAX index veya helper dönüşü ACK sayılmaz.
Girdiler own fixture veya bağımsız gözlemlerdir; native object identity,
oyun belleği ve gerçek hareket bu API ile doğrulanmaz. Genel RouteRunner ve
UI değiştirilmedi; yeni raw API henüz rota ekranına bağlı değildir.

`work/audit_source_route_coordinate.py`, iki hash'li dosyada **156 talimat
kaydını** disk baytlarıyla doğrular. Koordinat literali, ikinci karşılaştırma,
lock/guarded zincir, iki taze index, iki FSTP local'i, aynı local push'larının
tekrarı, AH dalları ve processing clear ayrıca anchor'lardır. Float sabiti
`00000040`=2,0iki sürümde doğrulandı. Rapor:
`outputs/FarmexBot_rota_koordinat_satiri_kod_kaniti.json`.
Bu Ghidra/disk kanıtıdır; REA Evidence değildir. Kayıtlar tam fonksiyon
tamamlanması veya diğer auditlere göre benzersiz kapsam sayısı değildir.

16 yeni test dahil ilgili91 test geçti. Tam Python kontrolünde **2115 test
geçti (6.914 saniye)**. Eşleşme/cleanup ayrımı, erken
nonzero kilit, tam DWORD6, null/failure/wrap zinciri, parser/local/metric
gap'leri, less/equal/unordered, aynı float local'lerinin korunması, move
dönüşü, processing caller kapısı ve taze index eksikleri sınandı.
Diğer satır gövdeleri, yardımcı etkileri ve canlı uyumluluk açık kalır.
UI/native kaynak değişmedi; bu aşamada UI smoke/native fixture tekrarlanmadı.
