# Relog seçim çağrıları ve denetleyici bağı

`relog_selection.py`, dört kaynak wrapper'ın normal pointer/argüman akışını
modeller. Bütün okumalar ve çağrılar ham gözlem veya kayıt olarak kalır; gerçek
fonksiyon adresi, süreç belleği, VCL/oyun nesnesi ya da native dispatch çalışmaz.

| Tür | Yordam | Kaynak hedef ve fiziksel PUSH sırası |
|---|---|---|
|İlk seçim|41272c /36talimat|Guarded base+5541d4+(argument*5541e0 düşük32bit) ile item; **taze doğrudan** object zinciri; vtable+554200 değerindeki hedef; PUSH(10000000hex,item).|
|İkinci seçim|41279c /13talimat|Taze doğrudan object zinciri;553f40 globalindeki doğrudan fonksiyon adresi; PUSH(argument). Guarded chain veya vtable offset araması yok.|
|Onay|4127c4 /33talimat|Guarded base+5541bc ile item; taze doğrudan object zinciri; vtable+554200 hedef; PUSH(1,item).|
|İlerletme|4126f4 /20talimat|Taze doğrudan object+5541d0 değeri item olur; aynı object vtable+554200 hedef; PUSH(1,item). Guarded helper yok.|

İlk/onay yollarında erken45dc44 yardımcı zinciri ile sonraki doğrudan root/object
zinciri ayrı gözlemlenir. Aynı global slot ve offset'in önceki sonuçları yeniden
kullanılmaz.554200 globali callable mutlak adres değil, **vtable offset** değerini
tutar. İkinci yolun553f40 globali ise doğrudan callable hedef değerini tutar.
Kayıtlarda ECXobject, hedef ve fiziksel PUSH sırası ayrı etiketlidir. Gerçek ABI,
callee stack cleanup, register/flag koruması veya native RET doğrulanmış sayılmaz.

DWORD indeks/stride çarpımı ve adres toplama düşük32bit tutulur. Kaynakta olmayan
indeks sınırı veya zero-pointer early exit eklenmez; sıfır adres/target kayıtları
gerçek çağrıya dönüştürülmez. Opaque dispatch normal dönüşünden sonra ham fullEAX
ve ayrı frame çıkış gözlemi gerekir.

`RelogControllerSelectionsFrame`, denetleyicide istenen `advance`, `select_first`,
`select_second`, `confirm` çağrılarını tipli alt modellere bağlar. İndeks argümanı
yalnız ulaşılan parent çağrısından türetilir; bağımsız child override yoktur.
Alt giriş kaynak kenarından türetilir, normal dönüşler türetilmez. Alt model ve
dış wrapper dönüşü ayrı gerekir. Sonraki seçim okuması child dönüş değerinden
veya çağrının tamamlanmasından oluşturulmaz. Eksik gerçek gözlem beklenir.

Birden fazla alt model tek denetleyici turunda sırayla bağlanabilir; hiçbiri
erken parent receipt ile atlanamaz. Önceki tamamlanmış alt izler korunur. Bir kez
bağlanan eksik child, gözlemi boş bırakarak opak çağrıya çevrilemez. Tüketilmiş
opak dönüşe geriye dönük bağlama reddedilir. İstenmeyen eski opak sınırlar API
olarak korunur; bu sınırların semantiği doğrulanmış sayılmaz.

Dört yeni REA analizi, mevcut290talimatlık denetleyici analizi ve iki sabitlenmiş
disk sürümü karşılaştırılır: toplam784ayrık talimat kaydı. Bu102wrapper+290caller
talimatının çıkarım doğruluğudur; native davranış veya tam fonksiyon sertifikası
değildir. Gerçek hook/oyun ABI, seçim teslimi ve canlı uyumluluk açık kalır.
