# DC–Hapis pencere listesinin kaynağı

`jail_selection.py`, `0046ce04` yordamının140 instruction'lık normal kontrol akışını kendi liste projeksiyonuna bağlar. Bu vektör, hapis korumasının `0046dc5c` çalışma yardımcısının okuduğu context `+c0` vektörüdür; içerik başlangıç/bitiş pointer'ları context `+d0/+d4` alanlarındadır. Gerçek VCL veya oyun nesnesi oluşturulmaz ve native vektör belleğine yazılmaz.

## Arayüz ve olay kimliği

Kaynakta ayrı `TfrmDCWindow` sınıfının VMT başlığı aynı field table, method table ve class-name kayıtlarına işaret eder. Field table `bancloselist` alanını object `+3d4` ile eşler. Kaynak UI modeli bu alanın checkbox'lı iki sütunlu liste olduğunu gösterir. `frmMain` üzerinde de `3d4` offset'i bulunması bu alanları aynı nesne yapmaz; sınıf kayıtları ayrı doğrulandı.

Üç published method kaydı:

| Olay | Kaynak adresi | Normal çağrı zinciri |
|---|---|---|
|FormShow|0045bf8c|0045bab0 liste yenileme|
|Listeyi Yenile / Button1Click|0045bfa4|0045bab0 liste yenileme|
|Kaydet ve Kapat / Button2Click|0045bfbc|context5690f8 ile0046ce04; sonra TCustomForm.Close|

`0045bab0`339 instruction'lık yenileme yordamı süreç snapshot'ı, executable arama, kimlik metni, mevcut satırlarla duplicate kontrolü ve yeni satır/karakter adı ekleme zincirlerini içerir. Bu aşamada yenilemenin tamamı modellenmedi. Ham uzak metin okuma yardımcısının serbest bırakılmış pointer döndürmesi burada da önemlidir; metinlerin güvenilir veya başarıyla okunmuş olduğu varsayılmaz.

## İşaretli satırları aktarma

Model giriş/prologue, scratch string initialization ve vector end/begin/erase yardımcılarının normal dönüşlerini ayrı bekler. Erase yardımcıları opak olduğundan normal dönüş tek başına listenin boş olduğu kanıtı sayılmaz; `after_reset` içeriği açık, değişmez bir gözlemdir.

Her turda UI `TListItems.GetCount` sonucu yeniden alınır ve indeksle **signed** karşılaştırılır. Satır varsa item getter ve Checked getter ayrı gözlemlerdir. Checked sonucunun düşük AL baytı sıfırsa metin dönüşümü ve vector insertion tamamen atlanır. Nonzero2 de true dalına girer; bool1 şartı eklenmez.

İşaretli satırın kaynak Unicode getter, ANSI conversion, scratch assignment, ANSI temporary cleanup ve Unicode temporary cleanup sırası korunur. ANSI byte'ları yakalanmış gözlemdir; Python metni üzerinden kaynak RTL/codepage davranışı tahmin edilmez. Sonra vector size ve capacity yardımcıları ayrı normal dönüş/DWORD sonuçlarıyla alınır. **Unsigned size<capacity** hızlı insertion yoludur. Bu yol taze end pointer'ını kullanır ve insertion normal dönüşüyle dönen EAX değerini context `+d4` alanına yazılmış olarak planlar. Diğer yol end iterator hazırlığı ve reallocating insertion yardımcısını bekler; hızlı end-store bu dala eklenmez.

Kendi liste projeksiyonuna yalnız tamamlanmış insertion'dan sonra eklenir. Fast yolda dönen end EAX eksikse store ve ekleme henüz yapılmaz. Sonraki satır/cleanup beklerken kabul edilmiş önceki başlıklar korunur. Tek frame tekrar ilerletilince eski satırlar tekrar eklenmez; henüz ulaşılamayan count/metin gözlemleri erkenden saklanmaz. Yeni invocation için yeni frame gerekir.

## Kanıt ve sınırlar

10 hedefli test; açık reset içeriği, signed UI count, rawAL, yalnız checked satırlar, unsigned size/capacity, iki insertion yolu, fast returned-end store, cleanup/insert kesintileri, tüketilen önekin korunması, yeni count/metin gözlemleri ve context taşmasını denetler. Sekiz kaynak yordam iki sabit Richard görüntüsünde toplam **1928 instruction kaydıyla** doğrulandı. Altı yeni REA çıktısı ve bir mevcut çalışma yardımcısı çıktısı doğrulandı. Kaynak kayıt: `outputs/FarmexBot_koruma_pencere_liste_kaniti.json`.

İlk iki komşu yordam adayı `0046dd70/0046d904` liste üreticisi değildir; bunlar başka koruma eylemi tüketicileridir. Bu ayrım kanıt dosyasında kayıtlıdır. Yeni model yalnız0046ce04 içindir; yenileme, kapatma callback'i ve diğer eylem tüketicileri için tam davranış sertifikası verilmez.

Model API kapsamındadır. Mevcut UI henüz bu save modelini veya liste→canlı pencere bağlantısını kullanmaz. Native string/iterator/erase/allocator etkileri, istisnalar, gerçek form/vtable kimliği, liste lifetime'ı ve canlı uyumluluk açık kalır. Hiçbir süreç listelenmedi, oyun belleği okunmadı veya süreç kapatılmadı.
