# Armor başlangıç düğmesi

4719 Python testi; yeni tam GUI: 1037 kontrol, 11 form, 18 sekme.
ARMOR_START_UI_VALIDATION.json bu aşamanın kod hash'lerini ve kapsamını kaydeder.

Gerçek btnUpgradeArmorAl artık ortak Upgrade Editor sağlayıcısına ve aynı
source-clock runner'a bağlı. Sağlayıcı yoksa düğme kapalıdır. Raw561f55 callback
gate0 hiçbir kaynak alanını veya seçim kutusunu tüketmeden döner. Filter/NPC
selector, NPC pointer, koordinat offset/ftol, distance ftol ve bag AL sonuçları
açık gözlemlerdir; gerçek bellek/FPU/helper işlemleri yürütülmez.

Yeni ArmorStartFrame, tek snapshot'ın sonunda tüm alanları uygulamak yerine
ulaşılan alanları sırayla yazar: NPC4c, pointer48, X50, Y54, mapped item58,
ikinci seçim5c. Daha sonraki bir boşluk veya hata bu öneki geri almaz. Önceki
gözlemleri her devamda yeniden vermek gerekmez. Signed distance DWORD10 ve üzeri
too_far yoluna gider; source ftol INT_MIN sonucu signed olarak değerlendirilir.
Pointer0 sessiz döner; NPC0, uzaklık, boş eşya ve dolu bag mesaj yolları ayrıdır.

Gerçek kendi combo ItemIndex'i iki kez okunur. İlk okuma mapping dönüşü
beklerken sabittir; ikinci okuma ancak mapping tamamlandıktan sonra yapılır.
Bu arada seçim değişirse eşya kimliği ilk, selector ikinci değerden gelir.
5/11/17 boş mapping'leri, ikinci getter ve bag sorgusundan önce çıkar. Eşleme
23 source literalini kullanır; ItemIndex-1 ham DWORDffffffff olarak default0'a
gider. Hidden form'da güncel kendi profil ItemIndex'i kullanılır.

Mesaj/helper normal dönüşü ve iki ayrı managed-string cleanup dönüşü beklenir.
Eski pure replay'in birleşik cleanup göstergesi bu frame'i tamamlamaz. Mesaj
ve string helper yan etkileri opaque kalır; orijinal modal/VCL/SEH çalıştırılmaz.
Başarı kuyruğu ve iki zaman damgasını korur; yalnız counter60=0 sonra mode10=2
yazılır. Kaynak constructor düğme enabled durumunu değiştirmediği için kendi
Start/Stop runtime bayrakları da korunur. Mode2 satın alma worker'ı henüz bu
başlangıca bağlı değildir; döngünün çalıştığı veya eşya alındığı iddia edilmez.

Kendi100ms/FIFO Editor kuyruğu sekme değişiminde devam eder. Profil değişimi
eski frame'i iptal eder ve yeni runner yaratır. Bekleyen worker varken yeni
Armor başlangıcı açılmaz; bu kendi eşzamanlılık politikamızdır. Native hook,
iterator/FPU/ABI, callback zamanlaması veya tam fonksiyon eşliği değildir.

GUI testi gerçek düğme ve combo olaylarıyla raw gate0, mapping boşluğunda iki
farklı seçim, hidden form, blank item erken çıkış, iki message cleanup ve profil
iptalini sınar. Unit testler partial koordinat öneki, getter normal dönüşünde
freeze, signed distance/pointer0 ve geç capture iptalini de kapsar. İki Richard
PE'sindeki constructor/map/NPC selector ve callback'ten1294 instruction kaydı
yeniden byte düzeyinde karşılaştırıldı. Test/kayıt sayıları tamamlanma oranı
veya bitmiş fonksiyon sayısı değildir.

Sonraki açık: Armor mode2 worker, branch'e özel notice/cleanup/mode0 sırası,
paylaşılan queue'nun iki enqueue'su ve ayrı post-clock/counter aktarımı.
Ek statik inceleme FarmexBot_armor_worker_sinir_analizi.json içinde431 worker
instruction kaydını yeniden karşılaştırır: uzaklık/dolu bag önce mode0 yazar;
43 sınırı notice ve ilk cleanup'tan sonra, ikinci cleanup'tan önce mode0 yazar.
Mode2 ortak Start/Stop UI helper'ını çağırmaz. Mevcut legacy float distance/
birleşik stop modeli bu alanın tam source kapsamı sayılmaz.
Native helper/runtime kimliği, otomatik veri edinimi ve canlı oyun uyumu da açık.
Bu aşamada yeni REA decompile veya oyun bellek/ağ/eylem IO yapılmadı.
