# Yeniden giriş aşama denetleyicisi

`relog_controller.py`, `00412adc` içindeki290talimatın normal kontrol yollarını
ham gözlemlerle modeller. UI, native callback, bellek, seçim, giriş veya ağ
işlemi yapmaz. Özellikle hazırlık yardımcısı41245c opak kalır; hesap/parola
değerleri, stringleri veya runtime giriş tamponları okunmaz.

| Aşama | Kaynak koşul ve sıra |
|---|---|
|Ön işlem|553e3c etkinse taze553e40 ile SleepEx fiziksel PUSH(0,delay). Üç ayrı byte kapısından sonra signed64 fark en az5000 ise42732c sınırı.|
|Başlıklar|553f3c kökü ve5541a0 offset'i iki kez taze okunur; ikinci zincire+8 eklenir. İki ek base dereference ve beş base+offset object helper'ı tüm UI kararlarından önce çalışır; kullanılmayan yerel dönüşler de ayrı gözlenir.|
|Hazırlık|UI byte **AL tam1**, etkinlik veya taze pending bayrağı ve signed64 fark>=5000 gerekir. Yeni timestamp **553e46 mod kontrolünden önce** kaydedilir. Mod tam1 ise41245c opak çağrısı gelir.|
|İlerletme|İlk UI byte AL1 ise ikinci UI okunmaz; aksi halde ikinci AL1 aranır. Etkinlik/pending kısa devresi olumluysa4126f4 çağrısı gelir.|
|İlk kurulum|553c8c sıfırsa4e2bc8 probe'u çalışır. AL0 ve signed yerelDWORD>90 ise466b8fc(412874,target,554224) sınırı gerekir. Ardından553c8c=1 olur ve doğrudan asıl callback kuyruğuna gidilir; sonraki seçim aşamaları atlanır.|
|Alternatif hazırlık|İlgili UI AL1 iken555e6c ilk okuması0 ise553c88 sıfırlanır,4c6a24 çağrılır. Mod1/etkinlik/taze555e6c ve5000ms kapısı olumluysa4c6934,4123b0,4126b8 sırası; yeni timestamp ve **taze** counter+1 yazımı vardır. Önceki sıfırlama yeni counter gözlemi yerine kullanılmaz.|
|Birinci seçim|Ayrı etkinlik/pending ve seçim UI AL1 gerekir.5541d8 alanı0 ise taze50b2cc ile41272c çağrılır. Aynı alan taze offset ve helper sonucuyla yeniden okunur; hâlâ0 ise sonraki seçime gidilmez.|
|İkinci seçim|5541dc sonucu taze50b2d0 ile karşılaştırılır. Farklıysa **tekrar okunan**50b2d0 argümanı41279c'ye gider. Sonra alan ve istenen değer yeniden okunur; eşitlik oluşmadan onaya gidilmez.|
|Onay|Signed64 fark>=30000 gerekir.553e84 kökü/5541f8 byte sonucunun AL değeri1 değilse4127c4 ve ayrı post-tick timestamp yazımları gelir.|
|Asıl callback|Bütün normal yollar553f3c slot->doğrudan root->taze5541a0 object ve554220 target zincirine ulaşır. EAXtarget/ECXobject ile opak çağrı kaydedilir. Tam EAX dönüşü ve frame çıkışı ayrı gerekir.|

Üç zaman kapısı tick ve düşük/yüksekDWORD'ları bağımsız okur; negatif64bit
farkları atlar. Sayaç sarılması32bit geçen süreye dönüştürülmez. Tekrar okunan
bayrak/offset/hedefler ayrı etiketlidir; bir önceki helper dönüşünün UI'ı veya
oyun alanını değiştirdiği varsayılmaz. Eksik sonraki gözlem önceki store/call
öneklerini korur. Tüm pointer aritmetiği düşük32bit tutulur.

50b2cc/d0 tüketimleri önceki412ed0 snapshot producer'ının yazdığı alanlarla
byte-backed olarak eşlenmiştir. Bu eşleme semantik olarak geçerli canlı
sunucu/kanal değerlerini veya başarılı oturum açıldığını kanıtlamaz.

Yeni REA290talimatlık controller analizi ve mevcut12talimatlık snapshot analizi
eski/yeni sabitlenmiş modüllerle karşılaştırılır. SleepEx ve GetTickCount import
kimlikleri gerçek PE thunk'larından çözülür. Toplam608ayrık talimat kaydı byte
doğrulanır. Native yardımcılar, dolaylı hedef ABI'si, callback/hook kurulumu,
exception/SEH, tam fonksiyon davranışı ve canlı uyumluluk açık kalır.
