# İsim CFG içe/dışa aktarımı

18 Ekim2026. `name_cfg_codec.py` ve panel, doğrulanmış normal text/BOM
dalları için yerel CFG okuma/yazma sunar. Orijinal klasör otomatik aranmaz
ve değiştirilmez; kullanıcı dosyayı seçer. Tam native/fallback ve canlı
uyumluluk bundan çıkarılmaz.

## Kanıt

Sabit RTL BPL'nin500AC000..50160000 file-backed aralığından737280 baytlık
adres bağlı carrier çıkarıldı. Her instruction hem carrier'a hem orijinal
PE'ye eşleştirildi. BinaryLoader image-base metadata'sı0 kalsa da gerçek
block ve talimatlar500AC000 tabanındadır; her adres ayrıca denetlendi.
14constructor/default/preamble/prefix metodu ve önceki encoding detector
toplam648 talimat kaydında doğrulandı. İş14complete/0missing/0failed ile
terminal oldu. BPL çalıştırılmadı; bu yerel Ghidra kanıtıdır, REA Evidence
veya oyunda yüklü runtime kimliği değildir.

Rapor `outputs/FarmexBot_isim_CFG_codec_kod_kaniti.json`; carrier kaydı
`outputs/FarmexBot_RTL_liste_varsayilan_carrier.json`; üretici
`work/audit_name_cfg_codec.py`.

Base TStrings kurucusu CRLF ve flags0E yazar. GetANSI ilk nesnesini
kernel32.GetACP ile oluşturup cache'ler. Panel yalnız kendi host ACP'sini
ölçer; oyunun cache'i veya private Items subclass'ı ölçülmüş sayılmaz.
BOM sırası UTF8/UTF16LE/UTF16BE; literal EFBBBF/FFFE/FEFF ve prefix byte
karşılaştırması doğrulandı. Explicit encoding yalnız kendi BOM'unu atlar.
BOM olmayan UTF8 kendiliğinden tahmin edilmez; açık codepage kullanılır.

## Codec ve panel

`decode_name_cfg` geçerli UTF8/UTF16 ve kayıpsız byte roundtrip sağlayan
MBCS verisini destekler. Bozuk Unicode, kayıplı dönüşüm ve özel delimiter
unresolved döner. RTL'nin replacement/best-fit/locale/exception yolları
tam emüle edilmiş değildir. Export flags2/4 ile preamble ve son satır
sonunu belirler. Gömülü NUL length-based export'ta kalabilir; yeniden
SetTextStr import'u NUL'da durabilir. Her satır için kayıpsız roundtrip
genellemesi yapılmaz.

`read_name_cfg` explicit absolute local path ve own1MiB bütçesi kullanır.
`write_name_cfg` dönüşüm başarılıysa temp+replace ile atomik yazar. Bu own
yazma politikası native yarım yazma davranışını yeniden üretmez. Kayıplı
export mevcut dosyaya dokunmaz. Testler yalnız kendi geçici dosyalarını
kullanır; runtime/BPL/credential dosyaları source ZIP'e girmez.

Panelde liste seçimi, BOM'suz dosya codepage alanı ve **CFG aç/kaydet**
düğmeleri vardır. Import kaynak004603fc gibi seçilen listeyi **önce
temizler**; dosya açılamazsa boş kalır. Diğer liste korunur. Dialog iptali
işlem çağırmaz. Başarılı import encoding metadata'sını o liste için mevcut
oturumda tutar; export her zaman güncel satırlarla kullanır. Clear encoding
metadata'sını silmez. JSON profile yalnız Unicode satırları gider; CFG
encoding metadata'sı profile yazılmaz ve profile bind'da sıfırlanır.

14yeni test dahil **2339 test geçti (7.623 saniye)**; ilgili34 test geçti.
Üç BOM, Türkçe ANSI, açık/default codepage, bozuk veri, duplicate/space,
NUL, boş/BOM, flags, bütçe, missing-file ve atomik eski dosya koruma sınandı.
Tam gizli UI1037kontrol/11form/18sekmede geçti. Son Clear-before-open
düzeltmesinden sonra odaklı isim/CFG UI testi tekrar geçti: liste izolasyonu,
missing sonrası boş liste, yeniden import ve aynı BOM ile export doğrulandı.

Gerçek yüklü runtime/cache/subclass, native invalid/fallback davranışı,
tüm orijinal profil zinciri ve canlı uyumluluk açık. Oyun belleğine veya
ağına erişilmedi; orijinal bot modülü çalıştırılmadı.
