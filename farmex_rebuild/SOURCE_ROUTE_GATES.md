# Kaynak Gate Skill, Gate Open ve Gate dalları

18 Ekim 2026. `source_route_gates.py`, güncel004f276c içindeki004f2d31..004f30fd
aralığını modeller. Bekle/Otur/Kalk false sonucundan sonra typed `gates`
girdisiyle `source_route_commands`→`source_route_step`→`route_progress`
zincirine bağlanır. Üç karşılaştırma kendi sırasında yapılır; önceki eşleşince
sonraki tüketilmez. Hepsi false ise typed `delos` girdisiyle Delos dallarına
geçilebilir; ayrıntı SOURCE_ROUTE_DELOS.md'dedir. Girdi yoksa devamındaki raw
gövde açık bırakılır; processing temizliği veya normal dönüş uydurulmaz.

## Düzeltilen genel davranış

İki ikilide de literal, branch ve template aynı eşlemeyi gösteriyor:

| Komut | Başlangıç yolu | Bekleme |
|---|---|---:|
| Gate Skill |004c8d84(00561ef8), parametre parse edilmez|3000ms|
| Gate Open |33 + parameter DWORD little-endian,5bayt local enqueue/delay0|1500ms|
| Gate |4b + parameter DWORD little-endian,5bayt local enqueue/delay0|3000ms|

Önceki genel `special_routes.py` modelinde Gate Skill ile Gate'in başlangıç
yolları ve Gate Skill/Gate Open süreleri yanlış eşlenmişti; Gate Open da
yanlış4bşablonunu kullanıyordu. Model ve testler bu kaynak eşlemesine göre
düzeltildi. Bu, sürümler arasında davranış değişikliği iddiası değildir;
önceki yerel uygulamanın düzeltmesidir.

`routes.py` genel adapter'ı Gate Skill için sayısal parametre istemez, Gate
için ister. Gate Open/Gate bekleme dalında veya actor gate henüz geçilmemişken
metni parse etmez. Geçilmiş başlangıç dalında kendi route formatının strict
decimal signed32 kuralı korunur; native parser/locale bire bir emüle edilmez.
Delos/ChangeCamp genel adapter politikası bu adımda yeniden yazılmadı.

## Raw kaynak akışı

Karşılaştırma/string cleanup normal dönüşü ve saved AL ayrı gözlemlerdir.
BYTE5f4 nonzero ise ayrı caller GetTickCount DWORD sıfırla genişletilir,
5f8/5fc tam QWORD damga çıkarılır. Signed64 fark tabloda belirtilen süreye
ulaşınca önce5f4,sonra5e8 sıfırlanır. Wait dönüşü yeni actor, parametre,
memcpy veya queue verisi istemez. Ortak source epilogue index'i taze okur.

Başlangıç dalında guarded root/554020-offset/BYTE zinciri kullanılır. AL
nonzero ise normal erken dönüş, hiç queue veya stamp yazısı yoktur. Helper
null/failure/eksik gözlem ayrımı korunur; gerçek bellek/protection API'si
çağrılmaz. Gate Skill için004c8d84 normal dönüşünden sonra ayrı caller clock
ve5f8/5fc/5f4 yazıları gelir. Helper'ın gerçek oyun etkisi açık kalır.

Gate Open/Gate, taze index/parametre parser span'ı için normal dönüş ve EAX
DWORD'u ister. Template beş bayttır; parametre offset1'e dört bayt yazılır.
Memcopy normal dönüşü ayrı gözlemdir. `enqueue` mevcut kendi QueueState'ini
kullanır; length5,delay0,bağımsız queue gate ve ulaşıldığında ayrı queue clock
gerekir. Enqueue modeli normal tamamlansa bile dış004c7710 normal dönüşü
ayrıca istenir. Sonraki **caller clock**, queue timestamp'iyle doldurulmaz.
Caller timestamp low/zero-high ve started yazıları ancak bundan sonra gelir.

Gate0bağlantısında queue kaydı eklenmez; normal dönüş ve caller clock
verilmişse source started1yine yazılır. Bu yüzden started1veya normal helper
dönüşü gönderim, başarılı gate veya sunucu ACK'si değildir.

## Queue sahipliği ve eksik planlar

Plan saf bir yerel invocation denemesidir. Tamamlanmayınca kabul edilen
queue girişte kalır, bilinen local enqueue `prospective_queue` içinde
görünür. Sonradan caller clock girdisi eklenerek **aynı giriş QueueState'i**
üzerinden yeniden denenir; prospective queue yeni invocation girişi olarak
uygulanmaz. Bu tasarım native eylemleri geri almayı veya tekrar yürütmeyi
iddia etmez; hiç native eylem yapılmaz.

Queue entry/accepted/prospective ayrımı source parent'a ve route_progress
caller'ına taşındı. Parent epilogue index'i veya caller'ın taze count/processing
örneği eksikse üst plan queue'yu kabul etmez. Step helper'a daha ulaşılmadan
gap varsa supplied alt queue planı hiç sunulmaz. Tam source planıyla caller
processing1dalında dönse de local queue kaydı korunur; pazar çıkışına geçilmez.
Queue drain/native transport/ACK bu çalışmada yoktur.

## Kanıt ve kontrol

`work/audit_source_route_gates.py`, iki hash'li dosyada **510 talimat kaydını**
disk baytlarıyla doğrular. Üç literal ile ad/threshold/başlangıç eşlemesi,
actor dalları, parameter parse/memcpy/length5/delay0queue çağrıları ve queue
sonrası caller clock/store sırası ayrı anchor'lardır. İki5bayt template
`3300000000` ve `4b00000000`, GetTickCount ve CC32260MT._memcpy import
kimlikleri doğrulandı. Rapor: `outputs/FarmexBot_rota_gate_dallari_kod_kaniti.json`.
Bu Ghidra/disk kanıtıdır; REA Evidence değildir. Audit kayıtları tam fonksiyon
tamamlanması veya önceki auditlere göre benzersiz kapsam sayısı değildir.

17 yeni raw/queue testi ve3 yeni genel RouteRunner entegrasyon testi eklendi.
Tam Python kontrolünde **2153 test geçti (10.493 saniye)**; son Gate/genel
hedefli kontrolde51 test ayrıca geçti. Tam gizli UI kontrolü de1037kontrol,
11form,18ana sekme ve mevcut alt motor senaryolarında geçti; pencere
withdraw kaldı. UI kontrolü bu raw API'nin canlı veya arayüze bağlı olduğu
iddiası değildir; genel rota davranışı ve mevcut uygulama için regresyon
kontrolüdür. Native fixture tekrarlanmadı.
Kaynak ad/süre/payload eşlemesi, tam QWORD,actor short-circuit,eksik
parser/copy/queue-return/clock, gate0, ayrı iki saat, prospective kuyruk,
parent/caller gap'leri ve deferred parametre parse sınandı. Gerçek gate/skill
eylemi, helper/allocator etkileri, sonraki raw gövdeler ve canlı uyumluluk açık.
