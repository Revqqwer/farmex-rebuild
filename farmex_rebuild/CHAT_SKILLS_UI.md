# Chat yetenek isteği arayüz bağı

20 Ekim 2026. Motor Denemesi içindeki **Chat Yetenek İsteği**, Job panelinin mevcut Mage TP, Rogue SW/Wolf ve Priest Buff/AC/Und/Str/Cure/Disease checkbox/metin alanlarını kullanır.18 gerçek alan her adımda yeniden derlenir; paneldeki bayrak ve tam keyword karşılaştırması sonucu değiştirir.

Mesaj HEX'i sınırlı yerel chat-prefix ayrıştırıcısına, gözlem JSON'u ulaşılan producer adımlarına verilir. Örnek JSON'daki `values` taze kanal/gate/sınıf gözlemleri, `normal_returns` helper dönüşleridir; bunlar oyun gözlemi olarak üretilmez. Kaynak producer'da bağımsız taze okumalar olduğundan JSON gözlemleri paket kanalını otomatik sabitlemez.1254/65001codepage seçimi açık ve keyword dönüşümü lossless olmalıdır.

İlk açılıştaki `10` ve `{}` girdileri eksik byte/gözlemde bekler. Sentetik “go” düğmesi seçilen sınıf için örnek mesaj ve gözlem doldurur; gerçek panel ayarlarını değiştirmez. Seçilen örnek sınıfı gerçek oyunun sınıf tespiti değildir. Aynı panel/HEX/codepage snapshot'ı mevcut frame'de devam eder; bunlardan biri değişince veya Sıfırla kullanıldığında yeni yerel deneme başlar. Tüketilmiş gözlemler sonraki eksik alan geldiğinde yeniden ayrıştırılmaz. Geçersiz ulaşılan girdi eski frame/sonucu temizler.

Sonuç yalnız bekleyen istek key/kind/sender ve context store projeksiyonudur. Kaynaktaki ilk eşleşme, signed Priest Buff gate ve pending overwrite guard korunur. Bu UI tüketici, session veya gerçek skill çağrısını çalıştırmaz; mesaj göndermez. Önceki generic HP/MP deneme alanları burada kullanılmaz.

Sekiz yeni birim testi dokuz ayar çiftini, güncel panel etkilerini, tam keyword eşleşmesini, invocation reset/cache'i, geç compare dönüşünü, codepage/HEX değişimini, bozuk JSON ve short-prefix sınırlarını kapsar. Gizli `smoke_chat_skills_ui.py`, gerçek18widget'ı kullanır; örnek düğmesinin ayarları koruduğunu, diğer denemede kontrollerin gizlendiğini ve generic HP alanı geçersizken bu yolun çalıştığını kontrol eder. Geniş gizli `smoke_ui.py` bu kontrolü diğer UI regresyonlarıyla birlikte çağırır. Sonuçlar `CHAT_SKILLS_UI_VALIDATION.json` dosyasındadır.

UI/compiler envanterine18alan eklenerek kapsam289 oldu; envanter dışı düzenlenebilir yollar233 kaldı. Bu sayılar bot özelliklerinin tamamlanma oranı değildir. Kaynak davranış kanıtı önceki `outputs/FarmexBot_chat_skill_istek_kaniti.json` raporudur; bu aşamada yeni ikili analiz veya REA Evidence üretilmedi. Gerçek oyun bağlantısı/native yetenek etkisi ve canlı eşdeğerlik açık kalır.
