# Otomatik stat ve skill puanı dağıtımı

Sonraki API bağı: iki listenin bounded captured üretici modeli eklendi. Aşağıdaki satır üretiminin açık olduğuna ilişkin notlar önceki aşamanın kapsamıdır; native/UI/consumer-memory bağlantıları hâlâ açıktır. [Satır üreticisi](ALLOCATION_PRODUCER.md).

`00458df8`,NP/coin/level kontrolü00458f98'den ayrı127 talimatlık bir yordamdır. Merkezi004576ec üreticisinin form+f48/f4c getter'ları, context+20/+21 alanlarını doldurur. Published method/field kayıtları bunları `Diğer > Otomatik Stat/Skill` altındaki `chAutoStat` ve `chAutoSkill` kontrolleriyle eşleştirir. Ana0046ee14, bu yardımcıya562194 context'ini geçirir.

`auto_allocation.py`, bu kontrol akışını raw captured gözlemlerle uygular. Başlangıç GetTickCount sıfır genişletilip553cac/553cb0 QWORD damgasından çıkarılır. Signed64 fark500 ms'ye eşit/büyükse devam edilir. DWORD tick sarması pozitif süre varsayılmaz. Hiç girişim yoksa damga güncellenmez.

Stat BYTE açık ve00462eb8 free-point EAX sonucu signed olarak pozitifse stat vektörü taranır. Satırlar12 bayt aralıklıdır. Count için begin null kontrolü, end ve çıkarma begin'i ayrı okunur; düşük32 fark signed kabul edilip CDQ/IDIV12 ile sıfıra doğru bölünür. Sonuç unsigned olarak indeksle karşılaştırılır. Negatif/bad fark otomatik boş listeye çevrilmez. Sorgu anahtarı, eşik ve eylem argümanı için üç ayrı begin okuması vardır.

00462ed8 satır anahtarıyla sorgulanır. Signed güncel değer eşikten küçükse satır+4 argümanı004650d8'e verilir. Eylem normal dönüşünden sonra taze GetTickCount düşükDWORD damgaya, yüksekDWORD0 yazım planına girer; yordam çıkar. Aynı turda birden fazla stat veya skill girişimi yapılmaz.

Stat yolu girişim yapmadıysa skill BYTE ve00462e8c free-point sonucu kontrol edilir. Skill vektörü de12 baytlık satırlardır; sorgu argümanı satır+4, eşik satır+8'dir.00462d20 sonucu signed olarak eşikten küçükse00462670 level sorgusu gerekir. Level sonucu güncel değerden kesin büyük değilse bütün yardımcı erken döner; sonraki skill satırlarına geçmez. Uygunsa satır+4 yeniden taze okunup00465ec4'e verilir, shared damga taze tick ile güncellenir ve çıkılır.

Satır anahtarı/argümanı/eşiği açık DWORD gözlemleridir. Stat adının kodlaması veya UI liste sütunlarının native satırlara dönüştürülmesi henüz uygulanmadı. Eylem helper'larının gerçek callback etkileri opaque normal dönüşlerdir; model puan sayısını artırmaz/azaltmaz ve başarı varsaymaz. Kaynak eylem helper gövdelerinde doğrudan004c7710 çağrısı yoktur; bundan dolaylı etkisizlik veya ağ davranışı sonucu da çıkarılmaz.

`AutoAllocationFrame` tüketilmiş öneki korur. Eylem dönüşünden sonra post-tick beklenirse yeni argümanla tekrar girişim üretilmez. Yerel row bütçesi kaynak liste sonu değildir; bütçede durulursa skill yoluna geçilmez. Ana işleyicide geçmiş API anahtarı `common_genie` korunmuştur; bu etiket kaynağın Genie özelliği olduğu anlamına gelmez. Bu key altındaki typed child artık yalnız gerçek00458df8 modelini bağlar ve dış normal dönüş ayrıca gerekir.

On yeni test;500 eşitliği/sarma, stat önceliği, fresh pointer'lar, stat eşitliğinde skill'e geçiş, signed free-point/threshold, IDIV negatif/sarma, level erken dönüşü, action/post-tick ayrımı, yerel bütçe ve main child/outer dönüşlerini kapsar. Eski/güncel ikililerde3422 mevcut talimat kaydı, iki UI method/field eşlemesi ve beş gerçek REA raporu doğrulandı. Bunun254 kaydı otomatik dağıtım gövdesidir; diğer kayıtlar pasif producer/caller/helper kanıtıdır.

UI compiler bağlantısı, satır producer'ı, native puan dağıtımı ve canlı oyun etkisi açık kalır. Compiler kontrol sayısı293 olarak kalır. Yeni ikili keşif veya tam fonksiyon sertifikası iddia edilmez.
