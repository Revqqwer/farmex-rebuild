# Tek tarama actor/item üreticileri

`merchant_quick_source.py`, bitmiş isim metadata'sı vermek yerine explicit lookup/read/copy gözlemlerinden tek tarama snapshot'ını üretir. Gerçek Tara düğmesinin sağlayıcısı `QuickSourceSnapshot` da döndürebilir. Bu bir süreç okuyucusu değildir; native lookup/float dönüşleri ve yakalanmış byte aralıkları hâlâ açık girdilerdir. Hiçbir normal dönüş veya boş lookup eksik girdiden türetilmez.

Item üreticisi mevcut base/extension lookup modellerini çağrı argümanları ve ayrı normal/EAX gözlemleriyle birleştirir. Resolver için lookup+4, isim kategorisi için extension+4c, extension ID için extension okunur. İsim kategori0/2/5/11 ise lookup'un1c/c storage/data alanlarından; diğerlerinde extension'ın18/8 alanlarından alınır. Bu nedenle kategori1'i başka name-helper'ın aile kuralıyla değiştirmez. Data DWORD inline durumda da okunur. Unsigned storage16 ayrımı, pointer/count veya inline255 byte copy isteği üretir.

Ortak `game_text` modeli, açık read-probe sonucu ve tam byte aralığını512 sıfırlı tampon/ilkNUL kuralıyla işler. Eksik capture boş ad sayılmaz. Okunamaz gözlemi source empty fallback'ini verir; büyük/unterminated native buffer sınırları unsafe davranış yürütülmeden unresolved tutulur. Copy'den sonra kaydedilen kategori fresh ve ayrıdır. Burada codec/decode yoktur; suffix ve Unicode tablo çözümlemesi sonraki mevcut katmanlardadır.

Actor üreticisi lookup normal dönüşünden sonra active byte'ı kontrol eder. İki buyer okuması için iki ayrı offset/EAX tüketilir; carry byte korunur. Kullanılmayan entity ID okuması atlanmaz. X/Y float-reader ve ftol normal dönüşleri ayrıdır; EAX'lar açık yakalanır. Seller storage/data okumaları, inline yolda fresh name offset ve exact copy aralığı source sırasını korur. Dört cached ID bitmeden ilk item metadata'sına geçilmez.

Üreticiler ilk eksikte durur; önceki own alan ve metadata önekleri korunur. Birinci nonempty slot'un metadata'sı hazırken direction hâlâ bilinmiyorsa sonraki slot üretilmez. Actor'lar arasında carry aktarılır. Root üretici sonraki actor'ı kaynak akışı ulaşmadan tüketmez. Ortaya çıkan ham snapshot, mevcut quick projection/decode/filter/search/table katmanına verilir; son UI commit için hem üretim hem gerekli decode girdileri tamamlanmalıdır.

LookupEAX0 otomatik boş item değildir; source'un sonraki read-helper gözlemleri ayrıca gerekir. Source read helper'larının page-protection ve native string allocation/lifetime/SEH yan etkileri yürütülmez. `complete`, kendi captured-value üretiminin tamamlandığıdır; native parent-helper receipt veya canlı uyumluluk sertifikası değildir.

Kaynak kanıtı `FarmexBot_merchant_tek_tarama_ureticileri_kaniti.json`, iki Richard sürümündeki quick gövdesi/callback referansına ek altı lookup/copy/read yardımcısını disk byte'larıyla sabitler:4490 instruction kaydı. Gözlem kaynaklarının oyundan otomatik edinimi ayrı açık iştir. Güncel Python/GUI kaydı `MERCHANT_QUICK_SOURCE_VALIDATION.json` içindedir.
