# Satış hazırlığında oturum ve ürün yanıtı bekleme

18 Ekim 2026: `merchant_sell_prepare_wait.py`, aşama 3'ün ready/item bekleme
dallarını verilen gözlemler üzerinde planlar. `MerchantSnapshot.sell_prepare_wait_inputs`
ile runner'a bağlanır. Workbench'in varsayılan kapalı gözlem modu aşağıda açıklanır.

İlk okunan ready BYTE +38'dir. Sıfırsa ürün pending'i, prepared slot sayısı ve
seçim girdileri okunmadan oturum damgası QWORD +40 üzerinden beklenir. Ready
nonzero ise item pending BYTE +28 okunur. Bu da sıfırsa seçim yoluna geçilir;
bekleme tick'i veya damgası gerekmez. Nonzero pending için ayrı QWORD +30
ürün damgası kullanılır. İki damga birbirinin yerine konmaz.

Her iki bekleme dalında GetTickCount DWORD sıfır genişletilir; QWORD damga
SUB/SBB ile çıkarılır. Signed64 fark >=10000 ise zaman aşımı dalına girilir.
DWORD saat sarması unsigned32 elapsed'e dönüştürülmez; negatif fark bekler.
Damganın üst DWORD'u yok sayılmaz. Bu hesap aşama 6 izlemesinin signed32
hesabından ayrıdır.

Zaman aşımında kaynak önce mesaj/gösterim/cleanup dalını tamamlar, sonra
`0040ae0c(0x561f34,0)` çağırır. Ayrı normal dönüş gözlemleri gerekir:

| Bekleme | Mesaj span'ı | Stop çağrısı |
|---|---|---|
| Ürün | 0042197b..004219e7 | 004219f1 |
| Oturum | 00421ae2..00421b4e | 00421b58 |

Stop dönüşü tek başına eksik mesaj dönüşünü atlayamaz. Plan prefix çağrılarını
gösterir; native mesaj veya stop etkilerini gerçekleştirmez. İki dönüş sonrası
runner'ın `sale_item_timeout` / `sale_session_timeout` ile durması kendi
orkestrasyon politikasıdır; helper iç etkilerinin emülasyonu değildir.

Runner producer bayraklarının gözlemle eşleşmesini ve seçilen damganın kendi
phase/item damgasıyla tutarlı olmasını ister. Eksik gözlemde legacy monotonic
saat hesabına düşmez. Bekleme dalında kaynakta daha sonra okunan prepared
slot sayısı istenmez. `selection_path` yalnız sonraki kapının açılmasıdır;
seçim, paket, oyun başarısı veya bütün aşamanın tamamlanması değildir.
Plan bir invocation içindir; native thread/callback devam ettirildiği iddia edilmez.

`work/audit_sell_prepare_wait.py`, iki sabit hash'li dosyada **198 talimat
kaydının** baytlarını doğrular. Ready/pending branch önceliği, iki farklı
damga, clock import kimliği, signed/unsigned branch dizisi ve mesajdan sonra
stop sırası ayrı kontrol edilir. Rapor:
`outputs/FarmexBot_satis_hazirlik_bekleme_kod_kaniti.json`.
Ghidra statik kanıtıdır; REA Evidence veya native yürütme değildir. Mesaj/stop
gövdeleri, ortak epilog ve callback eşzamanlılığı açık kalır. Örtüşen audit
kayıtları benzersiz toplam kapsam olarak toplanmaz.

13 yeni test ile tam Python çalıştırmasında **1919 test geçti** (6.948 saniye).
Birleşik satış modeli artık oturum ve ürün beklemelerini ayrı açık ham saat
örnekleriyle geçirir; sağlanan yanıt örneği pending'i temizledikten sonra seçim
yoluna döner. Kuyruk iki yerel kayıttır. Bu örnekler canlı yakalama veya server
ACK'sı değildir. UI düzenlenmedi; genel UI smoke tekrar çalıştırılmadı.
Gerçek producer/mesaj/stop etkileri ve canlı uyumluluk doğrulanmadı.

## Deneme arayüzü

`Sell Merchant` denemesinde **Satış yanıtı beklemesini örnekle** seçeneği yeni
denemeye alınır. JSON yalnız aşama 3'e ulaşıldığında okunur. `{}` hazır bayrağını
bilinmiyor bırakır; genel **Deneme işlem kapısı açık** kutusu bunun yerine geçmez.

Alanlar `ready_byte`, `item_pending_byte`, `tick_dword`, `session_stamp_qword`,
`item_stamp_qword`, `message_span_returned`, `stop_returned` şeklindedir.
Ham sayılar JSON tam sayısı, dönüşler `true`/`false` olmalıdır. Bilinmeyen alan
adları reddedilir. Henüz erişilmeyen değerler okunmaz: örneğin ready 1/pending 0
ile `tick_dword` istenmez; eksik tick varken damga ve timeout dönüşleri okunmaz.
Yalnız erişilen alanların tipleri doğrulanır. Oturum/ürün damgası, çıktıdaki kendi
yerel caller damgasıyla eşleşmelidir; otomatik oyun saati veya canlı bellek örneği
üretilmez. Yeni eksik gözlem önceki tamamlanmış planla doldurulmaz.

Örneğin `{"ready_byte":1,"item_pending_byte":0}` yalnız seçim yolunu açar;
gerçek oturum/ürün yanıtının geldiğini kanıtlamaz. Timeout mesaj ve stop dönüşü
örnekleri de native yardımcıları çalıştırmaz. Ayarın deneme sırasında değiştirilmesi
mevcut denemenin seçimini değiştirmez; yeniden başlatılan denemede alınır.

`work/verify_sell_prepare_wait_ui.py`, kendi arayüzünü gizli kurarak flag,
clock, branch, iki bağımsız timeout dönüşü, lazy alanlar ve reset davranışlarını
sınar. Orijinal panel veya oyuna dokunmaz. Önceki satış maliyeti arayüz kontrolü
de geçti. Üç parser testiyle güncel tam sayı **1922 test** (7.697 saniye);
önceki 1919 sayısı çekirdek model değişikliğinin tarihsel çalıştırmasıdır.
Genel UI smoke bu aşamada tekrarlanmadı; hedefli kontrol layout görsel onayı değildir.
