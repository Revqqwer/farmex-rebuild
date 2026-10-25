# Chat/PM parti daveti arayüz bağı

19 Ekim 2026. EnginePage içindeki **Chat/PM Party**, Diğer > Party Davet Ayarları panelinin `chinvitechat`, `txtinvitechat`, `chPartyChatInviteListControl` alanlarını ve ortak PartyList caption'larını okur. Ayarlar her adımda taze okunur. Genel HP örneği veya sınıf-panel checkbox'ına bağlı değildir.

Başlangıç HEX değeri `10`, JSON `{}` olduğundan eksik veri açık kalır. **Sentetik Alice “add” mesajı** düğmesi ayrı, etiketli yerel örnek yükler; paneli kendi kendine etkinleştirmez veya komutu değiştirmez. Kod sayfası1254/65001 açıkça seçilir. Orijinal DLL çalıştırılmaz; oyun/ağ bağlantısı veya gerçek davet gönderimi yoktur.

Aynı HEX, panel, isim listesi ve kod sayfasında aynı `ChatPartyInvitationFrame` devam eder. Eksik ikinci kuyruk gözlemi geldiğinde ilk kayıt korunur. Tamamlanmış aynı denemede tekrar adımlamak yeni kayıt oluşturmaz. Sıfırla veya sentetik örnek düğmesi yeni deneme açar. HEX/panel/list/kod sayfası değişirse yeni boş yerel frame oluşur; önceki denemenin kuyruğu yenisine taşınmaz. Bu deneme politikası gerçek oyundaki iki aynı mesajı birbirinden ayırt eden bir capture sistemi değildir.

JSON yalnız ulaşılan alanları tüketir. `helper_returns` karşılaştırma/actor/filtre/argüman/davet dönüşlerini, `actor_dword` kendi karakter gözlemini, `use_owned_filter` veya `filter_eax` filtre yöntemini belirtir. `queue_samples` içindeki `1`/`2` nesnelerinde `gate` ve `tick`, `enqueue_returns` içindeki `1`/`2` bool değerlerinde ayrı normal dönüşler bulunur. `cleanup_returned` ayrıca gerekir. Daha önce tüketilmiş gate yeniden ayrıştırılmaz; gate0 yolunda tick gerekmez. Ulaşılmayan bozuk alanlar değerlendirilmez. Bozuk HEX, JSON veya ulaşılan alan hatası önceki sonucu/frame'i temizler.

**9 yeni adaptör testiyle toplam2657 birim testi geçti (8.215s).** Tam gizli UI testi1037kontrol/11form/18ana sekmede geçti. Gerçek Tk enable checkbox'ı, komut Entry'si ve liste kısıtlama checkbox'ı kullanılarak Alice/Carol, harf farkı, unchecked caption, kısmi kuyruk devamı, tekrar adım ve stale-frame temizliği doğrulandı. Son gösterimdeki yerel kayıt sayısı da ayrı odaklı UI kontrolünden geçti. Hiçbir test oyuna eylem göndermedi.

UI/compiler kapsamındaki alan sayısı252'den255'e çıktı; bu özellik tamamlanma yüzdesi değildir. Kapsam dışında267düzenlenebilir yol bulunuyor; bunlar doğrudan eksik özellik sayısı değildir. Kaynak analizindeki528talimatlık dar kapsam, önceki chat dallarının ulaşıldığını veya tüm fonksiyonun eşdeğerliğini kanıtlamaz.96bayt üstü isim stack çakışması ve native/canlı uyumluluk açık kalır.
