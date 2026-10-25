# Relog karşılaştırma ve callback kurulum geçidi

`relog_gate.py`, `00412874` içindeki181talimatın normal kontrol yollarını
tamamlayan yerel modeldir. Önceki callback-slot modeli yalnız kurulum alt
aralığını kapsıyordu. Bu genişletme tam fonksiyon/native/hook sertifikası değildir.
Yeni412828/16talimat ve412858/10talimat wrapper yolları `relog_selection.py`ye
eklendi; mevcut dört wrapper için önceki izole native kanıt tarihsel olarak kalır.
Yeni iki wrapper henüz native çalıştırılmadı.

| Aşama | Kaynak davranış |
|---|---|
|Başlık|553f64 guardedroot;5541e4 base;5541ec/f0/f4 nesneleri ve ilk nesnenin5541fc byte'ı **base0 kontrolünden önce** okunur.|
|Kurulum denemesi|553c84 sıfırsa probeAL0 ve signed yerelDWORD>90 kurulum sınırına götürür.553e80->5540d4context->table,554204slot offset;554218 slot yazımı, ardından **taze554218 okuması** ve466b8fc(46f520,freshslot,554228). Helper dönmeden attempted bayrağı yazılmaz; probe geçmezse de attempted1 olur.|
|Tek seferlik iş|553e7c/553fec byte ALnonzero ve553c85=0 ise4f95d0; normal dönüşten sonra553c85=1 ve asıl callback'e geçiş.|
|Pasif|İlk kaydedilmiş UI byte AL1 gerekir.50b2d9 ve pending562208 ikisi de0 ise fazın tazeAL1 veya ikinci tazeAL2 okuması412858'e gider. AL4 bu pasif yolda olumlu değildir.|
|Aktif karşılaştırma|Etkinlik veya pending olumluysa fazAL5 durumunda553f6c/helper sonucu taze50b2d4 ile karşılaştırılır. İlk eşitlik ilk nesneyi412828'e verir. Fark varsa her iki değer yeniden okunur; unsigned küçükse son nesne seçilir.|
|Aktif fallback|Karşılaştırma seçim üretmezse üç bağımsız faz okuması sırasıyla1,2,4 arar. İlk olumlu sonuç412858'e gider; kalan okumalar yapılmaz.|
|Asıl callback|Her normal yol taze553f64 slot/root ve5541e4 object,554224target zincirine ulaşır; EAXtarget/ECXobject opak çağrı, hamfullEAX ve ayrı frame dönüşü gerekir.|

50b2d4 karşılaştırmaları412ed0 snapshot yazımıyla byte-backed olarak bağlanır.
Etkinlik/pending OR kısa devresi ve bütün tekrar okumalar ayrı gözlemlerdir.
Önceki store değeri sonraki global read yerine konmaz. Kurulumun başarısı,
probe birimi veya kıyaslanan değerin canlı sunucu/karakter anlamı varsayılmaz.

İki yeni wrapper:

- `ui_select /412828`:553f64 root+5541e4object, vtable+554200 hedef;
  ECXobject ve fiziksel PUSH(1,argument). Argüman ulaşılan geçit çağrısından türetilir.
- `ui_advance /412858`:553f64 slotundan okunan **root doğrudanECX** olur;
  object offset'i okunmaz.553f74 doğrudan fonksiyon adresidir; stack argümanı yoktur.

`RelogGateSelectionsFrame` bu iki çağrıdan yalnız ulaşılanı tipli child olarak
bağlar. Child girişleri türetilir; child normal/EAX/frame ve dış dönüş ayrı kalır.
Eksik child parent receipt ile atlanamaz. Önceki controller/selector API ve
argüman biçimleri korunur. Gerçek call, patch, pointer dereference veya game
callback çalışmaz; tüm native etkiler opak niyet/gözlem sınırıdır.

Üç yeni REA ve mevcut snapshot analizi iki sabitlenmiş sürümle karşılaştırılır:
181+16+10+12function talimatı veSleepEx thunk'ı, toplam440ayrık byte kaydı.
Callback kurulumu, native ABI/SEH, seçimlerin oyun tarafından uygulanması ve
canlı uyumluluk açık kalır.
