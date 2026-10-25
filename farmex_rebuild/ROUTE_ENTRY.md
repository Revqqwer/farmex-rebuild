# Rota girişi, sorgu zamanları ve Enemy geçişi

Güncelleme: `query_execution` artık [ROUTE_QUERY.md](ROUTE_QUERY.md) içindeki
typed 0046cfcc planını bağlayabilir. Eksik bound planın kısmi çıktıları
kullanılmaz; tam plan için de ayrı normal dönüş receipt'i gerekir. Ham
output override ile karıştırma ve bilinen parametre uyuşmazlığı reddedilir.
Aşağıdaki ilk aşama açıklamalarındaki query iç boşluğu bu sınırlı normal
caller modeliyle daraltıldı; isim helper/runtime/canlı etkiler hâlâ açıktır.

18 Ekim 2026. `route_entry.py`, güncel004eb2c4/eski004eb2a8 başlangıcını
mevcut `route_progress.py` zincirine bağlar. Böylece o zincire004eb3ef'de
ulaşılmış olduğu varsayımı bu adapter için entry koşullarıyla değiştirildi.
Bu, query/reload/helper iç etkilerini veya native fonksiyonun tamamını
çözdüğümüz anlamına gelmez. Girdiler taze source read ve helper gözlemleridir;
hiç process/bellek/oyun çağrısı yapılmaz.

## Local baytlar ve sorgu kapısı

Her invocation local-31/-32/-33 BYTE'larını0başlatır. Önceki query çıktıları
otomatik taşınmaz. İlk global569100BYTE nonzero/569108DWORD0yolu eligible ise
Enemy pre-check atlanır; aksi halde569120/569130BYTE çiftinin nonzero olması
gerekir. Kaynaktaki kısa devreler ve field genişlikleri korunur.

Eligible ise ilk ayrı GetTickCount DWORD sıfırla genişletilir, object
5e0/5e4 tam QWORD başlangıç damgası çıkarılır. Signed64 fark **en az10000**
olmalıdır. Sonraki ayrı clock'tan global56ff8c/56ff90 QWORD sorgu damgası
çıkarılır; burada fark **1000'den büyük** olmalıdır.1000eşitliği query yapmaz.
DWORD düşük parçaya indirgeme veya aynı clock örneğini tekrar kullanma yoktur.

Query çağrısının fiziksel push sırası local-33ref,local-32ref,taze global
569124DWORD,local-31ref,taze global569104DWORD,5690f8object'tir.0046cfcc
normal dönüşü ayrı receipt'tir; helper'ın kendi dönüş değeri veya3output
baytıyla aynı şey değildir. Model call'a ulaştığında output'ları bilinmiyor
yapar; unconfirmed return eski0değerlerini koruyormuş gibi gösterilmez.
Normal dönüşte explicit optional3BYTE örnekler alınır. Sonraki **üçüncü**
clock sorgu stamp low'una,0high'a yazılır.

Output eksikliği gerektiği yerde durdurur: local-32 Enemy kontrolünde,
local-31 ilerleme içindeki AntiCR koşulunda kullanılır. Local-33'ün caller'da
init/ref verilmesi dışında doğrudan okuması yoktur; unknown kullanılmamış
output, counter yolunun tamamlanmasını gereksiz durdurmaz. Bu, helper'ın
output ve diğer yan etkilerinin tamamının bilindiği anlamına gelmez.

## Taze Enemy kontrolü ve ilerleme bağı

Kaynak569120/569130BYTE'larını query eligibility okumalarından **sonra yeniden**
okur. İkisi nonzero ve local-32nonzero ise004eb3a6..004eb3dd `Enemy` route
reload/string cleanup span'ının normal dönüşü ayrıca gerekir; ardından
doğrudan dönülür. Önceki flag'ler bu taze okumaları doldurmaz. Query yapılmamış
invocation'da local-32başlangıç0olduğu için stale output'tan reload doğmaz.

Diğer yol004eb3ef progress modeline gider. Local-31bu modelin
`anti_result_byte` girdisinin producer'ıdır; aynı alana raw override verilemez.
Query yoksa0,query output unknown iseNoneaktarılır. Progress kendi sonraki
global/field/helper/clock örneklerini ayrı ister. Eksik progress'te bilinen
entry timestamp yazıları trace'de kalır; accepted/prospective active-enable
ve queue ayrımı alt modellerden taşınır. Enemy erken dönüşünde unvisited
progress veya supplied alt queue çıktıları gösterilmez.

Entry `.state` yalnız kendi modellenmiş direct active/enable projeksiyonudur.
Query veya Enemy reload helper'ı gerçek native alanları değiştirmemiş diye
yorumlanmaz; o etkiler açık kalır. Pointer escape,concurrency,exception ve
normal epilogue'un tüm runtime etkileri emüle edilmez. Saf own trial
prospective ayrımı native rollback veya gerçek helper yürütmesi değildir.

## Merchant callback bağı

`MerchantCallbackObservation.route_execution` optional typed entry kararını
kabul eder. Route pending nonzero ve bound karar eksikse raw helper-return
true olsa bile own callback ilerlemez. Bound karar complete ise de **ayrı
`route_helper_returned=True` receipt'i hâlâ gerekir**. Sonraki master/enable
global okumaları ve mode okumaları da bağımsız tazedir; entry çıktısından
doldurulmaz. Bu model complete'ini gerçek native helper dönüşü diye saymayı
engeller. Route pending0veya daha erken skip'te unvisited bound karar
çıktıya taşınmaz; lazy merchant snapshot factory çağrılmaz.

Bu ek completeness gate'i own adapter giriş politikasıdır; orijinal callback'e
fazladan native branch eklendiği iddiası değildir. Legacy raw callback API'si
bound karar verilmediğinde aynı kalır. Native execution/live verified alanları
false kalır. Bu raw entry yolu henüz rota UI'sinde ayrı kontrollerle sunulmaz.

## Kanıt ve kontrol

`work/audit_route_entry.py`, iki hash'li sürümde **160 talimat kaydını** disk
baytlarıyla doğrular. Local init/ref/use sayıları,flag genişlikleri,10000
inclusive ve1000strict dalları,üç clock,query push sırası,taze Enemy okumaları,
Enemy literali/reload veGetTickCount importu kontrol edildi. Her sürümde
local31/32/33doğrudan referans sayıları3/3/2'dir. Rapor:
`outputs/FarmexBot_rota_giris_sorgu_enemy_kod_kaniti.json`.
Bu Ghidra/disk kanıtıdır; REA Evidence değildir. Helper gövdeleri ve önceki
auditlere göre benzersiz kapsam/tam fonksiyon tamamlanması kanıtlanmaz.

20 yeni test dahil entry/callback/progress/motion için67 ilgili test geçti.
9999/10000,1000/1001,QWORD high,ayrı update clock,query gap/output,None33,
taze Enemy reload,local31producer,stale output engeli,bound callback skip/gap,
ayrı helper return/post-globals veprospective queue sınandı. Tam Python
kontrolünde **2235 test geçti (9.880 saniye)**. UI/native kaynak değişmedi;
bu aşamada UI smoke/native fixture tekrarlanmadı. Query/helper/reload
iç etkileri, gerçek native bağlantı ve canlı uyumluluk açık kalır.
