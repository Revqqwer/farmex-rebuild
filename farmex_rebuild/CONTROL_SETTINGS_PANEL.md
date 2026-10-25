# Kontrol ayarlarının kendi panelimize bağı

Motor Denemesi içindeki **Kontrol Ayarları** seçeneği, Kontrol sekmesindeki
15 gerçek checkbox/metin alanını `ControlSettingsTrial` üzerinden kaynakta
doğrulanan 191 talimatlık ayar üreticisine bağlar. [Kaynak kapsamı](CONTROL_SETTINGS.md).
**Panel ayarlarını önizle** düğmesi, bu alanların değerlerini içeren açık bir
yerel örnek oluşturur. Gerçek VCL/RTL dönüşleri veya oyun işlemi yürütülmez.

Coin eşiği iki DWORD olarak korunur ve birlikte signed64 sayı olarak gösterilir.
Örneğin `4294967297` hem alt hem üst DWORD'da bir tutar; `-1` görüntüde negatif
kalır. Diğer sayıların kaynak davranışındaki alt DWORD ve fallback kuralları
değişmedi. Sayı dönüşü, dış dönüş ve temizlik gözlemleri ayrı ayrı bekleyebilir;
kabul edilen önceki yazımlar yerel alanda korunur.

Snapshot değişirse eski örnek reddedilir. Alan değerleri JSON gözlemiyle
değiştirilemez. HP gibi bu önizlemeyle ilgisiz test girdileri ayarları etkilemez.
15 alan profil kaydı/yüklemesinde korunur. Örnek sayı dönüştürücüsü yalnız açık
signed decimal64 alt kümesini destekler; kaynak parserının bütün kurallarını
uyguladığı iddia edilmez. Kaynak catch yolu ayrıca gözlem olarak verilebilir.

15 alanın 13'ü önceki kontrol kararları için envanterdeydi. Zone değişimi ve
Town isteği bayraklarıyla iki yeni giriş eklendi: toplam 373→375; envanter dışında
kalan düzenlenebilir alanlar 150→148. Bu iki bayrağın oyun içi durdurma etkisi
doğrulanmış sayılmadı. Kontrol kararlarına API köprüsü mevcuttur; bu yeni ekran
yalnız ayar üretimi ve yerel yazımları önizler.
