# Chat komutları: sekiz dalın karar modeli

Sonraki UI entegrasyonu:16alan artık Chat Komutları denemesinden tüketiliyor. Güncel toplam2717 test ve tam gizli UI geçti. Aşağıdaki API-only notları ilk aşamanın kapsamıdır. [Güncel UI bağı](CHAT_COMMANDS_UI.md).

20 Ekim 2026. `chat_commands.py`, Diğer > Chat Komutlarına Göre İşlem Yap grubundaki16flag/text alanını derler ve yalnız **ulaşılmış `004565c9..00456804` dalını** modeller. Önceki chat dalları ve bütün mesaj handler'ının dönüşü bu kapsama dahil değildir. Oyun, süreç, klavye veya native hedef üzerinde işlem yapılmaz.

| Kaynak sırası | Komut | Çağrı planı | Push sırası |
|---:|---|---|---|
| 1 | Karakter DC | `004c7e0c` | `561ef8` |
| 2 | Merkeze dön | `004646b4` | Y float bitleri, X float bitleri |
| 3 | Bot başlat | `0040ae0c` | `1`, `561f34` |
| 4 | Bot durdur | `0040ae0c` | `0`, `561f34` |
| 5 | Genie başlat | `00466cc4` | `1` |
| 6 | Genie durdur | `00466cc4` | `0` |
| 7 | Kalk | `004c8d48` | `561ef8` |
| 8 | Town | `00465678` | argüman yok |

Her dal önce mesajı ayarlı string'le karşılaştırır, sonra checkbox byte'ını kontrol eder. Checkbox kapalı olsa da karşılaştırmanın normal dönüşü gerekir. Karşılaştırma tam byte/uzunluk eşitliğidir; trim/casefold yoktur. Sekiz dal bağımsızdır; aynı keyword birden çok açık komuta atanmışsa birden fazla action intent'i oluşabilir. İlk eşleşmeden sonra otomatik çıkış eklenmedi.

Genie başlatmada `561f6f` BYTE sıfır olmalı, `004631c8` sonucunun AL'si sıfır olmalı ve `004631e8` sonucunun AL'si pozitif/nonzero olmalıdır. Kaynak remaining değeri byte olarak zero-extend eder; signed DWORD karşılaştırması uydurulmaz. Durdurmada ayrı, taze `004631c8` sonucu kullanılır ve AL **tam1** olmalıdır. Her native/helper normal dönüşü ayrı gözlemdir; başlatmanın state sonucu durdurma için tekrar kullanılmaz.

Merkez hareketi önce `562004` Y DWORD'unu signed FILD ile, sonra `562000` X DWORD'unu okur. Her biri ayrı FSTP float dönüşümünden sonra stack'e girer. Model DWORD ve post-FSTP binary32 bitlerini ayrı ister; x87 control/rounding varsaymaz ve varsayılan Python float sonucunu kaynakla eşit saymaz.

`ChatCommandsFrame` bir çağrının stable own config/mesaj snapshot'ını ve yalnız tüketilmiş gözlem önekini korur. Eksik sonraki normal dönüşte önceki action intent'leri kaybolmaz veya aynı sonuç listesinde çoğalmaz. Tamamlanmış frame yeni komut çalıştırma yerine aynı sonucu döndürür. Yeniden gelen gerçek mesaj ayrı frame gerektirir. Intent listesi bir eylem yürütücüsü değildir.

`compile_chat_commands` açık `WindowsNameCodec` ile lossless Unicode→ANSI dönüşümü yapar ve kaynak char* zincirindeki NUL kesilmesini korur. Bu bağımsız kod sayfası politikası gerçek RTL/VCL/codepage davranışının tamamını doğrulamaz. Kaynak producer flag alanları `+9..+10`, string alanları `+18,+40,+68,+90,+b8,+e0,+108,+130` olarak eşlendi. Parametre-context ofsetleri farklı fonksiyon nesnelerine genellenmez.

**818benzersiz talimat**,16published field/method kaydı ve sekiz runtime karşılaştırma source PE baytlarıyla doğrulandı.16olayın ortak `00454cb0` üreticisine ve `569220` context'ine gittiği kontrol edildi. Önceden doğrulanmış string-length/compare kanıtı ayrıca referanslandı. Bu Ghidra/PE analizidir, REA aracı çıktısı değildir.

**12yeni testle toplam2709 birim testi geçti (6.977s).** Sekiz farklı çağrı/push sırası, aynı keyword ile tüm dallar, kapalı checkbox karşılaştırması, Genie koşulları, Y/X okuma ve signed FILD, eksik action dönüşü, önekten devam ve kod sayfası/NUL davranışı sınandı. UI/native C değişmedi; bu tur UI/native fixture tekrar çalıştırılmadı.

UI compiler envanteri255olarak kaldı.267düzenlenebilir yolun16'sı artık bilinen command API-only olarak işaretlendi; bu sayı eksik/tamamlanmış özellik adedi değildir. Helper gövdelerinin gerçek etkileri, native float/string/context durumu, öncesindeki chat reachability ve canlı eşdeğerlik açık kalır. Bu dal içinde yeni kanal/self/auth filtresi eklenmedi; önceki handler'ın tüm giriş koşullarının yokluğu sonucuna varılmaz.
