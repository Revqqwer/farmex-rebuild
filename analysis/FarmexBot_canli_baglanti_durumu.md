# Canlı bağlantı kanıtları — 25 Ekim 2026

Bağımsız sürümün gerçek oyun verisini otomatik edinmesi ve oyun eylemlerini
göndermesi henüz doğrulanmadı. Yerel model testleri bu eksikleri kapatmaz.

## Kurulu dosyalar

`FarmexBot_kaynak_kimligi_20261025_122636.json` beş dosyanın aynı okuma
sırasında değişmediğini kontrol eder. Loader ve üç bot modülü mevcut analiz
kopyalarıyla bayt düzeyinde eşleşir. Damon ve Richard'ın ham ve çözülmüş
içerikleri birbirinin aynısıdır. Bu sonuç, yüklenmiş süreç görüntüsünü doğrulamaz.

Güncel oyun dosyası 7.018.128 bayt ve SHA-256 değeri
`ecc420d7c0274ef198c8d174007f51eb954507d25b7226a7082d3ad44493706e`.
Okuyucuda bu kimlik için kayıtlı profil yoktur. İki eski oyun kimliğinin
adreslerini yeni dosyaya taşımak için henüz yeterli kanıt bulunmuyor.

Kaynak doğrulama aracı eski oyun kimliğini zorunlu kabul etmek yerine bot
eşleşmesini ve oyun profili durumunu ayrı raporlar. Tarihsel süreç kaydını
güncel oturum kanıtı olarak kullanmaz; tarihli yeni çıktı oluşturur.

## Süreç görünürlüğü

12:21 UTC ölçümlerinde varsayılan araç ortamı 4, masaüstü ortamı 319 süreç
gördü. Her iki envanterde de beklenen oyun adı bulunmadı. Bu gözlem sadece
belirtilen ölçüm zamanına ve görünür süreç adlarına aittir. Araç ortamında
oyunun bulunamaması tek başına masaüstünde oyunun kapalı olduğunu kanıtlamaz.

Bu iki ölçüm oyun handle'ı açmadı, belleği okumadı ve yönetici testi başlatmadı.
Görünürlük farkı geçmişteki erişim reddinin nedenini açıklamaz. Tarihsel
erişim hataları güncel süreçte yeniden ölçülmüş gibi sunulamaz.

## HP/MP tablosu

`FarmexBot_HPMP_tablo_referanslari_20261025_122607.json`, korunan Ghidra
dökümündeki açık mutlak adres referanslarını çözülmüş modül baytları ve
Capstone operandlarıyla karşılaştırır. Yeni bir REA sağlayıcı çalıştırması
veya canlı gözlem değildir.

| Tablo alanı | Doğrudan referans |
| --- | ---: |
| Kök adres yuvası | 241 |
| HP ofseti | 5 |
| Maksimum HP ofseti | 5 |
| MP ofseti | 1 |
| Maksimum MP ofseti | 1 |

253 komutun tamamında ilgili doğrudan bellek operandı okunur; bu kümede
doğrudan yazma bulunmadı. Başlatıcılar tablo alanlarını nesneye göre adreslenen
operandlarla doldurur. Bu nedenle sonuç, tablonun değişmez olduğunu veya
dolaylı/harici yazma bulunmadığını kanıtlamaz. Bot tablosu sabitlerinin
doğrulanması da güncel oyun alanlarının anlamını doğrulamaz.

## Açık işler ve kabul kanıtları

| İş | Mevcut durum | Tamamlanmayı kanıtlayacak gözlem |
| --- | --- | --- |
| Güncel istemci profili | Kayıtlı değil | Aynı oyun kimliğine bağlı kök/alan adresleri ve bağımsız alan doğrulaması |
| Salt okuma erişimi | Bu ölçümde sınanmadı | Güncel oturum kimliğine bağlı başarılı, kapsamı sınırlı okuma |
| HP/MP | Yerel aday okuyucu var | Görünen dört oyun değeriyle zaman uyumlu karşılaştırma |
| Oyun içi yayıncı | Test IPC altyapısı var | Gerçek kaynağı doğrulanmış yayıncı; sentetik veri kabul kanıtı değildir |
| Koordinatlar | Yerel sağlayıcı arayüzü var | Bağımsız konum karşılaştırması ve gerçek sağlayıcı bağlantısı |
| Eylem gönderimi | Yerel kuyruk var | Gerçek taşıma arayüzü ve seçilen işlemin oyundaki sonucu |
| Özelliklerin eşliği | Yerel davranışlar kısmen modellenmiş | Her özellik için kaynak kanıtı ve uçtan uca karşılaştırma |

Bu aşama uygulama kaynaklarını değiştirmez. Önceki 4.990 test ve 1.037
kontrollük arayüz kaydı kendi kapsamlarında korunur; yeni canlı test yapılmış
sayılmaz. Önceki oturumlara ait tek seferlik yönetici testleri tekrarlanmadı.

## Kanıt dosyaları

- `FarmexBot_kaynak_kimligi_20261025_122636.json`
- `FarmexBot_baglanti_hazirlik_20261025_121911.json`
- `FarmexBot_surec_gorunurlugu_default_20261025_122111.json`
- `FarmexBot_surec_gorunurlugu_host_20261025_122115.json`
- `FarmexBot_HPMP_tablo_referanslari_20261025_122607.json`

Ham ikililer ve disassembler dökümü GitHub paketine dahil edilmez. Bunlar
olmadan dosya baytlarının bağımsız yeniden doğrulaması yapılamaz; raporlar
korunan girdilerin kimliklerini ve kontrol edilen komutları kaydeder.
