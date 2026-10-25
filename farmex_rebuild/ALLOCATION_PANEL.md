# Stat/Skill panelinden satır üretimi

Bağımsız arayüzün `Stat/Skill Ayarları` yerel denemesi, Diğer bölümündeki iki gerçek etkinlik checkbox'ını ve `LwAutoStat/LwAutoSkill` listelerini okur. Gizli ana başlık eylem kimliğini, ilk alt sütun ismi, ikinci alt sütun eşiği sağlar. `checked` satır metadata'sı kaynak üreticide kullanılmadığı için kendi snapshot eşitliğine ve filtreye dahil edilmez.

`compile_allocation_panel` değişmez bir panel görüntüsü oluşturur. Checkbox/count/metin getter'ları bu kendi kararlı görüntüsünden gelir; bu, native VCL veya kaynak event/timer yürütümü değildir. Deneme bounded producer girişini kendi API sözleşmesiyle açıkça seçer. String/CPP container helper'larının normal dönüşü, final ANSI bytes ve iki generated integer conversion sonucu dış JSON gözlemleri olarak ayrı kalır. Varsayılan `{}` başarılı native/helper dönüşü üretmez.

JSON yalnız ulaşılan helper/alanı okur. Başka bir satırın bozuk dönüşü veya kullanılmayan değer erken değerlendirilmez. Eksik alt sütun kaynakta sessizce boş string/default sayılmaz; kendi trial açık hata verir ve eski sonucu temizler. Captured StrToInt64 child'ı tamamlanmadan üst helper dönüşü ile geçilemez. Kaynak varsayılan−1 yalnız açık catch-landing receipt'iyle gelir.

Örnek düğmesi mevcut panel satırlarına göre **sentetik** gözlemler üretir. İsimler için yalnız ASCII örneği destekler; diğer isimlerde yerel codepage tahmin etmez. Sayılarda strict signed-decimal64 alt kümesi kullanılır; geçersiz metin için native catch sonucu otomatik uydurulmaz. Kullanıcı ayrı raw capture gözlemleri sağlayabilir; bunlar lexical/native eşdeğerlik kanıtı sayılmaz.

Oluşturulan örnek panel snapshot SHA256'sına bağlıdır. Başlık/isim/eşik/etkinlik değişirse eski örnek reddedilir ve yeniden doldurulması istenir. Checked değişikliği hash'i değiştirmez. Yeni anlamlı panel görüntüsü yeni kendi producer frame'i açar; aynı görüntü eksik receipt'lerde mevcut frame'i sürdürür. Bozuk JSON eski görünür sonucu temizler, tüketilmiş prefix'i değiştirmez.

Sonuç ekranı iki listenin üretilen satır sayısını ve beklenen adımı gösterir. Native adresler veya puan dağıtılmış başarı mesajı üretmez. Üretilen semantik row nesneleri, gerçek AnsiString pointer'ları/oyun vektörleri değildir. Bu panel bağı raw otomatik dağıtım tüketicisini canlı belleğe bağlamaz veya oyun puanını değiştirmez.

Yedi yeni birim testi flags/JSON önceliği, gerçek sütunlar, unchecked satırlar, değişmez snapshot, eski örnek reddi, prefix devamı, eksik alt sütun, reached-only/bad JSON ve örnek politikalarını kapsar. Gizli kendi widget testi iki checkbox'ı invoke eder, gerçek treeview satırlarını kontrol eder; örnek/prefix/yeni satır, profil roundtrip ve stale-result temizliğini sınar. Bütün bunlar kendi uygulamamıza aittir.

Compiler envanteri293'ten297 kontrole çıkmıştır; bunun294'ü ana form sekmelerindedir. Kapsam dışı editable yol225'tir. Bu sayılar özellik veya proje tamamlanma yüzdesi değildir. Sınırlı statik fonksiyon eşlemesi123 olarak kalır. Kaynak producer'ın önceki3188 talimatlık kanıtı yeniden kullanılır; native allocation, codec, scheduler ve canlı uyumluluk açık kalır.
