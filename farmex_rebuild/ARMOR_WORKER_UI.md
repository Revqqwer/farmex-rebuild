# Armor gözlemli worker bağlantısı

4733 Python testi; yeni tam GUI: 1037 kontrol, 11 form, 18 sekme.
ARMOR_WORKER_UI_VALIDATION.json bu aşamanın kapsamını ve kod hash'lerini kaydeder.

Gerçek Armor başlangıcı mode2'yi kurduktan sonra açık worker sağlayıcısı kendi
100ms timer'ında UpgradeWorkerInput/ArmorWorkerObservation verir. Varsayılan
otomatik oyun sağlayıcısı yoktur. İlk Armor QWORD stamp bilinmiyorsa0 varsayılmaz.
Gate tick ham DWORD'dur; signed64 elapsed>=200 olmadan sonraki alanlar tüketilmez.
Timer'ın100ms poll süresi kaynak GetTickCount sonucu yerine geçmez.

Kaynak FILD sırasındaki cached Y54/X50 bilinir olmalıdır. Distance helper'ının
son ftol sonucu ham DWORD olarak alınır ve signed32 karşılaştırılır; INT_MIN
gibi source sonuçları nonnegative float'a zorlanmaz. Sonuç bilindikten sonra bag
helper AL ayrı ve fresh gözlemdir. İlk gate/distance tamamlandıktan sonraki
boşluklarda bu girdiler yeniden örneklenmez. Yardımcı FPU/native işlemlerinin
kendisi yürütülmez. NPC4c/item58/selector5c kaynak push sırasıyla tutulur;
source Armor Unicode hazırlık span'i ayrı normal dönüş ister.

Mevcut Armor serializer 20 byte satın alma ve 2 byte takip kaydı üretir. Her
enqueue kendi connection gate/tick gözlemine sahiptir; delay0 ve100 ayrıdır.
Free-slot helper ve vendor karşılaştırmaları açık gözlemdir; tanımsız vendor
local için0 uydurulmaz. Caller temporary cleanup ve post-helper stamp ayrı
kalır. Legacy execution'ın packet/source prefix'lerini tam yerel helper frame'i
bilinene kadar prospective tutma sınırı korunur; orijinalin allocator/queue
yan etkileri bu transaction politikasıyla sertifikalanmaz.

Counter60, helper ve caller cleanup dönüşünden sonraki güncel shared DWORD'dan
artırılır; eski pending tahmini sonuca geçirilmez. Post stamp Armor40/44'e,
counter60'a kendi source-field izdüşümünde yansır. INC low32 wrap eder ve limit
signed counter>42'dir. Yerel43 tam deneme testinde86 kayıt oluşur; bundan oyun
satın alma başarısı veya inventory ACK sonucu çıkarılmaz.

Üç terminal yol ayrı devam eder. Distance>=10 veya bag AL!=0, mesaj span'inden
önce mode0 yazar. Counter limiti ise kuyruk/post-clock/counter önekini korur,
mode2'de message normal dönüşünü ve ilk cleanup'ı bekler; mode0 bundan sonra,
ikinci cleanup'tan önce yazılır. Mode0 olsa da pending cleanup için timer devam
eder. Mode2 bu yollarda ortak Start/Stop UI helper'ını çağırmaz ve düğme runtime
bayrakları korunur. Mesaj/string span'lerinin native etkileri opaque kalır;
kendi devamı ayrı açık normal-return receipts ister.

Shared queue öneki/ID sırası korunur. Pending helper'da başka writer değişirse
overwrite/rebase yapılmaz; conflict bekler. Publish hatası packet/helper'ı
tekrar çalıştırmaz; yazıp hata veren writer aynı candidate görülünce duplicate
oluşturmaz. Bu kendi writer/FIFO politikasıdır. Pending worker sırasında yeni
başlangıç invocation'ı açılmaz. Profil değişimi eski sağlayıcı/capture'ı ve
kendi worker'ını geçersiz kılar; native eşzamanlılık/SEH eşliği iddia edilmez.

GUI testi gerçek Armor düğmesi ve cached seçimden gider: unknown ilk stamp,
eksik ikinci enqueue, shared queue öneki ve20/2-byte içerik/zamanlar, explicit
local counter42 fixture'iyle limit notice/cleanup0/mode0/cleanup1 ve profil
stale capture. Unit testler43 tam attempt/86 record, signed INT_MIN, low32 wrap,
fresh counter after helper, cached argument/coordinate prefix, distance/bag
erken stop, publish duplicate ve external writer conflict'i kapsar.2289 source
instruction kaydı tekrar byte düzeyinde karşılaştırıldı:1294 Armor startup/
map/selector/callback;564 iki-sürüm serializer/first-zero/followup;431 current
worker. Bunlar bitmiş fonksiyon veya tamamlanma yüzdesi sayıları değildir.

Kalan kapsam: finer native getter/packet prefix ve helper/string/FPU/runtime/
allocator/SEH/concurrency eşliği, otomatik current-game veri edinimi ve canlı
uyumluluk; diğer özelliklerdeki açık akışlar da devam eder. Yeni REA decompile,
orijinal bot/oyun çalıştırması, bellek okuma/yazma veya ağ/eylem IO yapılmadı.
ARMOR_START_UI ve UPGRADE_WORKER_UI kayıtları önceki tarihsel aşamalardır.
