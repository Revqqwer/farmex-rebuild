# Görev listesi tıklaması → ayrıntı görünümü

Gerçek `LwZoneQuests` mouse-release olayı `QuestDetailsFrame`'i çalıştırır.
Sağlayıcı `set_source_quest_details_provider` ile açıkça bağlanır. Kayıtlar
önceki yerel Yenile akışının koleksiyonundan gelir; oyun veri edinimi bağlı değildir.
Sağlayıcı yokken tıklama ayrıntıları değiştirmez ve veri bağlantısını bildirir.

Tıklamada görünür seçim ve satır caption'ları kendi snapshot'ımıza alınır.
Caption'dan çıkarılan koleksiyon indeksi kullanılır; görünür sıra numarası
doğrudan kayıt sayılmaz. Sıralama ve NPC filtresinden sonra da doğru kayıt
gösterilir. Programatik seçim veya görünümün tekrar çizilmesi yeni tıklama
olayı üretmez. Negatif seçim mevcut başlık ve ayrıntı satırlarını korur.

Sütun başlıkları çalışma zamanı durumunda tutulur ve tekrar çizimde geri gelir.
Başlık0 seviye, başlık1 görev adıdır; ikisi de ayrıntı satırlarının Clear
işleminden önce atanır. Eski başlıkların yerine olmayan varsayılan `Ad`
metinleri eklenmez. Sonra NPC, Görev etiketi, boş satır ve Ödül etiketi gelir.
Etiketler gerçek gereksinim veya ödül içerikleri olarak gösterilmez.

`QuestDetailsContext` ticket, nesil, aşama, seçili görünür satır, çözüldüyse kayıt
indeksi ve eksik bilgiyi sağlayıcıya taşır. Eksik dönüş/dönüşümde oluşmuş önek
korunur. Kendi 100ms timer'ımız başka form görünürken de devam eder. Bu kendi
snapshot/timer politikamız native VCL event/concurrency eşliği değildir.

Yenile, NPC filtresi, metadata ve ayrıntı işlemleri aynı görünümde birbirinin
bekleyen akışına girmez. Yeni bir ayrıntı sağlayıcısı, bekleyen ayrıntı işini
iptal ederken görev koleksiyonunu korur. Profil/panel değişimi eski yanıtı ve
timer'ı geçersiz kılar. Liste/sütun başlığı sağlayıcı içinde değiştirilirse
eski gözlem bu değişikliğin üzerine yazılmaz.

Odaklı kontrol ve tam GUI, gerçek mouse-release binding'i üzerinden sıralı ve
filtreli indeksleri, kolon/satır sırasını, dört satırı ve boş satırı, seçimsiz
korumayı, gizli formda devamı, hatalı kod sayfası düzeltmesini, rakip düğmelerin
bekletilmesini ve eski başlık/profil yanıtının reddini kontrol eder. Ortak eylem
kuyruğu ve görev koleksiyonu değişmez. Tam kayıt `QUEST_DETAILS_UI_VALIDATION.json`;
önceki API açıklaması `QUEST_DETAILS.md` kendi önceki aşamasını anlatır.

Native formatter/getter/string/codepage/heap/VCL/SEH/runtime eşliği, seçili
Al/Ver ve canlı oyun bağlantısı açık kalır. Bu görünüm bir görev alma/iptal
onayı veya gerçek ödül sorgusu değildir.
