# Upgrade gerçek başlat/durdur düğmeleri

4691 Python testi ve yeni tam GUI: 1037 kontrol, 11 form, 18 sekme.
UPGRADE_START_UI_VALIDATION.json bu aşamanın kapsamını ve hash'lerini kaydeder.

Başlat ve Durdur aynı Editor sağlayıcı/FIFO yaşam döngüsüne, parametre
üreticisinin cached scroll durumuna ve tek source-clock UpgradeRunner'a bağlı.
Normal dönüş/gate/slot byte gözlemlerini açık sağlayıcı verir. Sağlayıcı yoksa
düğmeler kapalıdır; parametre callback'i oluşmadan cached değer hazır sayılmaz.
Scroll metni görünür combo'dan yeniden alınmaz; kaydedilmiş sayılmış ANSI
değeri açık kod sayfasıyla çözülür. Her slotun yeniden dönüşüm byte gözlemi
ayrıdır; otomatik veya bağımsız doğrulanmış dönüşüm varsayılmaz.

Başlat kendi düğmelerini 0/1 yapar, end/begin/erase dönüşlerinden sonra kuyruğu
temizler. Scroll sonucu -1 olsa da seçili satır döngüsü sürer. Caption signed32
dönüşümü ve cleanup/append dönüşleri ayrı beklenir; mode1 yalnız sonda yazılır.
Geçersiz caption native exception sonucu bilinmediğinden başarıya çevrilmez.
Durdur mode0'ı düğmelerden önce yazar; kuyruk/scroll/zaman damgaları korunur.

Gerçek Tk düğmesi başlangıçta tasarım gereği kapalı olan Durdur'u açabilir.
Yalnız düğmenin kendi Enabled tasarım değeri runtime durumuyla değiştirilir;
devre dışı üst bileşenler aşılmaz. Sekme değişince aynı runtime durum yeniden
uygulanır. Kaynak helper boşluklarında o ana kadarki kendi değişiklikleri
korunur. Provider değişimi pending işleri iptal edip committed prefix'i tutar;
profil değişimi kendi runner/parametre durumunu ve eski timer yanıtlarını
geçersiz kılar. Reentrant Stop, pending Start'ın ardından kendi FIFO'sunda
işlenir. Bunlar açık yerel politikalardır; native thread/VCL eşliği değildir.

Yeni GUI kontrolü gerçek parametre olayından scroll üretir ve gerçek düğmeleri
çağırır. Bilinmeyen cache, gate0, seçili/işaretsiz caption, korunan kuyruk/saat,
runtime enabled/rerender, helper boşluğu, gizli sekmede FIFO ve profil içinden
dönen eski provider yanıtı sınanır. İki retained Richard PE'sindeki Upgrade
olay grafiğinin 1904 instruction kaydı yeniden byte düzeyinde karşılaştırıldı.

Sayısal cached Anvil/aralık değerlerinin worker'a aktarımı ve worker'ın ortak
eylem kuyruğuyla yürütülmesi henüz bağlı değildir. Constructor varsayılanları
canlı kaynak değerleri sayılmaz. Armor panel bağlantısı, native exception/
string/allocator eşliği, otomatik veri edinimi ve canlı oyun doğrulaması açık.
Ek statik inceleme (FarmexBot_upgrade_worker_aktarim_sinirlari.json) iki yordamın
505 instruction kaydını yeniden karşılaştırdı: kaynak serializer Anvil+8'i iki
eşya getter'ından sonra kopyalar; mevcut UpgradeExecution ise helper başında
sabitliyor. Worker bağlantısında bu erken okuma düzeltilmeli. Kaynak worker'ın
ortak Stop yardımcısına iki çağrısı var; yalnız mode0 yazmak UI eşliği sağlamaz.
Bu aşamada oyun belleği/ağ/eylem IO veya yeni REA decompile yapılmadı.
UPGRADE_START_FRAME.md ve onun validation dosyası önceki API aşamasıdır.
