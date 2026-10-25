# Kaynak profil seçimi ve gönderici alanlarının kurulumu

21 Ekim sender referans düzeltmesi:sıfır dolgulu/dolgusuz adresler aynı taramada15mention(13okuma/2adres argümanı)veriyor.1375mevcut talimat doğrulandı; ek hedef karşılaştırmaları ve yerel şablona kaynak kopyası slot yazıcısı sayılmadı. Kurulu EXEhashaynı/steam_api.dll yok; canlı Applicationyolu/profil/ABI doğrulanmadı. Runtime/UI değişmedi, son tam test3025/yeni koşu yok. [Kapsam](SENDER_REFERENCE_RECHECK.md).

19 Ekim 2026. `source_profile_selection.py` iki dar aşamayı modeller: `004a199c` içindeki FileExists-sonrası dönüş/cleanup kararı ve `0049f470..0049f4c0` başlangıç profil seçimi. Tam kurucu veya canlı auto-profile uygulaması değildir.

Statik kaynak, `TApplication.GetExeName` sonucunun ANSI zincirinden geçirilip `ExtractFilePath` ile klasörünün alındığını, `steam_api.dll` eklendiğini ve `FileExists(..., true)` çağrıldığını gösterir. Bu çağrının **düşük AL baytı** sıfır değilse2, sıfırsa1döner. Candidate string cleanup ve dönüş yolundaki kalan string cleanup'ları ayrıdır. Model bu aşamaya açık gözlemlerle girer; gerçek dosya sorgusu, GetExeName/ANSI/RTL string davranışı veya path oluşturma yürütmez.

Başlangıç caller'ı detector'ın normal dönüşünü ayrıca ister ve EAX'in yalnız AL baytını `553e46` alanına yazar. Ardından iki ayrı mode okuması yapar:

| Koşul | Önce yazılan DWORD etiketi (`553e48`) | Kurucu | Gönderici context/target projeksiyonu |
|---|---:|---|---|
| İlk mode BYTE =2 | `0x10097f` | `004e4398` | `0x11eaa84` / `0x6241a0` |
| İkinci mode BYTE =1 | `0x1009d4` | `004fd640` | `0x1128a94` / `0x70b360` |

553e48 etiketi burada yalnız sayısal store olarak izlenir; bütün tüketicileri ve anlamı bu kapsamda doğrulanmadı.

İlk koşuldan sonra ikinci mode yeniden okunur. Model bunu tek bir `if/else` kararına indirmez. Açık gözlemlerde ilk değer2, sonraki1ise iki kurucu da sırayla planlanır ve son US projeksiyonu önceki gönderici alanlarını değiştirir. Bu testteki değişim sentetik bir girdi senaryosudur; gerçek oyunda böyle bir mutation gözlenmedi.

Varsayılan API iki taze mode gözlemi ister. `use_owned_mode_reads=True` yalnız **araya değişiklik girmeyen kendi başlangıç state'i** sözleşmesini açıkça seçer. Bu modda kaynakta yeni yazılan AL'den yerel okuma yapılır; aynı aşamaya raw mode verilirse çatışma reddedilir. Canlı global'in değişmediğine dair kanıt olarak kullanılamaz.

Her kurucuda yalnız `+48/+54` iki gönderici alanı projekte edilir. Bu yazımlar sonuçtaki prospective `stores` içinde görünür, fakat kurucunun ayrı normal dönüşü yoksa `complete=False` kalır. Kurucunun diğer yüzlerce alanının modellenmiş olduğu iddia edilmez. Eşleşmeyen mode'da önceki gönderici global'leri uydurulmaz; çıktı yalnız bilinen projeksiyonları taşır.

Detector child eksikse parent normal dönüşü bunu bypass etmez. Detector EAX ile bound detector plan aynı anda verilmez. Dosya varlığı sonucu, helper dönüşü, cleanup ve üst başlangıç çağrısı birbirinden ayrıdır. Dönen `complete` yalnız bu gözlemli dar yolun tamamlandığını anlatır.

**1202benzersiz talimat** güncel Richard dosya baytlarıyla eşleştirildi: detector179talimat, iki tablo kurucusu508/491talimat ve ilgili startup/absolute slot-reference aralıkları. Dört absolute sender-slot mention bulundu; bunlar sadece keşfedilmiş assembly envanteridir. Aliased, hesaplanmış, dış modülden veya dinamik üretilmiş yazıcı bulunmadığı kanıtlanmadı. Byte doğrulama bütün-fonksiyon davranış sertifikası değildir. Kanıt Ghidra/PE audit'idir; REA aracı çıktısı değildir.

Oyun dosyası yolunun yanındaki dosya metadata kontrolünde `KnightOnLine.exe` görüldü, `steam_api.dll` görünmedi. Bu, özgün botun o anda hangi TApplication EXE yolunu kullandığını veya gerçek FileExists sonucunu kanıtlamaz; modelin FileExists gözlemi bununla otomatik doldurulmadı.

**9yeni testle toplam2677 birim testi geçti (6.826s).** AL/fullDWORD farkı, ayrı cleanup ve parent dönüşleri, iki taze mode okuması, değişen mode'larda iki kurucu sırası, eksik constructor dönüşü ve raw/owned çatışmaları sınandı. UI/native C değişmedi; UI son2657aşamasında geçti. Gerçek oyun seçimi, global yazımı, native yürütme ve canlı uyumluluk açık.
