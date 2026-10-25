# Kaynak Delos Gate Open ve Delos Gate

18 Ekim 2026. `source_route_delos.py`, güncel004f276c içinde004f3102..004f350a
aralığını modeller. İlk üç Gate false olduğunda typed `delos` girdisiyle
aynı Gates→Commands→SourceStep→RouteProgress zincirine bağlanır. Daha önceki
komutlar eşleşmiş veya gap vermişse Delos tüketilmez. İki Delos karşılaştırması
da false ise typed `finish` girdisi Change Camp/NPC/unknown son dallarına
geçebilir; ayrıntı SOURCE_ROUTE_FINISH.md'dedir. Girdi yoksa gövde açık kalır.

## Delos Gate Open

Karşılaştırma/string-cleanup normal dönüşü ile saved AL ayrı gözlemlerdir.
5f4 nonzero dalı1000ms signed64 bekler; ayrı DWORD clock sıfırla genişletilip
5f8/5fc QWORD damga çıkarılır. Süre dolunca5f4,sonra5e8 temizlenir. Actor/NPC
girdileri bekleme yolunda okunmaz.

Başlangıçta553e7c/554020 guarded DWORD→BYTE actor zinciri vardır. AL nonzero
erken normal dönüştür; timestamp/started yazılmaz. AL0ise `[Teleport Gate]`
filter/lookup/stack cleanup span'ı ayrı normal dönüş ister. Raw selector EAX
DWORD'u ya da mevcut `select_npc` modelinin supplied typed candidate satırları
ve açık iterator-complete girdisi kullanılabilir. İkisi aynı anda verilemez.
Bound selector yalnız own satırlar üzerinde çalışır; süreç/NPC taramaz.

NPC ID0ise veya00464a10 pointer EAX0ise kaynak yine clock→5f8/5fc→5f4=1
yazar ve1000ms beklemeyi başlatır. ID unsigned karşılaştırılır; ffffffff
nonzero yoludur. Normal start, NPC bulunduğu veya gate açıldığı kanıtı değildir.

Pointer nonzero ise554008 ve554010 offset'leri taze okunur; adresDWORD'da
sarılır.0045ddb8/FSTP x/y normal dönüşleri ve iki captured local float bit
deseni ayrı girdilerdir. Float getter/protection/FPU internalleri burada
emüle edilmez. Aynı y/x local bitleri metric ve gerekirse hareket çağrısında
kullanılır; tekrar NPC/string okunmaz.

Metric9,0karşılaştırması sonrası `AH & 5` testi uygulanır. Greater/equal yolu
004646b4 normal dönüşüyle hareket planlar ve sonra beklemeyi başlatır.
Less/unordered yolu actor'ı **yeniden** okur. İlk clear actor sonucu bu
ikinci okuma yerine konmaz. İkinci AL nonzero ise normal erken dönüşte
started yazısı yoktur. AL0ise004c8f7c(00561ef8,cached NPC ID) normal dönüşü,
sonra ayrı clock gerekir. Gerçek NPC etkileşimi veya hareket yapılmaz.

## Delos Gate

Başlangıç actor kapısı aynı tiptedir. Ardından fresh index/parametre parse
normal dönüşü ve raw EAX gerekir.19bayt source template
`550010373030315f64756e6765756e2e6c7561` kullanılır; parametrenin yalnız düşük
BYTE'ı offset1'e yazılır. Memcpy1 normal dönüşü ayrıca istenir.004625ac x
ve004625d8 y EAX gözlemleri sırasıyla **global**56ffb8 ve56ffbc'ye yazılır.
Y eksikse bilinen x yazısı korunur, enqueue yapılmaz.

Mevcut own enqueue, length19/delay1000ile çalışır. Queue gate ve ulaşıldığında
queue clock, dış queue normal dönüşü ve sonraki **caller clock** ayrıdır.
Queue gate0ise kayıt oluşmaz ama açık normal dönüş/caller clock sonrası
started yine yazılabilir. Yerel kayıt, gönderim veya gate başarısı değildir.

Started dalı saved origin globallerini sırasıyla y56ffbc/x56ffb8 signed DWORD
olarak metric'e verir. Float10,0 karşılaştırmasında kaynak `TEST AH,41hex; JP`
kullanır. Maskenin parity biti greater **ve unordered** durumlarında clock
kontrolüne geçer; less/equal durumda clock'a uğramadan normal döner.
Model basit `distance > 10` karşılaştırmasıyla unordered yolunu kaybetmez.
Clock yolunda ayrıca3000ms signed64 süre dolmalıdır; sonra5f4/5e8 temizlenir.
AH gözlemi gerçek fiziksel yer değişimi veya başarı diye yorumlanmaz.

## Üst modeller ve own durum

Kaynak parent, alt komutun origin yazılarını object field'ı yerine own
`RouteStartState.globals` map'ine uygular. Object timestamp/started alanları
ayrı kalır. Eksik epilogue index'inde global yazılar yalnız prospective own
state'dedir; queue entry/accepted/prospective ayrımı önceki Gate adapter'ları
üzerinden korunur. Bu saf invocation denemesidir; native yan etkileri geri
alma veya emüle etme iddiası yoktur. Hiç process/bellek/FPU/helper eylemi
yürütülmez.

Genel RouteRunner'ın Delos Gate parametre parser'ı da actor geçilmeden veya
started bekleme dalındayken çağrılmaz. Kendi strict decimal format politikası
ulaşılan başlangıç dalında korunur. Genel finite-distance simülasyonu, raw
AH/FPU/native semantics'in tamamı sayılmaz. Raw API henüz rota ekranında
ayrı kontrollerle sunulmaz.

## Kanıt ve kontrol

`work/audit_source_route_delos.py`, eski/güncel hash'li dosyada **530 talimat
kaydını** disk baytlarıyla doğrular. İki literal ve filter,9/10float sabitleri,
NPC/pointer kısa devreleri, aynı float local push'ları, fresh actor, parity
JP dalı,19bayt template, origin global store'ları,1000queue delay ve
queue-sonrası caller clock/store sırası ayrı anchor'lardır. GetTickCount ve
CC32260MT._memcpy import kimlikleri de doğrulandı. Rapor:
`outputs/FarmexBot_rota_delos_dallari_kod_kaniti.json`.
Bu Ghidra/disk kanıtıdır; REA Evidence değildir. Önceki auditlerle örtüşen
kayıtlar benzersiz yeni kapsam veya tam fonksiyon sayısı değildir.

21 yeni test dahil ilgili181 test geçti. Tam Python kontrolünde **2174 test
geçti (11.585 saniye)**. ID0/pointer0, bound NPC lookup,
fresh interaction actor, address wrap,9eşitliği, unordered9/10dalları,
tam QWORD clock, düşük parameter BYTE, origin write-space,1000queue delay,
eksik getter/lookup/clock, prospective queue/global ve deferred parser sınandı.
NPC/helper/native layout, hareket/etkileşim, sonraki raw komutlar ve canlı
uyumluluk açık kalır.

Genel rota parser'ı değiştiği için tam gizli UI kontrolü de tekrar çalıştırıldı
ve geçti:1037kontrol,11form,18ana sekme ve mevcut alt motor senaryoları.
Kendi pencere withdraw kaldı; gerçek oyun incelenmedi/eylem yapılmadı. Yeni
raw Delos girişleri ayrı UI kontrolü olarak sunulmuş değildir. Native fixture
tekrarlanmadı.
