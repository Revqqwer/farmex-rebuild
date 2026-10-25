# Upgrade gözlemli worker bağlantısı

4710 Python testi; yeni tam yerel GUI: 1037 kontrol, 11 form, 18 sekme.
UPGRADE_WORKER_UI_VALIDATION.json kod hash'lerini ve bu kapsamı kaydeder.

Gerçek Başlat düğmesi ve parametre olayları tek source-clock UpgradeRunner'ı
paylaşır. Ayrı, açık worker sağlayıcısı kurulduğunda kendi100ms Tk timer'ı
UpgradeWorkerInput ister. Clock, item getter, bağlantı gate'i ve helper dönüşleri
bu girdilerdir. Varsayılan gerçek oyun sağlayıcısı veya otomatik bellek/ağ erişimi
yoktur. Sağlayıcı yoksa worker zamanlayıcısı çalışmaz; mode2 Armor bu köprüye
henüz bağlanmadı. Editor/parametre işleri beklerken kendi worker'ı ertelenir;
bu tek-thread/FIFO yaşam döngüsü native thread eşliği değildir.

Cached interval bilinmiyorsa runner'ın constructor2000 değeri kullanılmaz.
İlk QWORD stamp bilinmiyorsa açık gözlem gerekir; başlangıçta0 varsayılmaz ve
Başlat damgayı sıfırlamaz. Daha sonra gate tick, enqueue tick ve helper sonrası
stamp ayrı kalır. Pending helper eski interval/gate'i yeniden tüketmez.

Anvil okuma sırası düzeltildi. Kaynak004f7168 önce scroll item getter'ını,
sonra target item getter'ını çağırır; object+8'i ancak ardından kopyalar.
UpgradeExecution artık cached Anvil okuyucusunu bu noktada çağırır. None bir
boşluktur;0 geçerli DWORD'dur. İkinci getter beklerken yapılan yeni Anvil ayarı
pakete yansır. Paket oluşturulduktan sonra ayar değişse de aynı invocation'ın
byte'ları korunur. Sonraki attempt yeni değeri alır. Standalone execution da
varsayılan runner Anvil'ini artık bu geç noktada okur.

Worker mevcut ortak yerel action queue'ya bağlanır; başka özelliklerin kayıt
önekini ve next_id sırasını korur. Yeni invocation başında güncel queue alınır.
Pending helper sırasında başka writer queue'yu değiştirirse overwrite/rebase
yapılmaz: queue_conflict bildirimiyle bekler. Tam yerel frame'den sonraki publish
hatasında işlem tekrar yürütülmez. Writer yazıp sonra hata verirse aynı candidate
görülerek çift append önlenir; normal dönüp değeri tutmaması başarı sayılmaz.
Bunlar kendi writer politikalarımızdır. Eski execution'ın queue/source prefix'i
normal helper dönüşü ve stamp tamamlanana kadar prospective tutma sınırı devam
eder; orijinalin erken row pop'u/native queue yan etkileri sertifikalanmaz.

Kaynak worker'ın scroll bulunamaması ve kuyruk boşalması yolları ortak
004f7af8 Durdur yardımcısını çağırır. Helper'ın içinde561f55 callback gate'i
yoktur; yalnız panel callback'i onu okur. Yeni helper giriş modu bu ayrımı
korur. Kaynakta Stop öncesi/sonrası managed string/notice/cleanup span'leri için
ayrı normal dönüş gözlemleri gerekir. Bu span'lerin tek tek native etkileri
uygulanmış sayılmaz. Ön span eksikken mode1 korunur; helper'a girince önce mode0,
ardından gerçek kendi Start/Stop düğmeleri güncellenir. Son cleanup beklerken
timer mode0 olsa da pending işi sürdürür.

Worker sağlayıcısını kaldırmak zamanlayıcıyı durdurur ve kendi pending prefix'ini
korur; yeni sağlayıcı aynı işi sürdürür. Profil değişimi worker/runner/sağlayıcıyı
geçersiz kılar. Profil içinden dönen eski capture uygulanmaz. Bekleyen worker
varken yeni Başlat/Durdur invocation'ı oluşturulmaz. Bu kendi eşzamanlılık
politikasıdır; source VCL mesajları veya hook yarışları için kanıt değildir.

Yeni GUI testi gerçek Start ve edit olaylarından gider: explicit ilk stamp,
getter boşluğu sırasında yeni Anvil, shared queue öneki/ID'ler, sağlayıcı
pause/resume, inner gate0'ın okunmaması, ayrı Stop span'leri ve profil değişimi.
Unit testler writer conflict, write-before-error, no-assignment return,
duplicate önleme, yeni invocation'da fresh Anvil ve invalid/unknown DWORD'u
kapsar.2409 retained instruction kaydı yeniden byte düzeyinde karşılaştırıldı.
505 kayıt önceki worker incelemesindeki iki current yordam,1904 kayıt iki
Richard sürümünün Upgrade olay grafiğidir; bu sayı bitmiş fonksiyon sayısı değildir.

Armor panel/worker aktarımı, otomatik veri edinimi/current-build bağları,
native helper/string/notice/exception/concurrency eşliği ve canlı oyun uyumu
açıktır. Yeni REA decompile, oyun bellek okuma/yazma veya ağ/eylem IO yapılmadı.
UPGRADE_START_UI ve UPGRADE_START_FRAME kayıtları önceki tarihsel aşamalardır.
