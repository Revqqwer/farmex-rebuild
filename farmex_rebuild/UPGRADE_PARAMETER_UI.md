# Upgrade gerçek parametre olayları

4677 Python testi ve yeni tam yerel GUI1037 kontrol/11 form/18 sekme geçti.
UPGRADE_PARAMETER_UI_VALIDATION.json kapsamı kaydeder.

Scroll combo seçimi, Anvil edit ve wait edit değişimleri aynı sıralı üreticiyi
çağırır. Ayrı explicit parameter provider yoksa yalnız normal ayar düzenleme
olur; kaynak callback sonucu/gate1 uydurulmaz. Kurulum sırasında event olmadan
cached parametreler hazır sayılmaz. Her gerçek olay kendi invocation/trigger
yoluyla gate/init/GetText/CP/scalar/cleanup gözlemlerini ister. Partial state
scroll ANSI ->Anvil lowDWORD ->wait lowDWORD sırasıyla saklanır.

Tk StringVar trace'i, Entry görüntüsü yenilenmeden çalışabilir. Bu nedenle
edit GetText yeni StringVar değerini kullanır. Combo'da actual get() değeri
ve bilinen seçim/cache vardır. Hidden ItemIndex-1 Text bilinmiyorsa boş metin
tahmin edilmez. Gözlenmiş özel Text kendi hide/rerender süresince korunur;
profil değişimi eski Text bilgisini ve kendi cached state'ini geçersiz kılar.

ID AL'ın kendi SetText'i Anvil event'ini oluşturur. Event anında başlatılır;
eksik bir inner observation varsa ID AL text_return aşamasında bekler ve
üst cleanup receipt'ini tüketmez. İç frame'ler tamamlanınca devam eder.
Gate0 inner callback normal no-op'tur: görünür ID değişebilir, cached Anvil
değeri eski kalır. Bu ayrım kaynakta ID AL'ın guard'sız olmasıyla uyumludur.

Own100ms parameter kuyruğu, reentrant event'leri FIFO'da izler; dış Editor
jobs ile ayrı çalışır. Native VCL monolitik/nested message timing veya bütün
SEH/concurrency eşliği iddia edilmez. Provider değiştirmek pending parent ve
child işleri iptal eder, fakat committed own parametre prefix'ini korur.
Profil değişimi hem işleri hem kendi cached state/Text bilgisini iptal eder.
Bunlar açık kendi yaşam döngüsü politikalarıdır; native profil davranışı
sertifikası değildir. Start/stop/worker/Armor aktarımı henüz bağlı değildir.

GUI testi gerçek ComboSelected ve edit trace'leriyle üç yolu doğrular:
lowDWORD/ANSI prefix, gate0 visible-vs-cache ayrımı, cached önceki Anvil ve
fresh sonraki wait, hidden form/FIFO, invalid scalar QWORD gözlemi, nested
ID AL beklemesi, observed custom minus-one Text ve profil/stale callback
izolasyonu.2128 source/RTL kaydı yeniden byte düzeyinde doğrulandı. Geçersiz
parse native catch sonucu hâlâ tahmin edilmez. Yeni REA decompile, orijinal
bot çalıştırması, oyun bellek/ağ/eylem IO yoktur. Canlı uyumluluk açık kalır.
