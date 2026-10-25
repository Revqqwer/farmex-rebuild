# Ban Notice dalının pasif kaynak çözümlemesi

21 Ekim 2026. `00457014..0045730e` bölümünün181talimatı ve `0041ac60` arama yardımcısının74talimatı eski/güncel kaynak PE'lerinde incelendi: toplam510dosya-baytı doğrulanmış kayıt. `work/audit_chat_notice_tail.py` exact branch/store/call noktalarını, dört literal'i ve import rollerini kontrol eder. Kaynak `outputs/FarmexBot_chat_bildirim_pasif_kaniti.json`; korunmuş Ghidra/PE kanıtıdır, yeni REA Evidence değildir.

Bu aşama pasif analizdir. `ChatHandlerSegmentsFrame` bu bölümü hâlâ desteklenmeyen tail olarak durdurur. Hiçbir yanıt otomasyonu eklenmedi; süreç, oyun veya ağ eylemi çalıştırılmadı.

## Giriş ve eşleşme

Taze kanal BYTE'ı7değilse doğrudan ortak temizliğe gidilir. Kanal7ise `illegal software` literal'inin uzunluğu `char_traits::length` ile alınır; mesaj nesnesinde başlangıç konumu0dan `0041ac60` aranır. Raw EAX `FFFFFFFF` ise eşleşme yoktur ve ortak temizliğe gidilir. Başka bir raw index eşleşme yoluna girer; kaynak burada ek negatif signed-index filtresi yapmaz.

Arama gövdesi descriptor uzunluğu/kapasitesini okur, kapasite10hex altındaysa inline veri, diğer durumda pointer kullanır; `char_traits::find/compare` rollerini çağırır. Index veyaFFFFFFFF döndürür. Bu gövdede casefold/lowercase çağrısı görülmedi. Bundan tüm CRT/locale davranışının veya malformed/aliasing string'lerin çözüldüğü sonucu çıkarılmaz.

## İşlem ayarından önceki etkiler

Eşleşmede context+340hex DWORD sayacı artırılır.561f55 ve561f54baytlarının ikisi de açıksa UI sayı güncellemesi ve `danger` sınıfıyla log çağrısı hazırlığı yapılır. Ardından `GetTickCount` EAX'i context+338hex'e yazılır; context+33chex sıfırlanır. Bu iki DWORD birlikte sıfırla genişletilmiş tick değeridir.

56913b alarm bayrağı açıksa `Default` alarmı için `00404260` çağrı hazırlığı ve geçici nesne temizliği vardır.569139 işlem enable kontrolü bütün bunlardan sonra gelir. Dolayısıyla enable kapalıyken counter/timestamp ve açık alarm adımları atlanmış sayılmaz.

56913a filtre bayrağı açıksa geçici nesne hazırlığıyla `0046cd1c` çağrılır. Sonucun yalnız düşük AL'si değerlendirilir:0ortak temizliğe çıkar, nonzero seçeneklere devam eder. Bu audit filter gövdesini çözmez; liste üyeliği, kullanıcı adı veya parser davranışı bu çağrı sınırından varsayılmadı.

## Chat dalındaki seçenekler

Her karşılaştırma56913cDWORD'unu yeniden okur. Tek sabit mode snapshot'ı kaynak eşzamanlılığı olarak varsayılmamalıdır.

| Karşılaştırılan değer | Bu chat dalında görülen çağrı yolu |
|---|---|
| 0 | `004c7e0c(561ef8)` DC yardımcısı |
| 1 |561f60açıksa `0040ae0c` fiziksel `(0,561f34)`, sonra `00465678`;569140açıksa `004c8498` fiziksel `(DWORD[562074],561ef8)` |
| 2 |561f6caçıksa `Notice` literal'i ve5687a8ile opaque `004ebcbc` çağrı hazırlığı |
| 3 | Bu chat bölümünde yanıt çağrısı yapmadan ortak temizliğe geçer |
| 4 | `GetCurrentProcess`, ardından mevcut süreç için `TerminateProcess(handle,0)` hazırlığı |
| Diğer | Ortak temizliğe gider |

Mod3için başka bir işleyicide (`0045a05c`)569139/56913creferansı bulundu; bu rapor oradaki Genie/delay işleyişini çözmez. Chat dalındaki çağrı yokluğu bütün özellikte etki yokluğu değildir. Benzer biçimde4c8498ve4ebcbcalt yardımcılarının tam anlamı burada çağrı ismi veya panel caption'ından türetilmedi.

Self `TerminateProcess` başarıyla çalışsaydı süreçte ortak temizliğe normal dönüş beklenmezdi. Kaynakta böyle bir çağrının bulunması onun çalıştığını veya başarılı olduğunu kanıtlamaz. Bu yol normal-cleanup completion receipt'iyle otomatik birleştirilemez.

## Arayüz ilişkisi ve sınır

Korunmuş form kataloğunda Koruma > `grpNoticeKontrol` başlığı “Ban Notice Kontrolu”, enable/alarm/liste filtresi, DC/Town/rota/Genie/oyunu kapat seçenekleri ve ayrı `frmNoticeNickList` formu vardır. Bunlar paketlenmiş kontrollerin varlığını gösterir. Her field'in producer→global bağının bu audit ile bütünüyle eşlendiği iddia edilmez.

Runtime kodu/UI/native C değiştirilmedi; yeni test veya UI koşusu yoktur. Son tam koşu2938testtir; bu pasif analizin native davranış kanıtı değildir. Oyun bildirimi yakalanmadı, anti-cheat üreticisi veya olayın gerçek kaynağı dosya literal'inden çıkarılmadı. Full-handler, alt-helper etkileri ve canlı uyumluluk açık kalır.
