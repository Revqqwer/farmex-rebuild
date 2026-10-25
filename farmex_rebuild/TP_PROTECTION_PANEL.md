# Koruma panelinden TP olay denemesi

Yerel deneme listesindeki **TP Koruma**, Koruma > Karakter TP Olursa kutusunu ve Bot Durdur/DC radio'larını kullanır. Akış dört adımı birleştirir: panel snapshot'ı, sınırlı kaynak ayar üreticisi, dispatcher'ın14 opcode karşılaştırması ve27 olay dalının çağrı/alan yazımı planı.

Boş JSON0046c0e1 ayar üretici girişinde bekler. Kaynak getter normal dönüşleri ayrıca sağlanır; enabled ve stop seçimi gerçek own panel değerlerinden gelir. Stop radio'suFalse ise kaynak B4=2 sonucuna gider; DC radio'su için ayrı bir getter uydurulmaz. Dispatcher prologue normal dönüşü olmadan çocuk girişine geçilmez. Önceki opcode eşleşirse o gövdede açık eksik olarak durulur; örneğin10 chat olayını atlayıp TP işlemi seçilmez.

**Panele ve olaya göre sentetik örnek** düğmesi açık own fixture gözlemleri doldurur. Varsayılan27 01 0a packet'i için oyun durumu okuyucu sonuçları10, tick10000 ve başlangıç zamanı0'dır. Bu örnek gerçek oyun, hesap veya bellek gözlemi değildir. Bildirim, bot durdurma, DC ve diğer yardımcı çağrıları yalnız planlanır; hiçbir oyun süreci durdurulmaz veya bağlantısı kesilmez.

Bu panel denemesi üç TP ayarını invocation boyunca sabit tutar. `tp_enabled_byte`, `action_first` ve `action_second` değerleri panelden türetilir ve çelişkili JSON ile değiştirilemez. Gerçek opak yardımcı/global/reentrant etkilerinin ayarı değiştirmediği kanıtlanmış sayılmaz. Farklı taze action değerlerini modellemek gerektiğinde alt seviye `TPFrame` API'si bunu destekler; own sabit panel denemesi o kapsamın tamamı diye sunulmaz.

Diğer alanlar ve normal dönüşler yalnız ulaşılan aşamada tüketilir. Bildirim dönüşü eksikken56209c yazımı planlanmaz; eksik giderildiğinde aynı frame ilerler ve önce tüketilmiş getter/tick öneki korunur. Tamamlanmış aynı frame tekrar çalıştırılmaz. Panel değişince ayar ve olay frame'i, yalnız packet değişince olay frame'i yenilenir. Sentetik örnek hem panel hem packet SHA-256 değerine bağlıdır; eski örnek yeniden oluşturulmalıdır. **Sıfırla** yeni deneme başlatır. Geçersiz JSON/HEX önceki sonucu geçerli bırakmaz.

Üç kontrol own profil kaydet/yükle yoluyla korunur. Scoped UI/compiler kontrol sayısı307→310, dışında kalan düzenlenebilir kontrol sayısı215→212 oldu. Bunlar özellik tamamlanma yüzdesi değildir. Sınırlı fonksiyon sayısı145 kaldı; yeni fonksiyon çözümü diye sayılmadı.

Sekiz yeni birim testi ve gerçek fakat gizli kendi Tk arayüz testi, üç widget seçimini settings→prefix→event planına bağlar; notice gap/resume, stop/DC radio eşlemesi, panel/packet snapshot reddi, aynı frame devamı, erken opcode sınırı ve profil roundtrip denetlenir. Geniş UI testine de bu kontrol eklendi. Native ve canlı uyumlulukFalse kalır.

21 Ekim20:39:35 UTC host metadata sorgusunda yalnız Knight/Farmex/Loader ad/PID kapsamındaki eşleşme0'dı. Bellek okunmadı ve yeni UAC/HPMP testi yapılmadı. Bu sonuç yalnız o an için geçerlidir.

Mevcut4 REA artifact'i ve iki sürümde3582 kaynak instruction kaydı tekrar doğrulandı. Ayrıca örtüşen2246 dispatcher kaydı kontrol edildi; toplam benzersiz kapsam diye eklenmez. Kaynak bağı: [TELEPORT_PROTECTION.md](TELEPORT_PROTECTION.md), [INCOMING_TP_DISPATCH.md](INCOMING_TP_DISPATCH.md). Tam UI kanıtı: `outputs/FarmexBot_TP_panel_bagi_kaniti.json`.
