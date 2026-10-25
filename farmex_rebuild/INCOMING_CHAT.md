# Gelen chat yönlendirmesi ve engelleme sırası

20 Ekim 2026. Güncel exporttaki keşfedilmiş doğrudan çağrılar içinde `00455ec0` chat işleyicisinin tek çağıranı, `004d82a4` içindeki `004d83c5` çağrısıdır. Eski ve güncel Richard'da seçilmiş dispatcher/filtre/producer gövdelerinde **476 talimat kaydı** disk baytlarıyla doğrulandı. Dolaylı veya keşfedilmemiş başka çağıranlar bu taramayla dışlanamaz.

## Kaynak sırası

Dispatcher önce paket opcode'unu `08` ile karşılaştırır. O dal farklı bir kapsamdadır. Ardından opcode'u yeniden okuyup `10` ile karşılaştırır. Chat dalında descriptor `+4` uzunluğu ve `+8` buffer pointer'ı alınır; fiziksel push sırası **uzunluk, buffer, `569220` context** olur. Sonra bütün `00455ec0` işleyicisi çağrılır.

**Chat engelleme kontrolü işleyiciden sonra gelir.** İlk taze kanal BYTE'ı `7` ise engelleme filtresi atlanır. Diğer durumda kanal yeniden okunur ve `00455e0c` çağrılır. Düşük AL sıfır değilse dispatcher'ın kaynak dönüş DWORD'u `0` olur. Bu filtreyi komutlardan önce uygulamak kaynak sırasını değiştirir.

Bu dönüşün gerçek oyundaki görüntüleme veya paket teslim sonucu henüz doğrulanmadı. Model `source_return_dword` üretir; paket hook'u kurmaz, paket düşürmez ve oyuna mesaj göndermez.

## Gerçek checkbox sırası

`frmMain/MainTab/SheetGenel/LwChatBlock`, form `52c` alanıdır. Producer ilk sekiz satırın checked değerini **konumuna göre** okur. Satır caption'ı yönlendirme anahtarı değildir.

| Satır | Katalog caption'ı | Context BYTE offset | Filtrenin eşlediği kanal |
|---|---|---|---|
| 0 | Tümü | 1 | Bütün kanallar |
| 1 | Normal | 2 | 1 |
| 2 | PM | 3 | 2 |
| 3 | Party | 6 | 3 |
| 4 | Clan | 5 | 6 |
| 5 | Shout | 4 | 5 |
| 6 | Merchant | 7 | 14 |
| 7 | Noah Knight | 8 | 34 |

Bu kaynak eşlemesi log bölümündeki kanal etiketleriyle bütünüyle örtüşmez. Örneğin log kanal4 için Shout etiketi kullanırken engelleme filtresinde kanal4'e özel satır dalı yoktur. Bağımsız model kaynak eşlemesini korur; caption adlarına göre düzeltme yapmaz. Dispatcher'daki ilk kanal7 istisnası nedeniyle Tümü satırı seçili olsa bile o çağrıda filtre çalışmaz.

Filtrenin true yolları yalnız AL'a `1` yazar; üst EAX bitlerinin temiz olduğu varsayılmaz. False yol EAX'ı sıfırlar. Çağıran zaten yalnız düşük AL'ı test eder. `ChatBlockPlan.low_al` bu sınırı korur.

## Son kanal5 kontrolü

Filtre erken dönüş üretmediyse kanal bir kez daha okunur. Taze değer `5` ise kaynak offset3'ten WORD sender okur. WORD sıfırsa ek kontrol atlanır. Değilse nesne arama yardımcısı çağrılır; EAX pointer sıfırsa yine normal `1` dönüşüne ilerlenir.

Pointer sıfır değilse taze `554000` offset'i eklenip guarded BYTE yardımcısı `0045dbdc` çağrılır. Düşük AL sıfırsa dispatcher dönüşü `0`, diğer durumda `1` olur. Bu guarded okuyucunun koruma yan etkisi burada uygulanmaz; normal dönüş/EAX gözlemidir. Pointer toplamı 32 bit sarılır. Önceki prelude sender DWORD'u, bu son taze WORD okuması yerine geçirilmez.

## Bağımsız API

`compile_chat_block(rows)` ilk sekiz checked bool'u source konumlarına yerleştirir; caption'ları eşleme için kullanmaz. `plan_chat_block` kararlı bir own flag snapshot'ı üzerinde çalışır. Gerçek context'in çağrı sırasında değişmediği böylece kanıtlanmış sayılmaz.

`plan_incoming_chat(configuration,observation)`, ayrı opcode/descriptor/kanal/WORD/helper EAX değerleri ve normal-dönüş gözlemleri ister. `IncomingChatFrame`, tek çağrının tüketilmiş prefix'ini korur. Son flag okuması eksikse önceki bütün-handler dönüşü ve kanal örnekleri yeniden istenmez. Tamamlanan frame tekrar eylem oluşturmaz; bütün çıktılar zaten inert planlardır.

Bu API henüz deneme arayüzüne bağlı değildir. UI/compiler271 ve envanter dışında251yol sayısı değişmedi. Chat Block listesi API-only olarak etiketlendi.

`whole_chat_handler` ayrı opaque normal-dönüş sınırıdır. Önceki prelude/komut alt modelinin tamamlanması bütün `00455ec0` işleyicisinin döndüğü anlamına gelmez; bu yüzden burada onun yerine kullanılmaz. Handler'ın kalan dalları ve cleanup, hook kurulumu, pointer ömrü ve canlı uyumluluk açıktır. Opcode08 ve chat dışındaki sonraki dispatcher dalları bu modelde açık kapsam boşluğudur.

## Doğrulama

**12 yeni testle toplam 2796 test geçti (6.930 saniye).** Sekiz checkbox satırının 256 kanal üzerinde eşlemesi, channel4 özel dalının yokluğu, düşük BYTE/AL sınırları, handler-before-filter sırası, kanal7 istisnası, taze kanal okumaları, WORD/pointer sıfır dalları, pointer sarılması ve her ulaşılan gözlem eksikliği sınandı. UI/native C değişmedi; UI yeniden test edilmedi.

Kaynak kanıtı: `outputs/FarmexBot_chat_yonlendirme_kaniti.json`; üretici: `work/audit_incoming_chat.py`. Bu korunmuş Ghidra/PE kanıtıdır; yeni REA Evidence veya canlı oyun yürütmesi değildir. Uygulama kanıtı `INCOMING_CHAT_VALIDATION.json` dosyasındadır.
