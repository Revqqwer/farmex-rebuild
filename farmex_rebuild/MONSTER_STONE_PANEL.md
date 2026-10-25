# Monster Stone panel bağlantısı

Bağımsız uygulamanın Yerel Deneme bölümüne `Monster Stone` seçeneği eklendi. Kaynak panelindeki boss/tüm mob seçimi, taş bitince alarm ve MS etkinleştirme olmak üzere dört gerçek kontrolü okur. “Yakında” diye kapalı gelen tüm-mob ve rotalı gitme kontrolleri açılmaz. Rotalı gitme, Achieve toplama ve ana worker'ın arayüzden çalıştırılması bu bağlantının tamamlanmış kapsamı değildir.

`MonsterStoneTrial`, kendi başlangıç modu0 ve yeni panel görüntüsüyle mevcut `compile_ms_settings` modelini kullanır. Boss önceliği ve ikisi de seçili değilse önceki modu koruma davranışı aynıdır. Her adımda ayar snapshot'ı alınır; anlamlı panel değişikliği yeni etkinleştirme denemesi başlatır. Bu kendi ayar→etkinleştirme düzenidir; orijinal event/timer sırası olduğu iddia edilmez.

Etkinleştirme için kaynak checkbox'ın kararlı boolean değeri kendi getter adaptöründen gelir. WallHack setter, bot-start ve dış tamamlanma dönüşleri ayrı JSON gözlemleridir. Varsayılan `{}` başarılı dönüş üretmez. Örnek düğmesi sentetik dönüşleri açıkça doldurur. İsteğe bağlı typed bot-start alt modeli eksikse dış dönüş bunu geçemez. JSON yalnız ulaşılan alanları doğrular; kullanılmayan bozuk alt-model alanları erken değerlendirilmez. Devam örnekleri yalnız yeni dönüşü içerebilir.

Setter dönüşü sağlandıktan sonra kaynakta görülen WallHack işaretleme etkisi yalnız kendi panelindeki boolean değere bir kez uygulanır. Bot-start veya son dönüş beklenirken bu UI prefix korunur. MS kapatıldığında yalnız MS flag0 planı vardır; WallHack kendi panelinde açık kalır, otomatik bot-stop veya native yazma üretilmez. Ayarlar mevcut JSON profil sistemiyle kaydedilip yüklenir.

Yerel deneme gerçek oyun, bellek, paket gönderimi veya sürekli worker çalıştırmaz. Ana worker/taş kullanımı/hareket/hedef modelleri ayrı API kanıtı olarak kalır. Ekran sonuçları seçim, alarm, beklenen adım ve kendi deneme durumunu gösterir; native adresleri kullanıcı akışına dökmez.

Yedi yeni birim testi snapshot/değişim, eksik ve kısmi dönüşler, yalnız bir UI prefix, disable yolu, typed child, mode koruma/reset ve hatalı örnekte eski sonuç temizliğini kapsar. Gizli açılan kendi gerçek Tk widget testi enable/alarm kontrollerini tıklar, kaynakta kapalı tüm-mob durumunu ve ayrı WallHack setter kapısını doğrular; profil roundtrip'i ve kapatınca WallHack'in korunmasını sınar. Gizli test ChatGPT/oyun penceresini öne getirmez.

UI/compiler envanteri289'dan293 kontrole çıktı; bu özellik veya proje tamamlanma yüzdesi değildir. Statik fonksiyon eşlemesi120 olarak kalır. Canlı uyumluluk hâlâ doğrulanmamıştır.
