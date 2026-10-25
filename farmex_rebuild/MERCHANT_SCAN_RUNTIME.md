# Yerel tarama yaşam döngüsü ve panel bağlantısı

Başlat/durdur düğmeleri, dört tarama checkbox'ı ve rota satırları kendi `OwnedMerchantScan` oturumuna bağlıdır. Bu uygulama, native normal-return gözlemleri isteyen `merchant_scan_control.py` planlayıcısından ayrıdır: kendi liste temizliği, Tk setter'ları ve Python durum değişiklikleri gerçekten çalışır; bunlar kaynak VCL çağrılarının tamamlandığına dair gözlem olarak kullanılmaz.

Başlat önce yerel verileri temizler, düğmeleri değiştirir, gerektiğinde Buying seçer, önbellekte rota açık ise X/Y satırlarını okur. Sayı çözümlemesi daha önce 2000 sonlu native örnekle karşılaştırılan Int32 skaler modelini kullanır. Hatalı koordinat önceki rota satırlarını geri almaz ve aktif bayrağına ulaşmaz. Kullanıcı durdur düğmesiyle bu durumdan çıkabilir. Boş rota kabul edilir; worker'ın sonraki sınır kontrolü ayrı kapsamdadır.

Başarılı başlatma `waiting_for_runtime_data` durumudur. Oyun verisi sağlayıcısı veya tarama zamanlayıcısı kurulmuş sayılmaz; sahte satır, lookup, yanıt, paket gönderimi veya tamamlandı sonucu üretilmez. Panel oyun verisi bağlantısını beklediğini gösterir. Tek tarama düğmesi, ayrı kaynak akışı uygulanana kadar kapalıdır. TXT dışa aktarım tamamlanmadı.

Combo seçimi sonuç filtresini yeniler; tarama ayar önbelleğini tek başına yenilemez. Dört checkbox'tan biri değiştiğinde beş ayar birlikte okunur. Belge yükleme kendi initialization aşamasıdır; kaynak programın global gate değeri bilinmez.

Durdurma aktif/bekleyen yanıt bayraklarını kapatır; rota ve sonuçları korur. Kendi GİT hücresi koordinat dönüşümünden önce aynı bayrakları ve üç düğme intentini değiştirir, durum metnini veya rotayı değiştirmez. PM taramayı durdurmaz. Gerçek hareket/gönderim etkisi yoktur. Tek tarama düğmesi için kaynak enable intenti, uygulanmamış bir düğmeyi açmak yerine yerel UI'da kapalı kalır; bu fark açıkça korunur.

Panel yeniden çiziminde oturum ve düğmeler korunur. Profil yüklemesinde oturum sıfırlanır. Yerel rota bir satır snapshot'ıdır; native taze Count/iterator yarışları, bellek kapasitesi, allocator hataları, managed cleanup ve SEH eşliği kanıtlanmış değildir.

Kaynak alan/callback eşlemesi `FarmexBot_merchant_tarama_yerel_arayuz_kaniti.json`; önceki source kontrolü `FarmexBot_merchant_tarama_kontrol_kaniti.json` içindedir. Güncel Python/GUI doğrulaması `MERCHANT_SCAN_RUNTIME_VALIDATION.json` ile ayrıca kaydedilir. Bunlar tam özellik veya canlı uyumluluk sertifikası değildir.
