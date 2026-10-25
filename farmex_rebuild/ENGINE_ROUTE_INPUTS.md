# Panel rota adlarının motor tüketicilerine aktarımı

Güncelleme: Factory artık varsayılan-kapalı SELL başarısızlık UI akışına ve
yerel RoutePage simülatörüne lazy callback'lerle bağlandı.
[SELL_BANK_ROUTE_UI.md](SELL_BANK_ROUTE_UI.md) güncel kapsamdır. Aşağıdaki
“henüz bağlanmadı” notu önceki API aşamasına aittir; native başlangıç ve
canlı oyun uyumluluğu hâlâ açıktır.

19 Ekim2026. Application artık EnginePage'e kendi panelinin gerçek combo
Text snapshot'ını ve seçilen kod sayfasını veren ayrı bir reader sağlar.
`panel_route_sample` yalnız ulaşılan türün metnini tüketir; her çağrıda tek
taze snapshot alır. Bu bir own UI örneğidir, native VCL/oyun gözlemi değildir.

SELL/BUY setup Unicode rota adını mevcut `compile_*_merchant_panel` çağrısına
iletir. Bu aşamada UTF8/ANSI çıktısı varsayılmaz. Madenin panel config çağrısı
ayrı explicit codec ile kayıpsız ANSI adını `manual_route_ansi/+5ffc` alanına
aktarır. Reader yoksa None/gap korunur; gerçek boş seçim ''/b'' olarak bilinir.
Panel seçeneği kapalıyken reader çağrılmaz. Eksik Text/bad snapshot, sıfır
isim veya önceki dosya adıyla doldurulmaz.

Bu bağ ayar tüketimini düzeltir. Dosya adı biliniyor diye scheduler/helper
gözlemleri veya maden/merchant start safhaları tamamlanmış sayılmaz. EnginePage
bank_route_allowed=False olan mevcut örnek davranışını değiştirmedi; native
rota başlangıcı veya oyun içinde yürüme eklenmedi.

## SELL banka rotası input API'si

`merchant_bank_route_inputs_from_panel`, bilinen SMerchant Text'ini source
5698bc alanı etiketiyle ANSI'ye dönüştürür ve explicit seçilen klasörü kendi
input object's57c prefix'ine bağlar. Kurucuda dosya okunmaz. DirectoryNone
bilinmeyen prefix olarak kalır; filename boşsa daha sonraki directory operandı
tüketilmez. Nonempty path absolute ve codec roundtrip denetiminden geçer.
Hiçbir native span/helper receipt'i veya RouteStart execution uydurulmaz.

Mevcut `plan_merchant_bank_route` ancak ulaşıldığında yerel dosyayı açar.
Entegre own deneme, panel Text İsim.R ->1254filename -> geçici .R dosyası ->
Bekle3adımı -> SELL failure caller zincirini sınar. Import ready olsa bile
dış route/string/helper span receipt'i olmadan MerchantRunner phase2de
needs_adapter döner. Ayrı explicit normal dönüş verildiğinde phase0 ve yalnız
`load_bank_route` yerel intent'i oluşur. Bu intent native yürütme/ACK değildir.

Yeni factory API düzeyindedir; EnginePage'in otomatik başarısızlık dispatch'ine
henüz bağlanmadı. Kaynak GetText/conversion/assignment ve kapsamlı ayar
yordamları native çalıştırılmadı. Önceki iki-sürüm1082instruction source
producer kanıtı yeniden doğrulandı; yeni benzersiz instruction sayısı eklenmedi.

Sekiz yeni test provider yok/empty/unknown, taze snapshot, Unicode vs explicit
ANSI/codepage, loss rejection, factory-no-IO, lazy directory, yerel dosya ve
outer-return gate ayrımlarını sınar. Yeni gizli UI kontrolü üç gerçek combo
seçimini SELL/BUY derleyicileri ve maden1254/UTF8 girdisinde gözler; madenin
eksik scheduler'ı tamamlanmış sayılmadığını ve non-panel dalının reader'ı
çağırmadığını denetler. Oyun okuması/yazımı/eylemi0, canlı uyumluluk açık.
