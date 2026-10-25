# Panel bağlantı kapsamı

Güncelleme UTC: 2026-10-25T08:58:19.486841+00:00

Toplam bağlı giriş kontrolü: **379**. Envanter dışında kalan düzenlenebilir ana sekme kontrolü: **144**.

| Ana sekme | Kaynak bileşen | Düzenlenebilir | Bağlı giriş | Envanter dışında |
|---|---:|---:|---:|---:|
| Genel | 74 | 46 | 19 | 27 |
| Bot | 75 | 48 | 26 | 22 |
| Job | 163 | 100 | 95 | 5 |
| Item | 26 | 19 | 15 | 4 |
| Tedarik | 45 | 30 | 26 | 4 |
| Koruma | 66 | 51 | 51 | 0 |
| Kontrol | 69 | 55 | 42 | 13 |
| Diğer | 57 | 42 | 36 | 6 |
| MS - Draki | 37 | 20 | 4 | 16 |
| Upgrade | 36 | 15 | 4 | 11 |
| Maden | 43 | 30 | 27 | 3 |
| Item Kır | 18 | 11 | 3 | 8 |
| Merchant Tarama | 27 | 9 | 0 | 9 |
| Flood - Etrafa PM | 15 | 4 | 1 | 3 |
| Sell Merchant | 43 | 18 | 14 | 4 |
| Buy Merchant | 38 | 16 | 12 | 4 |
| Log | 6 | 2 | 0 | 2 |
| Gorevler | 15 | 3 | 0 | 3 |

**Güncel yerel GUI/kod doğrulaması:** QUEST_READ_STRING_VALIDATION.json — 4977 Python testi; 1037 kontrol/11 form/18 sekme.

Yeni GUI çalıştırılmadı; 4960 testli QUEST_NAME_COMPOSITION_VALIDATION.json aşamasındaki tam GUI import closure hashleri değişmedi.

Existing actual ANSI comparison/lookup/Take/Give/common queue scope preserved. New fine-grained read-string API not yet lookup-composed; native read/RTL/codepage/refcount/SEH/runtime and automatic game acquisition/delivery remain unverified.

Bu kayıt native/game uyumluluk sertifikası değildir. Aşağıdaki adlandırılmış eski doğrulama notları tarihsel aşamalardır.


Bileşen, düzenlenebilir kontrol ve compiler girişi farklı kümeleri ölçer. Ana sekme dışındaki girdiler toplamda bulunabilir. Bu sayılardan özellik tamamlanma yüzdesi çıkarılmadı.

Kaynak yollarının bağlı olması, davranışın yerel model/önizleme tarafından tüketildiğini gösterir. Her alt özelliğin kaynak, UI, native ve canlı kanıt kapsamı kendi raporundadır.

**Fonksiyon takibi:** 298 sınırlı eşleme; tam fonksiyon sertifikası0; canlı uyumluluk sertifikası0.

Son UI genişlemeleri: DC/relog14 alanı(13 yeni compiler girdisi), Genie5 alanı ve Kontrol Ayarları15 alanı(2 yeni girdi). Kupon senkronizasyonu ve kontrol tüketici köprüsü ayrıca API modelleridir. DC Bekle/Manuel Rota kutuları ile Genie NoMob/süre alanları çalışma tüketicisi doğrulanmış yeni girişler olarak sayılmadı. Zone/Town bayraklarında yalnız ayar üreticisi bağlıdır; oyun içi durdurma etkisi kanıtlanmadı.

Kaynak: FarmexBot_guncel_ayar_motor_baglari.json, FarmexBot_panel_bag_eksikleri.json ve FarmexBot_fonksiyon_takibi.json. Güncel yerel GUI/kod kaydı MERCHANT_CELL_RUNTIME_VALIDATION.json içindedir:4272 test ve1037 kontrol/11form/18sekme. Merchant query/ANSI adları ve gerçek PM/GİT cell olayları kontrol edildi. Cell QA kısa saydam ekran dışı mapped aşama kullanır. Native/game uyumluluk ve özelliklerin bütünü tamamlanmış değildir.

Merchant sonuç listesinde filtre/query/başlık sırası ve kendi semantic PM/GİT hücreleri bağlıdır. PM ortak own preview kuyruğunda; GİT kanonik koordinat hedef intenti olarak hazırlanır. Kaynak ekran-X handler, üç SetEnabled/scan etkisi ve native sender/movement çalıştırılmış sayılmaz. Kaynak runtime CP/FPU/global, initialization gate ve tarama oturumu açık. Üç filtre kontrolü compiler envanteri dışında partial-UI olarak kalır. Son kapsam MERCHANT_CELL_RUNTIME_VALIDATION.json dosyasındadır.

Item Kırma Ayarları üç gerçek enable/hız/Abyss kontrolünden kaynak ayar planına ve kendi yerel shadow alanlarına bağlıdır. Worker, manuel düğme ve istek kuyruk API modelleri ayrıca vardır; bu üç-field panel bağlantısı gerçek oyun işlemi değildir. Diğer sekiz tasarım alanı için ayrı mod çalışma kanıtı yoktur.

Son tarama UI aşaması MERCHANT_SCAN_RUNTIME_VALIDATION.json içindedir:4296 Python testi ve tam1037 kontrol/11form/18sekme geçti. Gerçek başlat/durdur/checkbox ve rota Int32 akışı yerel oturuma bağlıdır. GİT tarama bayraklarını/düğmelerini dönüşümden önce değiştirir; PM korur. Altı tarama giriş yolu compiler envanteri dışında partial-UI olarak ayrıca işaretlenir (filtre yollarıyla örtüşebilir). Zamanlayıcı, gerçek veri sağlayıcısı/yanıt dispatch, tek tarama ve TXT hâlâ açıktır. Önceki4272 kapsam notları tarihsel aşamayı anlatır.

Güncel yerel doğrulama MERCHANT_TXT_EXPORT_VALIDATION.json içindedir:4330 Python testi ve tam1037 kontrol/11form/18sekme. Kaydet gerçek kendi dosyasına yazar; explicit kimlik/tm/metin ve dosya yolu kod sayfaları gerekir. Eksik bağlam dosya üretmez; stale tablo reddedilir ve profil sağlayıcıyı sıfırlar. Otomatik oyun bağlamı, source C++ stream/default CP/SEH eşliği hâlâ açık. Önceki4272/4296 notları tarihsel aşamalardır.

Son yerel doğrulama MERCHANT_QUICK_TABLE_VALIDATION.json:4352 Python testi ve tam1037 kontrol/11form/18sekme. Gerçek Tara düğmesi immutable captured-value provider ile dört-cache sonuçlarını açık CP altında ortak filtre/arama/tabloya bağlar. Eksik sağlayıcı/lookup/metadata başarı0-kayıt sayılmaz; liste başta temizlenir, eksik raw önek saklanır. Normal tarama Tara enable durumunu yönetir; profil sağlayıcıyı sıfırlar. Otomatik oyun verisi ve native helper/copy/lookup/SEH eşliği açıktır. Önceki4272/4296/4330 UI notları tarihsel aşamalardır.

Güncel kaynak üretici aşaması MERCHANT_QUICK_SOURCE_VALIDATION.json:4372 Python testi ve tam1037 kontrol/11form/18sekme. Tara artık lower-level lookup/read/copy/ftol gözlemlerinden actor/item ve son isim üretimini de tüketir. Quick-specific kategori/family/storage/data ve carry sırası korunur; eksik veriden normal dönüş uydurulmaz. Bu, oyundan otomatik gözlem edinimi veya native helper/SEH eşliği değildir. Önceki GUI notları tarihsel aşamaları anlatır.

Son izole API düzeltmesi MERCHANT_SCAN_SCHEDULER_VALIDATION.json:4384 Python testi. Zamanlayıcı ikinci/fresh tüketim saatini, koleksiyon sonrası fresh rota boyutunu,554020 actor alanını ve bağımsız helper dönüşlerini kullanır. Yeni GUI çalıştırılmadı; app/smoke_ui300 modül closure kaynakları4372 tam GUI kaydıyla aynı, değişen scheduler/test closure dışında. Gerçek timer/helper/data bağlantısı açık.

Son own invocation-frame aşaması MERCHANT_SCAN_FRAME_VALIDATION.json:4396 Python testi. Yalnız tüketilmiş gözlemler saklanır; bekleyen normal dönüş istekleri token ile bir kez üretilir, post saat beklemek consume isteğini yinelemez. İstekler native komut/ABI argümanı değildir. Yeni GUI çalıştırılmadı; aynı300 modüllük closure kaynakları4372 full GUI kaydıyla aynıdır. Child executor ve timer/data sağlayıcıları açık.
