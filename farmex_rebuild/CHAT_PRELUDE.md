# Chat komutlarından önceki giriş ve log bölümü

20 Ekim 2026. `chat_prelude.py`, `00455ec0..004565c9` normal yolunu ve Chat Log bayrağının producer bağını modeller. Eski/güncel kaynakta prefix'in **469'ar talimatı**, producer'ın flag bölümü ve güncel published event dahil **966 talimat kaydı** disk baytlarıyla doğrulandı. Bu Ghidra/PE/CFG kanıtıdır; yeni REA Evidence veya canlı yürütme değildir.

## Kaynakta bulunan koşul

`frmMain/MainTab/sheetInfoLog/chChatInfoLog`, form `1014` alanıdır; `00454cb0` bunun düşük AL değerini context'in ilk BYTE'ına yazar. Bu BYTE sıfırsa `004560c8` doğrudan komut girişine (`004565c9`) atlar. Başlatma, Town veya başka bir chat komutunun çalışması için Chat Log açık olmak zorunda değildir.

Log açıkken kanal 1..6, 14 veya 34 ise log çağrısı hazırlanır. Diğer kanallarda log çağrısı atlanır; normal dönüş/cleanup sonrası komutlara yine ulaşılır. Bu prefix içinde normal erken `RET` veya komutları reddeden kanal çıkışı yoktur. CFG'deki bütün normal ilerleme/atlama yolları komut girişinde birleşir. Bu sonuç **yürütülen bütün çağrıların normal döndüğü varsayımına bağlıdır**; allocation/string hataları veya exception yolu için bir garanti değildir.

| Kanal | Kaynak label |
|---|---|
| 1 | All |
| 2 | PM |
| 3 | Party |
| 4 | Shout |
| 5 | Clan |
| 6 | Boş label |
| 14 | Merchant |
| 34 | Noah Knights |

Kanal 6 izin verilen aralıkta olmasına rağmen ona label atayan dal yoktur; ilk boş string korunur. Otomatik bir kanal adı uydurulmaz.

## Bağımsız normal yol

Model önce `input_copy_and_sender_parse`, `text_buffers_prepare`, `message_objects_construct` normal sınırlarını ister. Kaynak allocation/memcpy/helper/string yürütmesi bu makbuzlarla emüle edilmiş sayılmaz. Mesaj, var olan bounded own parser'dan gelir: sender DWORD offset3, name length BYTE7, message length BYTE `8+name_length`, message başlangıcı `10+name_length`. Parser'ın boyut kontrolleri kendi politikamızdır; kaynak kod bu girişte aynı güvenli malformed-packet reddini yapıyor diye sunulmaz.

Log açıkken `log_strings_construct` gerekir. Seçilen kanalda varsa `log_label_<kanal>`, sonra `log_assembly` gerekir. Kendi bounded byte projeksiyonu `[label] isim : mesaj` biçimindedir; örneğin kanal6 için `[] Alice : go`. Native string/helper semantiği yalnız bu projeksiyona bakılarak tamamlanmış sayılmaz: ayrıca aynı immutable byte dizisini içeren `assembled_log_bytes` gözlemi gerekir.

`log_sink` normal dönüşü ayrı istenir. Kaynak `00405738` çağrısının hedef context'i `561f34`, kategori string'i boştur. Yardımcının kendi koşulları logu atlayabileceğinden normal dönüş, logun görüntülendiğini veya saklandığını kanıtlamaz. `log_line_cleanup` ve `log_strings_cleanup` da ayrı kalır. Hiçbir gerçek sink'e mesaj gönderilmez.

`ChatPreludeFrame`, bir çağrıdaki tüketilmiş normal dönüşleri ve assembled snapshot'ı korur. Son cleanup eksikse eski logu tekrar hazırlamaz veya yayımlamaz; sonuçlar zaten inert intent'tir. Tamamlanan aynı frame tekrar kullanıldığında yeni intent eklenmez.

## Komut zincirine bağ

`ChatCommandEntryFrame(configuration,captured,chat_log_byte)`, bounded prefix → prelude → mevcut command frame sırasını izler. Prelude bitmeden command gözlemleri tüketilmez; olumlu `action:*` makbuzları prelude boşluğunu aşamaz. Prelude bittikten sonraki komut boşluğunda önceki prelude tekrar gözlenmek zorunda değildir.

Bu yeni birleşim API düzeyindedir. Mevcut Chat Komutları arayüzü henüz bu prelude'ü kullanmaz; önceki açıkça ulaşılan komut denemesi devam eder. `compile_chat_log(values)` gerçek checkbox snapshot'ını alabilir; bu kontrol henüz UI/compiler envanterine eklenmedi.

Kaynak handler'a çağıran yönlendirme, gerçek paket capture ömrü, eşzamanlı değişen orijinal/copy buffer değerleri, handler'ın komut sonrası bütün dalları, hatalar ve canlı eşdeğerlik açıktır. Bu giriş birleştirmesi bütün handler'ın çözüldüğü anlamına gelmez.

Kaynak kanıtı: `outputs/FarmexBot_chat_on_giris_kaniti.json`; üretici: `work/audit_chat_prelude.py`. Test/model kayıtları ayrı `CHAT_PRELUDE_VALIDATION.json` dosyasındadır.

## Doğrulama sonucu

**12 yeni testle toplam2784 test geçti (7.162 saniye).** 256 kanalın log açık/kapalı normal yolu, boş6label, exact assembled snapshot, her normal dönüş eksikliği, prefix cache ve command gözlemlerinin prelude bitmeden tüketilmemesi sınandı. UI/native C değişmedi ve UI yeniden test edilmedi. Compiler271, envanter dışında251yol aynı; Chat Log bunlardan API-only olarak etiketlenen tek yeni alandır. Bu sayılar özellik tamamlanma yüzdesi değildir.
