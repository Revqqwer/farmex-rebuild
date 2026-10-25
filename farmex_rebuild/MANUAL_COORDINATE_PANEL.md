# Koordinata Git panel bağı

Gerçek `btnGoKordNormal` düğmesi artık `OwnedManualCoordinate` üzerinden
normal callback modelini kullanır. X/Y Text alanları yalnız kaynak getter
çıktısına ulaşıldığında panel belgesinden okunur. X alınmışken cleanup
beklerse X korunur; henüz alınmamış Y daha sonraki panel değeridir.

Kurulum, getter, StrToFloat, cleanup ve hareket normal dönüşleri açık bir
sağlayıcıdan gelir. Parse sonucu post-FSTP binary32 bitleriyle ve aynı anda
kullanılan metinle eşlenir. Sağlayıcı panel metnini değiştiremez veya henüz
alınmamış ekseni dolduramaz. Python locale/float ayrıştırıcısının kaynak RTL
eşdeğeri olduğu varsayılmaz. Eksik sonuçlar başarılı sayılmaz.

Düğme sağlayıcı yokken veya kendi tek bekleyen işlemi sürerken kapalıdır.
Bu kendi devam politikamızdır; senkron VCL çağrısının tüm thread/mesaj
davranışını kanıtlamaz. Her timer adımı sağlayıcıyı en fazla bir kez çağırır.
Profil yükleme ve sağlayıcı değiştirme nesli artırıp eski timer ve capture
token'larını geçersiz kılar. Tamamlanan çağrı polling ile tekrar yürütülmez.

Sağlayıcı API'si `set_manual_coordinate_provider(provider)` yoludur. Provider
`ManualCoordinateContext` alır, `ManualCoordinateCapture` veya None döndürür.
Capture, çağrı/nesil token'larını ve typed helper observation içerir.
Bu aşamada otomatik runtime sağlayıcısı yoktur. Test sağlayıcısındaki
gözlemler sentetiktir. Model hiçbir oyun hareket çağrısı yürütmez.

Kaynak: iki Richard PE'sinde136 komut, Delphi metot/alan kayıtları ve
GetText/StrToFloat import kimlikleri yeniden doğrulandı. Yedi CALL hedefi
yenilenen binary'de+1c kayar; model etiketleri eski kanonik adreslerdir.
Native helper/SEH/locale/x87 davranışları ve gerçek oyun hareketi açıktır.

Doğrulama:5039 Python testi (önceki5031 API aşamasına8 yeni runtime testi),
yeni tam yerel GUI1037 kontrol/11form/18sekme. Arayüz testi gerçek Git ve
X/Y widget'larını, X cleanup beklemesini, Y'nin fresh değerini, stale capture
reddini, disabled tekrar tıklamayı, yeniden çizimi, Tk timer'ı ve gerçek
profil yükleme yolunu sınar. Pencere gizli tutulur; oyunla IO yapılmaz.
`MANUAL_COORDINATE_PANEL_VALIDATION.json` güncel aşamadır. Önceki
`MANUAL_COORDINATE_VALIDATION.json` ve `PET_PANEL_VALIDATION.json`
tarihsel kaynak/test hashlerini saklar; bu dosyalar güncel eşlik iddiası değildir.

Giriş envanteri387, dışında kalan düzenlenebilir yol136'dır. İki metin alanı
eklenmiştir; bu sayılar tamamlanan özellik/fonksiyon sayısı değildir.
