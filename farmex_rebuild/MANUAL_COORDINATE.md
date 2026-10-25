# Koordinata Git: normal callback API

Bu belge önceki5031-test API aşamasını anlatır. Güncel düğme bağlantısı ve
5039-test tam GUI kaydı [MANUAL_COORDINATE_PANEL.md](MANUAL_COORDINATE_PANEL.md)
dosyasındadır. Aşağıdaki bağlanmamış API kapsamı tarihsel aşamaya aittir.

`manual_coordinate.py`, `btnGoKordNormalClick` yordamının004a8478..004a855c
normal gövdesini açık gözlemlerle modeller. Henüz gerçek Git düğmesine bağlı
değildir. Bu API hareket çağrısını yürütmez; otomatik oyun verisi edinmez.

Kaynak form alanları X için+4f8, Y için+4fc'dir. Sıra: exception-frame
kurulumunun normal dönüşü, X geçici Unicode yapımı, GetText dönüşü ve metni,
StrToFloat dönüşü, ayrı post-FSTP binary32 sonucu, X cleanup, aynı adımların
Y için tekrarı, fiziksel Y/X push sırası ve004646b4 hareket çağrısının normal
dönüşü. Hareket isteği görüldüğü hâlde dönüş eksikse sonuç tamamlanmaz.

Normal callback gövdesinde bir uzaklık, HP, koordinat aralığı veya sonlu sayı
kapısı yoktur. Bu, hareket yardımcısında da bu kontrollerin bulunmadığını
göstermez. Ham float bitleri korunur; Python float/locale ayrıştırıcısı
kullanılmaz. NaN payload'ları ve eksi sıfır normalleştirilmez. Kaynak NumbersOnly
özelliği, programatik metin değişikliklerini veya native parser davranışını
kanıtlamaz.

Frame yalnız ulaşılan metinleri, bitleri ve True normal dönüşleri saklar.
X cleanup beklenirken X tekrar okunmaz; Y henüz tüketilmemiştir ve sonraki
gözlemden alınabilir. Tamamlanan invocation tekrar planlanmaz. Bu kendi
devam politikamızdır; gerçek VCL eşzamanlılığı kanıtı değildir.

İki sabitlenmiş Richard PE'sinde136 komut kaydı, yayımlanmış metot kaydı,
iki alan kaydı ve GetText/StrToFloat import kimlikleri doğrulandı.
Yedi CALL hedefi yeni sürümde+1c kaymıştır; modeldeki yordam etiketleri eski
sürümün kanonik adresleridir. Opaque setup/cleanup yardımcısının tüm iç yolları
eşdeğer kabul edilmez. Kaynak: `FarmexBot_koordinata_git_normal_kod_kaniti.json`.
Bu yeni bir REA sağlayıcı çağrısı değildir; korunmuş Ghidra çıktısı ve PE
baytlarının çevrimdışı denetimidir.

Exception-handler boşlukları, parser hataları/locale, managed lifetime,
x87 çalışma zamanı, hareket yardımcısının gövdesi ve gerçek oyun etkileri
bu aşamanın dışındadır. ROTALI GİT düğmesinin korunmuş DFM'de OnClick kaydı
yoktur; yalnız başlığından davranış üretilmez.

Önceki yayımlanan5021-test Pet panel kaydı tarihsel olarak korunur.
Bu API'nin yeni hedefli testleri ve güncel regresyonu ayrı
`MANUAL_COORDINATE_VALIDATION.json` dosyasına kaydedilir. Arayüz bu aşamada
değişmedi; yeni GUI çalıştırılması veya bu API'nin GUI'de doğrulanması iddiası
yoktur.
