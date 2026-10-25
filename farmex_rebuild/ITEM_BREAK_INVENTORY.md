# Item kırma: slot taraması ve envanter koruması

23 Ekim 2026. `item_break_inventory.py` kaynak00463ac0 slot döngüsünü,
00470f6c normal koruma kararlarını ve mevcut ana döngüye tipli çocuk bağını
modeller. Slot getter'ı004634a4, isim araması00463950, string/notice/stop
yardımcılarının gerçek etkileri ayrı gözlem sınırlarıdır. Oyun I/O'su yoktur.

Slot taraması14'ten41'e kadar ilerler. Normal slot getter sonucu EAX0 ise
boş sayaç artar. Sayaç işaretli eşik argümanını **aşarsa** EAX0 ile hemen
çıkılır. Tüm slotlar bu koşula takılmadan biterse yalnız AL1 yazılır; EAX'ın
üst24 biti son getter sonucundan kalır. Eşik hamDWORD olarak tutulur ve
karşılaştırmada signed32 kullanılır. Negatif eşik ilk slotta bile çıkışa
neden olabilir; yeni bir negatif eşik doğrulama politikası eklenmedi.

Item kırma koruması bu yardımcıyı eşik0 ile çağırır. İlk boş slot sonucu0;
hiç boş yoksa sonuçAL1 olur. Çocuk planının tamamlanması ile00463ac0 parent
normal dönüşü ayrı kanıtlardır. Parent bayrağı eksik slot sonuçlarını atlatamaz.

Dolu durumda0040ae0c(561f34,0) planı ve ardından ayrı “Inventory Doldu , Bot
Durduruldu !” bilgi/temizleme bölümü gerekir. Bu dal mode+c veya Abyss
arama girdisini tüketmez; normal sonu4710d0'dır.

Boş yer varsa taze mode+c okunur. Sıfır olmayan modlar Abyss kontrolünü
atlar. Mode0 için “Abyss Gem” Unicode geçicisi oluşturma normal dönüşü,
00463950 normal dönüşü ve ham EAX ayrı girdilerdir. Yalnız AL0 yokluk
anlamına gelir; AL1..255 varlık dalına gider. Bu karar, geçici temizliği
çağrısından önce kaydedilir. Temizlik tamamlanmadan stop/notice yolu açılmaz.
Yoklukta ayrı stop ve “Abyss Gem Bitti , Bot Durduruldu !” notice planı çıkar.
Bu yollar4710c6 normal epilog girişine kadar modellenir; native SEH yoktur.

`ItemBreakInventoryCycleFrame` tipli koruma çocuğunu ana döngüde yalnız ilk
çalışma baytı gerektirdiğinde yürütür. Dışarıdan doğrudan guard-return
bayrağı vermeyi reddeder; çocuk tamamlandıktan sonra ayrıca parent-return
gerekir. Sonraki561f6c okuması bağımsızdır. Stop planı bayrağı sıfır varsaymaz;
gerçek helper etkisi ayrıca gözlenmelidir. İlk çalışma baytı0 ise tipli
envanter çocuğu zorunlu tutulmaz.

İki yeni REA analizi, yenilenmiş112-talimat koruma ve25-talimat slot gövdeleri
ile eşleşir. Eski/güncel iki ikilide bunlar,64-talimat caller ve19/16-talimat
opak string helper gövdeleriyle birlikte472 disk kaydı olarak doğrulanır.
String helper gövdelerinin kökenini doğrulamak onların native etkilerini
tamamlanmış saymaz. Gerçek slot çözümlemesi, isim araması, NPC seçimi,
serileştirme, sunucu etkileri ve canlı oyun uyumluluğu açık kalır.

16 yeni test; toplam3900 test geçti. Panel compiler girdi sayısı375 ve
bağlanmamış kontrol148 olarak kaldı. Tam fonksiyon/native/canlı sertifika yoktur.
