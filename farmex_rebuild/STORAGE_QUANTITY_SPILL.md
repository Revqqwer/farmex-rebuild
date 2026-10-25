# Uzun miktar kopyasının kaynak modeli — 19 Ekim 2026

004653a8 modelinin on/on bir karakterlik yolu, açık başlangıç pointer'ı ve değişmiş pointer'dan alınan bayt gözlemleriyle genişletildi. `StorageQuantitySamples.source_pointer_dword` ve sıralı `spilled_read_samples` girdileri kullanılır. Oyun veya başka bir sürecin belleği okunmaz; yalnız yerel Python bayt dizisi hesaplanır.

Tampon EBP−3c, saved source pointer EBP−34 konumundadır. İlk dokuz karakterin sonuncusu pointer'ın düşük baytını değiştirir. Sonraki iterasyon değiştirilmiş pointer+indeks adresinden okur ve okunan baytı pointer'ın sonraki baytına yazar. On bir karakterlik örnekte ikinci okumanın adresi ilk gözlem baytına bağlıdır.

Başlangıç pointer'ı 12345678 ve normal metin `-2147483648` için:

| İndeks | Kopyalanan bayt | Sonraki pointer | Sonraki kaynak okuması |
|---|---|---|---|
| 8 | 36 hex (`6`) | 12345636 | 1234563f |
| 9 | Açık gözlem: 00 | 12340036 | 12340040 |
| 10 | Açık gözlem: ff | 12ff0036 | Döngü biter |

Bu gözlemlerle kopya verisi `-21474836\x00\xff` olur. Özgün format metni ayrı kalır ve uzunluk alanı hâlâ 11'dir. memcpy NUL'da durmaz; gözlenen NUL ve ASCII dışı baytlar korunur. Böylece model, kaynakta oluşabilecek farklı çıktıyı tekrar düzgün decimal metne çevirmemiş olur.

`stack_copy_bytes` o ana kadar çözülen kopyayı, `source_pointer_writes` pointer değişimlerini gösterir. Başlangıç pointer'ı yoksa mevcut unresolved sonucu korunur. Sonraki adres/bayt eksikse akış cache ve hedef yazımlarından önce durur; yanlış adresteki gözlem reddedilir. Kısa yollar ek spill gözlemlerini tüketmez. Format spanı, her kopya ve dış helper normal dönüşü için önceki ayrı koşullar devam eder.

10 yeni test dahil **2551 test, 6.539 saniye** geçti. Bağımlı adresler elle hesaplanan örneklerle, NUL/ff baytlarıyla, eksik/yanlış okumalarla ve dış caller dönüş kapısıyla sınandı. Ortak 222 talimatlık iki sürüm denetimi yeniden geçti; yeni benzersiz talimat sayısı değildir. Kanıt Ghidra/disk denetimidir, REA Evidence değildir.

Yeni yol API kapsamındadır; arayüz değişmedi ve bu tur UI testi tekrarlanmadı. Native stack/frame geçerliliği, değişmiş pointer'ın gerçekten okunabilirliği, fault/exception davranışı, gerçek kopyalama ve oyun uyumluluğu kanıtlanmadı. Tamamlanmış operand planı, özgün yordamın çalıştırıldığı veya sağlıklı döndüğü anlamına gelmez.
