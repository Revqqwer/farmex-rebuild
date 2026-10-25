# Sayı yardımcısı ve Genie süre yazımları

`source_integer.py`,0045ef80yardımcısının gözlenen dönüş/operand akışını modeller. Metin UnicodeString snapshot'ıdır. Kopya normal dönüşü, seçilen normal/catch-landing yolu, parser veya landing cleanup dönüşü ve son argüman temizliği ayrı gözlemlerdir. Varsayılan DWORD, CDQile64bite işaret genişletilir; başarılı parser sonucu EDX:EAXolarak korunur. Son argüman temizliği beklemesinde sonuç değiştirilemez.

Normal parser rtl260.bpl içindeki `System.Sysutils.StrToInt64` importudur. Sözdizimi kabulü, boşluk/hex/range davranışı ve hangi hatanın hangi exception yolunu tetiklediği bu modelde çözülmüş sayılmaz. Hatalı veya boş metin otomatik varsayılan üretmez. `catch_landing` açıkça bu kaynak yoluna ulaşıldığını bildiren ayrı gözlemdir; catch cleanup normal dönüşü de gerekir. Kaynak descriptor'ının45efd9adresini göstermesi, o adresteki ham kod ve `_CatchCleanup`importu denetlendi; gerçek EHdispatch/unwind yürütülmedi.

`genie_duration.py` iki açıkça ulaşılmış üretici yazımını bağlar:

| Alan | Kaynak varsayılan | Yazım |
|---|---|---|
| resume_seconds |60|569114 DWORD|
| notice_minutes |30|569144 DWORD|

Her ikisi de tamamlanan generated sayı alt modeli ve ayrıca0045ef80üst normal dönüşü ister. Yalnız EAXyazılır: gözlenenQWORD4294967297ise yazım1olur; negatif-1ise hamFFFFFFFFyazılır. Bu aktarım metnin native parser tarafından kabul edildiğini kanıtlamaz. Worker eşikleri daha sonra kendi signedlow32çarpım ve signedQWORDelapsed kurallarıyla değerlendirilir.

Sekiz helper ve beş üretici testi eklendi; son tam koşu3025testtir. Eski/güncel48'er talimat96kaynak kayıt ve ayrıca11'er ham landing baytı doğrulandı. Bunlar önceki ikili envanterdeki mevcut kodlardır. Yeni REA Evidence, tam fonksiyon sertifikası veya native parser eşdeğerliği iddiası yoktur.

API-only bağdır. Gerçek widget okuması, profil compiler'a yeni alan bağlama, VCL/RTL çalıştırma, oyun belleği ve canlı Genie etkisi yapılmadı. Mevcut diğer derleyicilerin kendi decimal politikaları bu değişiklikle otomatik native eşdeğer sayılmaz; ilgili tüketicilere bağlama ayrı iştir.
