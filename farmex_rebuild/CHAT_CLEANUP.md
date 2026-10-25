# Chat işleyicisinin ortak normal temizleme bölümü

21 Ekim 2026. `chat_cleanup.py` yalnız `0045730e..00457384` normal dönüş bölgesine ulaşıldığı verilmişken çalışır. Önceki log/komut/davet/skill bölümlerinin veya başka tail dallarının tamamlandığını bu model tek başına göstermez.

Kaynak sıra: `[EBP-104hex]`, `[EBP-108hex]`, `[EBP-f4hex]` yerel pointer'larını üç ayrı `_free` çağrısına geçir; `[EBP-cChex]` yerel DWORD'undan2 çıkar; `004040f8` yardımcısına fiziksel `(2,EBP-54hex)` push'larını yap; yerel DWORD'u azalt; `00403860` için `(0,1,EBP-50hex)` push'larını yap; tekrar azalt; aynı reset yardımcısını `(0,1,EBP-28hex)` ile çağır. Son olarak `[EBP-e8hex]` değerini FS:0'a geri yükleyen store planı ve normal epilogue gelir.

`004040f8` ikinci argümanın bit0'ını sınar; çağrıdaki2 için bit0 kapalıdır.2değerini dizi eleman sayısı diye yorumlamak kaynakla desteklenmez. İç `005050bc` runtime çağrısı opaque kalır. `00403860` descriptor kapasitesini0fhex'e, uzunluğu üçüncü argümana getirir; caller üçüncü argüman0verir. Alt allocator/free/runtime gövdeleri ve string ownership'i tam çözümlenmiş sayılmaz.

`ChatCleanupArgs` sabit yerel DWORD snapshot'ını taşır. `ChatCleanupObservation` her yardımcı ve epilogue için ayrı normal dönüş ister. Sıfır pointer verilmesi kaynak `_free` çağrısını modelden çıkarmaz. `ChatCleanupFrame` tüketilen normal dönüşleri korur; daha sonra eksik kalan adıma devam eder. Yerel sayaç ve frame-relative adres hesabı DWORD taşmasını korur. Sayaca nesne sayısı veya başarı anlamı verilmez.

Sonuçta görünen store'lar prospective yerel projeksiyonlardır. Orijinal pointer serbest bırakılmaz, descriptor/native bellek yazılmaz ve FS kaydı değiştirilmez. Tam sonuç dahi heap etkisi, EAX başarı değeri, native yürütme veya canlı doğrulama değildir. Kaynak exception/unwind yolları ve aliasing bu normal modelin dışındadır.

`work/audit_chat_cleanup.py`, eski/güncel PE'lerde35'er tail talimatını ve24+45'er iki yardımcı talimatını karşılaştırdı: toplam208 kayıt. Her kayıt dosya baytlarıyla doğrulandı; üç `_free` import kimliği ve farklı runtime adresleri normalize edildi. Kaynak `outputs/FarmexBot_chat_temizlik_kaniti.json`; korunmuş Ghidra/PE kanıtıdır, yeni REA Evidence değildir.

Altı yeni test exact push sırasını, ara store'ları, her normal dönüş boşluğunu, cache/final sonucu, DWORD taşmasını ve sıfır pointer çağrı sınırını kapsar. Tam koşu `CHAT_CLEANUP_VALIDATION.json` dosyasında tutulur. UI/native C değiştirilmedi; UI yeniden test edilmedi. Temizlemenin önceki handler modellerine bağlanması ve gerçek oyundaki normal dönüşü açık kalır.
