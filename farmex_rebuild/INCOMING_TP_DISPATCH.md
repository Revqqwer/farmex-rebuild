# Gelen olay dispatcher'ından TP dalına kaynak bağı

`incoming_tp_dispatch.py`, kendi değişmez packet byte görüntüsüyle004d82a4 dispatcher'ının TP dalına ulaşma yolunu modeller. Bu bir oyun hook'u veya canlı paket dinleyicisi değildir. Oyun nesnesindeki context+8 pointer'ı veya uzunluk alanının kimliği hâlâ doğrulanmadı.

Önce dispatcher'ın004d82a4 prologue/SEH kurulumunun normal tamamlandığı ayrı gözlemle belirtilir. Çocuğun `entry_reached=True` girişi bu koşulu atlatamaz. Kaynak sonra sırasıyla08,10,11,12,14,15,17,18,1a,1b,21,23,24,26 opcode'larını karşılaştırır. Her başarısız karşılaştırma altı instruction'lık sonraki başlığa gider; bu başarısız yollarda başka yardımcı çağrısı yoktur. Own packet byte0 değeri27 ise14 yol da eşleşmez ve004d88e4 TP bölümüne ulaşılır. TP child girişi bu kaynak akışından otomatik türetilir.

Önceki opcode'lardan biri eşleşirse model o dalın gerçek gövde adresinde eksikle durur. Örneğin10 chat gövdesini atlayıp TP'ye geçmez. Chat için mevcut `IncomingChatFrame` modeli ayrı kalır; bu composition onu tamamlanmış varsaymaz.27 dışında sonraki opcode'lar için de “başarıyla işlendi” sonucu verilmez;004d8a98 sonraki bölüm sınırı açık kalır.

TP child normal tamamlanınca kaynak004d8a84'te EAX1 yazar, kaydedilmiş FS değerini geri koyar,004d9230'a atlar ve MOV ESP/POP EBP/RET4 ile döner. Bu normal kaynak yolu için EAX1 ve dört bayt stack temizleme bilgisi türetilir. Native register/stack/SEH yürütmesi, gerçek callback ABI'si ve oyuna teslim sonucu doğrulanmış değildir. EAX1 bir sunucu ACK'si olarak sunulmaz.

Çocuk getter/clock/notice/stop/DC gözlemi beklerken dispatcher kurulumu ve tüketilen child öneki korunur. Tamamlanmış aynı invocation tekrar ilerletilince yardımcı çağrı planları yeniden üretilmez. Eksik packet aralıkları kaynakta güvenli reddediliyor sayılmaz; yalnız own modelde desteklenmeyen veri aralığıdır. Gerçek packet belleği eşzamanlı değişebiliyorsa bu sabit snapshot modeli onun kanıtı değildir.

İki sürümde1123'er instruction'ın2246 kaydı disk baytlarıyla doğrulandı.14 adet altışar instruction'lık prefix ve yedi instruction'lık normal çıkışın toplam182 kaydı bu kapsama dahildir; ek benzersiz kapsam sayılmaz. Önceki tam REA çıktısı hash/adres/assembly ile yeniden eşleştirildi; yeni REA çağrısı yapılmadı.

Sekiz test; prologue atlatılamaması,14 erken eşleşmenin doğru sınırda durması, TP child girişinin türetilmesi, gözlem boşluklarında korunmuş önek, diğer opcode'ların tamamlanmış sayılmaması, kısa packet ve normal dönüşün tek seferliği üzerinedir. Arayüz veya gerçek oyun dispatcher'ı bağlanmadı; native/live bayraklarıFalse kalır.

Kaynak kanıtı: `outputs/FarmexBot_TP_dispatch_bagi_kaniti.json`; önceki TP kapsamı: [TELEPORT_PROTECTION.md](TELEPORT_PROTECTION.md).
