# Chat/PM parti daveti: ulaşılan dal ve bağımsız kuyruk modeli

19 Ekim 2026. `chat_party_invite.py`, güncel Richard içindeki `00456804..004569d6` davet dalını modeller. Giriş bu dalın **ulaşıldığına ilişkin açık varsayımdır**; önceki chat komutlarının veya tüm `00455ec0` fonksiyonunun çalıştırıldığı anlamına gelmez.

`compile_chat_party` üç panel değerini (`chinvitechat`, `txtinvitechat`, `chPartyChatInviteListControl`) ve ortak PartyList isimlerini açık Windows kod sayfasıyla okur. Kaynak caption/text → ANSI → char* zincirindeki NUL kesilmesi korunur; checked durumu isimleri elemez. Kayıplı dönüşüm reddedilir. Compiler artık EnginePage **Chat/PM Party** denemesine `ChatPartyTrial` üzerinden bağlıdır; [UI kapsamı](CHAT_PARTY_UI.md).

`parse_chat_prefix` dışarıdan sağlanan opcode10 baytlarını sınır kontrollü ayrıştırır. Gönderen DWORD konumu3, isim uzunluğu BYTE konumu7, mesaj uzunluğu konumu8+isim_uzunluğu, mesaj başlangıcı10+isim_uzunluğu şeklindedir. İsim ve mesaj C-string gibi ilk NUL'da kesilir. Tam başlık aralığı, sıfır uzunluklu mesajda da yerel parser politikası olarak istenir; bu davranış vendor'ın bozuk paket/taşma davranışı değildir. Ayrıştırma native malloc/memcpy/string dönüşlerinin kanıtı sayılmaz.

`plan_chat_party` kanal3'ü, kapalı ayarı, tam eşleşmeyen komutu ve kendi karakter ID'sini eler. Karşılaştırmada trim/casefold yoktur; self kontrolü WORD değil tam DWORD'dur. Yalnız liste kısıtlaması açıkken `004cbecc` filtresine gidilir. Bu sıra incoming parti kabul modelindeki filtreyi her zaman değerlendirme davranışından farklıdır. Filtre raw EAX'in düşük BYTE değeri veya açıkça seçilmiş sabit bağımsız isim listesi olabilir. Argüman kurulumları, karşılaştırma, actor, filtre ve davet yardımcısı normal dönüşleri ayrı gözlemlerdir.

`ChatInviteEmissionFrame`, `004ca694` yardımcısının iki yerel enqueue adımını ayırır: `2f03 + isim_uzunluğu_WORD + isim_baytları`, ardından aynı tamponun ikinci baytını01 yapan kayıt. Bağlantı kontrolü ve tick her çağrı için ayrıdır. İlk kontrol tüketildikten sonra tick eksikse bu kontrol tekrar okunmaz. Birinci kayıt veya normal dönüş tüketildiyse sonraki eksiklikte tekrarlanmaz. Gate0 bilinen bir atlamadır. İki enqueue normal dönüşü, string temizliği ve üst davet yardımcısı dönüşü ayrı kalır.

Kaynak tampon `EBP-90`, cursor `EBP-2c` konumundadır. Başlık4bayt olduğundan isim96baytı aştığında kopya cursor alanıyla çakışır. Model yalnız çakışmayan aralığı üretir; daha uzun ismi kesmez veya başarı saymaz, açık kanıt boşluğu döndürür. Kaynağın bu alandaki bozuk stack davranışı çözülmüş değildir.

`ChatPartyInvitationFrame` yapılandırmayı/mesajı bir çağrı için sabitler ve yalnız ulaşılan gözlemleri tüketir. Kuyruk çalışması başlamadan önceki eksik actor/filtre/argüman dönüşü hiçbir kayıt oluşturmaz. Bound planın hedef ismi kontrol edilir; başka isme ait veya tamamlanmamış child plan üst normal dönüşle bypass edilemez.

API aşamasında18yeni test eklenmişti; sonraki UI adaptörü9test ekledi. **Güncel toplam2657 birim testi geçti (8.215s).** Tam gizli UI1037kontrol/11form/18ana sekmede geçti. Testler gerçek oyun yakalaması, gerçek enqueue veya gönderim değildir. Disk kanıtı528benzersiz talimatı kapsar; kaynak Ghidra/PE kontrolüdür, REA aracı çıktısı değildir. Tüm fonksiyon/native çağrı/ağ teslimi/parti üyeliği ve canlı uyumluluk sertifikası yoktur.

Yerel kullanımda önce `parse_chat_prefix(captured)` sonucu kontrol edilir; ulaşılan dalın bağımsız denemesi için `ChatPartyInvitationFrame(config, prefix.message)` kullanılır. `advance` çağrısı yalnız ayrı gözlemlerle ilerler. Hiçbir sınıf oyuna bağlanmaz veya mesaj göndermez.
