# Doğrudan chat üreticilerinin tüketici bağı

20 Ekim 2026. Mage TP, Rogue SW/Wolf ve Priest Buff/AC/Und/Str/Cure/Disease olmak üzere dokuz doğrudan çağrı noktası, isteğe bağlı `ChatConsumerObservation.direct_execution` üzerinden `DirectChatExecutionPlan` sonucunu tüketir. Önceki yalnız opaque-normal dönüş gözlemi yolu korunur; o yol paket üretimini kanıtlamaz.

Bağlı sonuçta helper adresi, actor context DWORD'u, tam fiziksel hedef argümanı ve relative skill ulaşılan çağrıyla aynı olmalıdır. Rogue SW ve Priest WORD yüklemelerinde üst register bitleri fiziksel push kimliğinde korunur; üreticinin WORD kopyası bunları pakete aktarmaz. Wolf hedef argümanı almaz. Tam çocuk sonucu olsa da üst yardımcının ayrı normal dönüşü gerekir; eksik çocuk üstteki olumlu dönüşle atlanamaz. Kaynak helper EAX'ından başarı uydurulmaz.

Priest bekleyen isteği doğrudan helper çağrısından önce temizler; Mage/Rogue normal dönüşten sonra temizler. Çocukta kayıt oluşturulmadan sıfır hedef atlaması olması, üst tüketicinin AL1 döndürmesini engellemez ve skill başarısını kanıtlamaz. Eksik çocuk planında bu sıralama korunur; belleğe gerçek yazım yapılmaz.

`ChatConsumerFrame` eksik çocuk zenginleştirilirken tüketilmiş getter değerlerini, normal dönüşleri, hazırlanmış payload'ları, bilinen enqueue gate'lerini ve yerel kuyruk prefix'ini korur. Önceki kopyalar değiştirilemez veya kaybolamaz. Tam çocuk, üst helper dönüşü beklenirken yeni bir çocukla değiştirilmez. Alt sonuç sınıf tüketicisi üzerinden altı normal/legal başlığın sonucunda da taşınır. Sınıf başlıklarının ayrı post-lock gözlemi hâlâ gereklidir; alt store planından canlı lock çıkarılmaz.

13 yeni test dokuz çağrı noktasını, yanlış argümanları, ulaşılamayan dalda çocuğun tüketilmemesini, eksik builder/enqueue'yu, ayrı üst dönüşü, kuyruk/gate değişimini reddetmeyi, tüketilmiş getter'ları ve altı sınıf başlığında metadata taşınmasını sınar. Tam test sonucu `DIRECT_CONSUMER_BINDING_VALIDATION.json` içindedir.

Yeni ikili analiz iddiası yoktur. Bağ, korunmuş Ghidra/PE raporlarındaki kaynak kapsamını kullanır: `FarmexBot_mage_rogue_chat_tuketici_kaniti.json`, `FarmexBot_priest_chat_tuketici_kaniti.json` ve iki doğrudan üretici raporu. Dosya hash'leri doğrulama JSON'unda kayıtlıdır; bunlar yeni REA Evidence değildir.

UI/native C değiştirilmedi, UI yeniden test edilmedi. Producer'ın ortak pending yaşam döngüsü, gerçek callback/native helper çağrıları, kayıtların oyuna teslimi, server ACK ve canlı uyumluluk açık kalır. Bu bağ yerel modelleri birleştirir; orijinal botla uçtan uca eşdeğerlik değildir.
