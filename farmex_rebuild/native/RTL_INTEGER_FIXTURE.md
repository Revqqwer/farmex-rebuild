# Kendi süreçte sabitlenmiş RTL sayı gözlemleri

`rtl_integer_fixture.c`,32 bit kendi test sürecinde yalnız hash'i doğrulanmış `rtl260_7d98acb8fade7f09.bpl` yükler. `TryStrToInt64` export'u çağrılır; bot/oyun modülü yüklenmez, hedef PID seçilmez. Module path yükleme sonrasında ayrıca eşleşmelidir. Build script derleyici SHA256 kontrolü yapar. Orijinal BPL veya derlenmiş fixture teslim ZIP'ine konmaz.

Register ABI dosyadaki32 baytlık TryStrToInt64 gövdesinden doğrulandı: EAX UnicodeString karakter pointer'ı; EDX sonuç QWORD pointer'ı; AL başarı. Yordam EDX'i ESI'de saklar, kendi stack yerel Code adresini EDX'e koyarak `_ValInt64` çağırır, EDX:EAX sonucunu kullanıcı QWORD'una **hatalı girdide bile** yazar, Code0 ise AL1 üretir.16 instruction/32bayt sadece bu ABI gövdesini kapsar. String metadata statik refcount−1/UTF16/uzunluk ile kendi buffer'ımızda oluşturulur.

52 native girdi gözlemi: decimal0/işaretler, baş/son boşluk ve control characters, `$`/`0x`/`x` hex biçimleri, signed64 decimal sınırı, unsigned64 hex ve negatif hex, uzun leading zero, invalid prefixes, embedded NUL ve iki non-ASCII code unit. Her çağrıda stack pointer aynı kaldı. Bu bir tam parser davranış sertifikası değildir; örneklerin dışında ve native exception/lifetime yollarında tamlık iddiası yoktur.

Gözlenen ayrımlar: baştaki U+0020 kabul edilir; sondaki boşluk ve TAB/LF kabul edilmez. `$10`,`0x10`,`x10`16 olur. `$ffffffffffffffff` kabul edilip QWORD ffffffffffffffff verir; aynı pozitif decimal signed64 sınırını aşınca reddedilir. `-0xFFFFFFFFFFFFFFFF`1 olur. UTF16 `5\0x`, uzunluğu3 olmasına rağmen5 olarak kabul edildi. Tam genişlik rakam ve NBSP kabul edilmedi. Invalid girdilerde kısmi accumulator sonucu bulunabilir; bunu parser başarısı saymayız. Kaynak bot wrapper'ının fallback10 davranışı ayrı catch yoluna aittir; bu fixture exception üreten StrToInt64 yerine Try yordamını çağırır.

Bu aşama, UI ondalık alt kümesini henüz değiştirmez. REA ile StrToInt64/TryStrToInt64/_ValInt64 tam statik çözümlemesi ayrı devam eder. Pinned RTL'nin oyunda gerçekten yüklendiği, botun native catch/heap/managed-string yolları ve canlı uyumluluğu doğrulanmamıştır.
