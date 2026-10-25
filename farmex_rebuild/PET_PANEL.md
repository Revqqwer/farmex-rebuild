# Pet paneli ile karar motorunun yerel bağı

Bot sekmesindeki altı Pet kontrolü `PetTrial` üzerinden ayar üreticisine ve
Pet karar modeline bağlanır. Davranış denemelerindeki Pet seçeneği bu bağı
önizler. Kaynak modellerin kapsamı `PET_BEHAVIOR.md` içinde açıklanır.

İlk örnek alanı ayar üreticisinin normal/parse/cleanup gözlemlerini taşır.
İkinci alan çalışma yordamının yakalanmış helper, FPU ve saat gözlemlerini
taşır. Örnek hazırlama düğmesi kendi panelinden açıkça sentetik veri üretir;
oyuna bağlanmaz veya gerçek helper dönüşü iddia etmez.

## Bağın davranışı

- Altı kontrol dört ayar alanını üretir. Saldırı, Guard ve Loot sırası kaynak
  önceliğidir. Hiçbiri seçili değilse önceki bilinen mod korunur; önceki mod
  bilinmiyorsa çalışma o okumada bekler, sıfır mod üretilmez.
- İç parser, dış dönüş ve cleanup bağımsızdır. Cleanup beklerken bilinen
  ayar yazımları korunur; kendi çalışma frame'imiz ayarlar tamamlanınca başlar.
- Bir çalışma örneği yalnız ulaşılan değer ve True dönüşleri tüketir. Örneğin
  summon dönüşü beklerken daha önce oluşan üç alan yazımı korunur; devam
  edildiğinde aynı saat tekrar üretilmez.
- Panel özeti örnek özetiyle eşleşmelidir. Panel değiştirilirse eski örnek
  reddedilir. Bir örneğin tüketilmiş girdileri sonradan değiştirilemez.
- Her çalışma örneğinin artan bir numarası vardır. Tamamlanan numara aynı
  sonucu korur; eski numara başka bir çağrı olarak yeniden kullanılamaz.
- Kendi timer yazımları sonraki örneğe aktarılır. Ham örnek bilinen kendi
  timer veya ayar alanını başka değerle değiştiremez.
- Profil yüklemesi farklı bir document nesnesi oluşturduğunda Pet durumunu
  ve timer'ları temizler. Yeni profil aynı değerlere sahip olsa bile eski
  çalışma numarası reddedilir. Açık önizleme sıfırlaması numara alanını da sıfırlar.

Bunlar kendi tek-thread UI'mızın yaşam döngüsü politikalarıdır. Kaynak worker
API'si taze alanları bağımsız gözlemler olarak modellemeye devam eder; kendi
panelin bir çağrı boyunca sabit tutulması native thread/yarış eşliği değildir.
Çağrı ve yazım planları sadece Python nesneleridir; oyun belleğine veya
sunucuya gönderilmez. Normal helper dönüşü bir oyun işleminin başarı ACK'i
olarak yorumlanmaz.

## Doğrulama

13 bağlantı regresyonu ve bütün önceki testlerle toplam 5.021 Python testi
geçti. Yeni tam gizli GUI testi gerçek altı kontrolü, cleanup bekleme/devamını,
mod/çıkarma/besleme yollarını, tamamlanmış örneğin değişmezliğini ve gerçek
profil yükleme yolunda aynı-değer document değişimini doğrular. Önceki 648
komut kaydı iki PE'de yeniden kontrol edilir. Compiler envanteri 385 giriş,
dışarıda kalan düzenlenebilir yol sayısı 138 olur; bu sayılar tamamlanmış
özellik sayısı değildir.

`PET_PANEL_VALIDATION.json` kod ve test hash'lerini kaydeder. Otomatik Pet
veri edinimi, native callback/VCL/RTL/SEH davranışları, gerçek taşıma arayüzü
ve canlı oyun eşliği hâlâ doğrulanmamıştır. Önceki HP/MP native fixture deneyi
ayrı kapsamdır ve Pet kodunun native çalışması sayılmaz.
