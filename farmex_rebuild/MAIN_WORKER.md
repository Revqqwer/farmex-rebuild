# Ana işleyici ve Monster Stone bağlantısı

Sonraki API bağı: Genie yolu artık isteğe bağlı generated child ve MS/Genie ortak kendi kuyruğu ile bağlanabilir. Aşağıdaki Genie yolunun opaque olduğuna ilişkin notlar önceki aşamaya aittir. [Güncel bağ](MAIN_GENIE_BINDING.md).

`main_worker.py`,0046ee14 yordamının248 talimatındaki kontrol akışını koşullu gözlem modeli olarak uygular. Native helper'ları veya oyun işleyicisini çalıştırmaz. Diğer helper gövdeleri, callback/thread etkileri, exception yolları ve zamanlayıcı bu modelin tamamlanmış kapsamı değildir. `whole_worker_verified` ve canlı doğrulama alanları false kalır.

Ön hazırlık çağrısı enabled bayrağından önce gelir. Disabled, exclusive ve notice yolları erken döner. Notice için iki ayrı bayrak gerekir; GetTickCount sıfır genişletilip kayıtlı QWORD'dan çıkarılır ve işaretli64 fark1000'e eşit/büyükse opaque mesaj span'ı çalışmış olarak gözlenmelidir. DWORD zaman sarması pozitif geçen süre varsayılmaz.

Etkinlik bölümünde tek yerel tick korunur, fakat QWORD damgalar ve interval global'i her kaynak kullanımında ayrı okunur. İlk QWORD fark0 ise bölüm atlanır. Interval global0 ise467cc4 çağrısının sonucu store planına eklenir; helper'ın rastgelelik/aralık semantiği uygulanmaz. Sonraki kontrol fresh interval'i signed DWORD olarak genişletir: activity farkı eşiği kesin aşmalı, periodic farkı ise eşiğe eşit/büyük olmalıdır. Guard AL ve gerekli ikinci bayrak callback yolunu seçer. Callback yalnız çağrı planıdır; gerçek thread açılmaz. Ardından periodic damga ve yeni interval store planı gelir.

Monster Stone kolunda561f5c DWORD'unun tam1 olması ve561f70 BYTE'ın0 olması gerekir.561f6c ilk kez taş kullanımı için okunur; source004c567c(context56216c) döndükten sonra hareket için yeniden okunur. Bu iki okuma birleştirilmez. Ardından savaş enable/blok kontrolleri gelir. Genel mod0 işlemleri, ortak helper'lar ve idle erken dönüşü ayrı yollardır.

İki öncelikli helper'ın AL sonucu sıfırsa hedef koluna gidilir. Mod0 kontrolü ve sonraki mod1 kontrolü farklı taze okumalardır. Mod1'de alan getter'ı en fazla üç kez ayrı çağrılır: ilk çağrı51, ikinci52, üçüncü53 ile full EAX karşılaştırılır. Eşleşmede004c5468(context56216c) çağrılır. Diğer mod2 karşılaştırmasının ortak kuyruktan önce davranış etkisi görünmez; model okumasını yine korur. Ortak0040d554 çağrısı hedef kolundan sonra gelir; daha erken çıkış yolları buna ulaşmaz.

`MainWorkerObservation.children` içinde `ms_use`, `ms_movement`, `ms_target` typed girdileri sağlanabilir. Bunlar mevcut bağımsız devam çerçevelerinden üretilir. Eksik child dış normal dönüşle geçilemez. Child tamamlandıktan sonra dış normal ayrıca gerekir. Kuyruk kaydı üst dönüş beklerken bir kez üretilir; yeniden advance çağrıları aynı kaydı çoğaltmaz. Önceden opaque olarak tüketilmiş çağrıya sonradan child eklenip geçmişe yeni etki yazılamaz.

Child store planları child içinde kalır. Sonraki canlı global okumaları child sonucundan otomatik doldurulmaz; setter/event/helper yan etkileri kanıtlanmış değildir. Bu model bir ana-işleyici turudur; döngü periyodu veya sürekli çalışan bot iddiası içermez. Arayüz compiler'ına yeni kontrol eklenmedi.

14 yeni test; erken çıkış sırası, notice eşitlik/sarması, MS tamDWORD1, kullanım-hareket arasındaki fresh bayrak, savaş/öncelik kontrolleri, üç ayrı alan sonucu, taze mod kontrolleri, iki farklı zaman eşitliği, sign extension, callback kısa devresi, generated child boşlukları ve tek enqueue, sonradan binding yasağını kapsar. Eski/güncel PE'deki1086 mevcut talimat kaydı ve dört REA raporu eşleşti:496 ana kontrol gövdesi,590 mevcut MS child gövdesi kaydı. Yeni ikili keşif kapsamı veya tam fonksiyon sertifikası değildir.
