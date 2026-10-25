# Alış pazarı hazırlığı

Güncel coin bağı: `coin_inputs`, ayrı typed `SourceCoinObservation` üzerinden
iki guarded DWORD normal yolunu kendi gözlemlerinde hesaplayabilir; ham coin EAX
ile karıştırılmaz. Eksik zincir threshold kararından önce bekletir. Native okuma
yapılmaz. Ayrıntı: [SOURCE_COIN.md](SOURCE_COIN.md). Aşağıdaki ham EAX yolu da sürer.

Sonraki açma bağlantısı: Hazırlık sonrası kayıtlar `merchant_open.py` ile en fazla12satırlı tampon ve iki ayrı yerel kuyruğa aktarılabiliyor. Kaynakta görülen korumalı sıfır yazma/memset çağrıları yalnız plan; oyun belleğinde yürütülmez. Native caller prefix ve gerçek producer/ACK hâlâ açık. Ayrıntı: [MERCHANT_OPEN.md](MERCHANT_OPEN.md).

Sonraki liste hazırlama bağlantısı: `merchant_preparation.py` ve `BuySetupObservation.preparation_inputs`, aşağıda dış gözlem olarak anılan `0041dec8` normal yolunu yerel kayıt/string/helper gözlemleriyle yeniden kurar. UI hazır satırı doğrudan üretmek yerine bu zinciri kullanır; panel seçeneği açıksa ListView satırları bağlanır. Fiyat QWORD'u korunur, bütçe hesabına düşük DWORD geçer. Native VCL/heap/exception ve oyun etkileri uygulanmaz. Ayrıntı: [MERCHANT_PREPARATION.md](MERCHANT_PREPARATION.md). Aşağıdaki ham gözlem yolu da desteklenir.

`merchant_setup.py`, `0042070c` boş-yuva sayacını ve `00420740` alış pazarı hazırlık kararını gözlemlerden hesaplar. Native hazırlık, çanta okuma veya oyun işlemi çalıştırmaz. `operation_engine.py` içindeki BUY runner bu hesapları isteğe bağlı olarak kullanır; mevcut ham helper-sonucu girişi de korunur.

## Kaynak sırası

Hazırlık önce `0041dec8` liste hazırlama yardımcısını çağırır. Model bu yardımcının **normal dönüşünü ve dönüşten sonraki satırları** ister; panel satırlarını kendiliğinden hazırlanmış liste saymaz. Yardımcının kendi string/list/allocator yan etkileri uygulanmış değildir.

Ardından `0042070c`, mutlak çanta yuvaları 14..41 için 28 ayrı `004634a4` item-ID sonucunu alır ve sıfır sonuçları sayar. Önceki Upgrade item modelinin yakalanmış DWORD okuma zinciri her yuvaya ayrı bağlanabilir. Eksik gözlem sıfır sayılmaz. Native korumalı getter'ın döndürdüğü sıfırın gerçek boş eşya mı yoksa okuma başarısızlığı mı olduğunu bu model ayıramaz.

Kaynak daha sonra `0046258c` para okuyucusunu çağırır; boş-yuva eşik kararından **önce** coin EAX gözlemi gerekir. Coin kaynağı iki korumalı DWORD okuma kullanır; bunlar bu API içinde yürütülmez.

Boş-yuva sayısı signed DWORD eşikten küçük veya eşitse sonuç 1 olur. Diğer durumda hazırlık sonrası listedeki satırlar sırasıyla değerlendirilir:

1. Her döngüde önce taze vector-count sonucu gerekir. Açık `stable_rows=True` verilirse çağıran sabit snapshot varsayımını kabul eder; aksi halde her koşul için ayrı `vector_counts` gözlemi gerekir. Count helper'ının gerçek pointer farkı/string/heap işlemleri yürütülmez.
2. İndeks sayıya ulaşmışsa veya kalan boş yuva sıfırsa durulur. Son boş yuva tüketildikten sonra da bir sonraki count koşulu kaynakta önce gelir.
3. Satırın item DWORD'u okunur, fakat bu karar hesabında kullanılmaz. Adet ve fiyat çarpılır; IMUL sonrasında EDX sıfırlandığı için maliyet çarpımın yalnız düşük DWORD'udur. Bu taşma, alışverişin ekonomik olarak geçerli olduğu anlamına gelmez.
4. Maliyet kalan coin'den büyükse satır atlanır. Karşılanıyorsa bütçe azaltılır, bir boş yuva tüketilir ve sayaç artar. Daha sonraki satırlar yine değerlendirilir; ilk pahalı satır bütün hazırlığı durdurmaz.

En az bir karşılanan satır sonuç 0, hiç karşılanan satır olmaması sonuç 2 üretir. Bu kodlar yerel hazırlık kararıdır; eşya satın alma veya sunucu onayı değildir. Sıfır adet/fiyat/item gözlemleri kaynak DWORD hesabına göre kabul edilir; bu API'ye ürün kuralı eklenmedi. Genel panel `MerchantRow` doğrulaması ayrıca daha dar giriş kurallarına sahiptir.

## Runner ve arayüz bağlantısı

`MerchantSnapshot.buy_setup_inputs`, BUY phase2'de `setup_result` yerine bağlanabilir. İkisi aynı ulaşılan dalda verilirse hata olur. Eksik hesap `needs_adapter` döndürür; `setup_seen` veya phase ilerletilmez. Tamamlanan sonuç mevcut hazırlık kapısına ve hata politikasına aktarılır. Her tick ayrı bir gözlemdir; bu saf plan native çağrıların yapıldığını veya kısmi etkilerin geri alındığını iddia etmez.

`buy_inventory_inputs`, BUY izleme dalında `buy_free_slots` yerine taze 28 yuva hesabını sağlar. Bu bağlı yolda eşik signed DWORD yorumlanır: örneğin `0xffffffff`, -1 anlamına gelir. Genel runner'ın diğer saat, yeniden açma, bildirim ve stop davranışları önceki yerel politikalardır; bu ekleme bütün Merchant caller'ını native eşdeğer yapmaz. Ham sonuçla bağlı gözlemin birlikte verilmesi ulaşılan dalda reddedilir.

“Buy Merchant” denemesinde **Alış pazarı için örnek hazırlık/çanta gözlemleri** varsayılan kapalıdır. Kapalıyken hazırlıkta eksik gözlem bildirilir; önceki sabit `setup_result=0` kaldırıldı. Açık örnek, coin, boş yuva ve eşiği kullanır. Liste hazırlanmış sabit tek satır örneği olarak alınır; çanta ID sonuçları bu denemeye aittir. “Çanta dolu” sıfır boş yuva üretir. Eşik yeni deneme başlatılırken alınır. SELL denemesi bu eklemede değiştirilmedi.

## Kanıt ve kalan sınırlar

`work/audit_merchant_setup.py`, eski ve güncel Richard dosyalarında dört gövdenin 588 talimat kaydını ve izleme caller'ındaki signed eşik bağlamının 16 kaydını doğruladı: toplam 604 kayıt. Karar, boş-yuva sayacı ve para getter'ı byte olarak aynı; liste hazırlığının import çağrılarında değişiklikler vardır ve hazırlık etkileri modellenmiş sayılmaz. 15 aritmetik/sıra anchor'ı ve dört çanta tarama anchor'ı ayrıca denetlendi. Kayıt: üst çıktı dizininde `FarmexBot_alis_pazari_hazirlik_kod_kaniti.json`. Ghidra kayıtları REA Evidence veya canlı çalışma izi olarak sunulmaz.

Gerçek çanta, coin, hazırlanmış liste, oturum flag'leri, zaman örnekleri, native ABI, paket aktarımı ve sunucu sonucu doğrulanmadı. Yeni bir bot üyeliği veya hesap bilgisi bu yerel hesap için gerekmedi.
