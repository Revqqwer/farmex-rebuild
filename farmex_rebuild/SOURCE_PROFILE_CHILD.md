# Profil dedektörü alt sonucunun tutarlılığı

Üst profil seçimi artık bağlanan `ProfileDetectionPlan`sonucunu kendi immutable `ProfileDetectionObservation`gözlemlerinden yeniden üretip karşılaştırır. Salt `complete=True, mode=1/2`etiketi, sonradan değiştirilmiş sonuç, çağrı listesi veya native doğrulama iddiası yeterli değildir. Denetim ilk parent store'dan önce yapılır. Snapshot'sız elde hazırlanmış child planı açık hata verir.

Generated child eksikse eksik cleanup kapısı korunur; dış parent normal dönüşü bunu geçemez. Geçerli generated child tamamlandığında da ayrı `detect_profile`normal dönüşü gerekir. FileExistsdüşükALsemantiği, iki farklı startup modeokuması, constructor normal sınırı ve iki sender alanının dar projeksiyonu değişmedi. Ham detectorEAXyolu ayrı opaque gözlem olarak korunur; generated child kanıtı sayılmaz.

Beş yeni regresyon testi ters mod seçimini, değiştirilmiş çağrı/native iddialarını, snapshot eksikliğini, missing cleanup'ıncompleteolarak yeniden etiketlenmesini ve geçerli generated sonucun ayrı dış dönüşünü kapsar. Son tam koşu3030testtir. Bu değişiklik yalnız bağımsız model tutarlılığıdır; native profili veya canlı bağlantıyı doğrulamaz. UI değiştirilmedi ve yeniden sınanmadı.

Arayüz derleyicisi dışındaki233kontrol için envanter artık kaynak DFM `disabled_by`ve olay alanlarını da saklıyor.48'i DFM'de devre dışı,65'inde doğrudan olay property’si yok; bu iki küme örtüşebilir. Bunlar runtime'da devreye alınmadığı veya hiç tüketilmediği kanıtı değildir. Draki grubundaki14kontrolün kaynakta devre dışı başlaması, bu grubu14eksik çalışan özellik gibi saymamak gerektiğini gösterir. Tam özellik kapsamı ayrı analiz ister.
