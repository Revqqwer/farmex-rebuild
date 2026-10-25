# Kaynak Change Camp, NPC ve son eşleşmeyen komut

18 Ekim 2026. `source_route_finish.py`, güncel004f276c içinde004f350f..004f37be
aralığını modeller. İlk Delos karşılaştırmaları da false olduğunda typed
`finish` girdisiyle aynı Delos→Gates→Commands→SourceStep→RouteProgress
zincirine bağlanır. Böylece adı bilinen rota komutlarının ve son eşleşmeyen
komutun normal **çağıran** dalları tek raw zincirde temsil edilir. String
karşılaştırması, indeks/parametre erişimi, helper gövdeleri, exception yolları
ve native etkilerin tümü çözülmüş sayılmaz; tam fonksiyon sertifikası yoktur.

## Change Camp

Karşılaştırma/string-cleanup normal dönüşü ve saved AL ayrıdır.5f4 nonzero
ise2000ms signed64 beklenir: caller GetTickCount DWORD sıfırla genişletilip
5f8/5fc tam QWORD damga çıkarılır. Süre dolunca önce5f4,sonra5e8 temizlenir.
Bekleme yolunda health veya parametre helper'ı istenmez.

İlk dalda00464714 normal dönüşü,max HP004611c0 EAX ve HP004611a0 EAX ayrı
gözlemlerdir. Eşik maxHP*50 düşük32bit signed ürününün100'e sıfıra doğru
bölümüdür. HP signed karşılaştırılır. Eşikten küçükse normal döner;
Randomize karşılaştırması/parser/action/clock yapılmaz. Eşitlik devam eder.
Town ile aynı aritmetik korunur; sonsuz hassasiyetli Python çarpımı veya
floor division kaynak işlemin yerine kullanılmaz.

Parametre224'ün `Randomize` ile taze karşılaştırması ve cleanup normal dönüşü
ayrıca gerekir. Saved AL nonzero ise004c8a98(00561ef8) normal dönüşü istenir.
False ise ayrı fresh-index/0045ef80(parametre,default0) parse normal dönüşü
ve EAX gerekir. Sonuç0ise eylem helper'ı atlanır; nonzero ise
004c8698(00561ef8,number) normal dönüşü gerekir. Her iki normal yol ayrı
caller clock→5f8/5fc→5f4=1ile biter. Kaynağın native parser grameri veya
random helper etkileri bu çalışmada emüle edilmez.

Genel RouteRunner'ın Change Camp strict-decimal parser'ı da health eksik/düşük
olduğunda veya started beklemesinde çalışmaz. Health eşiği genel model ve
adapter arasında ortak fonksiyondur. Ulaşılmış numeric başlangıç dalında
kendi route formatının strict-decimal politikası korunur; native0045ef80'in
bütün kabul/fallback grameriyle eşdeğer olduğu iddia edilmez.

## NPC

İlk5f4=0dalında source actor553e7c/554020/guarded BYTE kontrolü yapılır.
Nonzero AL erken normal döner. AL0ise caller clock→5f8/5fc→5f4=1,
en son object DWORD600=1 yazılır. NPC alt motoru aynı çağrıda çalıştırılmaz;
parametre metni de bu dalda kopyalanmaz.

Started dalında004f370c..004f3730 fresh-index/Unicode parameter224→608
assignment span'ı için normal dönüş gerekir. Sonra004f11bc helper AL sonucu
test edilir.0normal **pending** dönüşüdür: bekleme süresi veya actor tekrar
okunmaz ve satır flag'leri temizlenmez. Nonzero ise5f4/5e8 sırasıyla0yazılır.
Normal helper dönüşü ile görevin tamamlanması ayrı tutulur; server/NPC ACK
çıkarılmaz.

Raw AL yerine mevcut typed `NpcRouteObservation` bağlanabilir. Bu durumda
kopyalanan Unicode parametre açıkça verilmelidir. Kendi giriş NPC frame'i
immutable korunur;608text'i yeni parametreyle değiştirilen ayrı frame üzerinde
mevcut alt motor çağrılır. Raw AL ve bound helper aynı anda kabul edilmez.
`needs_observation` sonucu üst caller'ı durdurur. Pending local sonuç normal
false, `returned_true` ise nonzero caller sonucuna dönüşür.

Alt motorun `npc_result.frame` çıktısı sonraki invocation için taşınmalıdır;
helper'ın phase/diğer field/global/text durumları bu nested frame'de kalır.
Kaynak parent'ın `RouteStartState` map'i yalnız kendi doğrudan yazılarının
projeksiyonudur; helper'ın bütün yazılarıymış gibi güncellenmez. Nested packet
ve cache niyetleri de mevcut NPC result içinde kalır; bu caller onları
kendiliğinden gerçek queue/transport işlemi diye yürütmez. Bu ayrım tam NPC
uyumluluğunun kanıtlanmış olmadığı sınırdır.

## Son eşleşmeyen komut

Change Camp ve NPC karşılaştırmaları da açıkça false ise kaynak yalnız
BYTE5e8=0yazar ve taze index epilogue'una geçer.5f4 veya timestamp temizliği
yoktur. Önceki genel `special_routes.py` unknown yolu5f4 karşılığı started'ı
da temizliyordu; yalnız processing'i temizleyecek şekilde düzeltildi. Bu
davranış bilinmeyen string'in helper çağrısı yapılmadan varsayılması değildir:
raw zincirde bütün önceki karşılaştırma gözlemleri gerekir.

## Kanıt ve kontrol

`work/audit_source_route_finish.py`, iki hash'li dosyada **388 talimat kaydını**
disk baytlarıyla doğrular. Caller health/Randomize/default0parse/helper/clock,
NPC Unicode608copy/AL/600start/final unknown store ve üç literal ayrı
anchor'lardır. Ayrıca NPC callee'nin phase600 girişini,text608 erişimini,
phase10→11/AL1ve diğer durumda EAX0 çıkışını doğrulayan yedi bridge kaydı
her sürümde kontrol edildi. NPC helper'ının tamamı bu scope'a dahil değildir.
Rapor: `outputs/FarmexBot_rota_son_komutlar_kod_kaniti.json`.
Bu Ghidra/disk kanıtıdır; REA Evidence veya tam fonksiyon/canlı sertifikası
değildir. Önceki auditlerle örtüşen kayıtlar benzersiz yeni kapsam sayılmaz.

18 yeni test dahil ilgili227 test geçti. Tam Python kontrolünde **2192 test
geçti (11.099 saniye)**. Health/signed overflow,Randomize,
numeric0/nonzero,2000ms/QWORD,actor,phase1start sırası,copy/AL/bound-helper
çatışması,pending/gap/complete ayrımı,immutable text608 ve unknown started
koruması,source parent/taze index ve deferred generic parse sınandı.
Gerçek Camp/NPC/helper/transport etkileri ve canlı uyumluluk açık kalır.

Genel parser/unknown davranışı değiştiği için tam gizli UI kontrolü de tekrar
çalıştırılıp geçti:1037kontrol,11form,18ana sekme ve mevcut alt motor
senaryoları. Pencere withdraw kaldı. Raw son-komut API'si ayrı UI kontrolleriyle
sunulmaz; NPC sonucu/server/oyun eylemi bu kontrolle doğrulanmış değildir.
Native fixture tekrarlanmadı.
