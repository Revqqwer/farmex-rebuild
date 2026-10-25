# Görev arama: normal tarama devam API'si

`QuestLookupFrame`, 004d642c kaynağını signed kapsayıcı DWORD sınırlarıyla
adım adım izler. Normal bitişte FFFFFFFF üretir; fakat entry, argument-copy,
ulaşılan tüm satır/helper adımları ve argument-cleanup tamamlanmadan EAX vermez.
Al/Ver caller üreticisine henüz bağlanmadı. Oyun belleğini okumaz veya kod çalıştırmaz.

Her normal receipt/değer `(iteration, role)` token'ı ile sağlanır. Argument
yaşam döngüsü `(-1, role)` kullanır. Tamamlanmış çağrı yeniden üretilmez;
normal receipt geldiğinde EAX gözlemi eksikse aynı çağrının değerini bekler.
Sayaç DWORD sarınca yeni ordinal farklıdır; eski turun cache'i kullanılmaz.
Kendi step-budget politikası yalnız devamı böler, kaynak bitişi sayılmaz.

Bir turda kayıt lookup'ı, record+50 anahtarı ve metadata lookup'ı ayrıdır.
Null record veya metadata sonraki tura geçer. Name storage metadata+20'den
signed okunur: >=16 ise metadata+10'dan pointer ve raw storage kadar kopya;
diğer durumda metadata+10 inline adresi ve15 byte istenir. Bu helper'ın inline
sayısı, başka refresh-display yolundaki50 byte ile karıştırılmaz. Temp init,
read span, assignment, temp cleanup ve name compare ayrı normal gözlemlerdir.
Native string okuyucusu, kod sayfası, refcount veya ANSI RTL karşılaştırması
yerine kendi metin eşitliği konmaz; compare EAX/AL açık yakalamadır.

Ad karşılaştırmasının AL'si sıfır değilse nation gate/value iki ayrı fresh
record+19 okumasıdır. Gate3 current-query'yi atlar; diğer durumda ikinci lowBYTE,
current helper'ın tam DWORD'u ile karşılaştırılır. Class gate/value da iki
ayrı record+18 okumasıdır; gate5 özel, diğer karşılaştırmada iki lowBYTE kullanılır.
Uyumsuzluk, mode okumasına gitmeden name cleanup'a gider.

Record+24 mode byte'ı yalnız bu filtreler geçince okunur ve mode DWORD'u ile
karşılaştırılır. Eşleşme başarı dönüşü üretmez; kaynak CMP'den sonra başarı
dallanması yoktur. Name cleanup ardından sayaç artar. Üst sınır INT32_MAX ise
DWORD sarması normal aralık çıkışı sağlamaz; model sonraki gözlemi bekler.

15 yeni test ile4923 test geçti. İki pinned PE'de384 lookup instruction kaydı,
ayrıca önceki464 kayıtlık normal dönüş/caller kanıtı kaynakları doğrular.
`QUEST_LOOKUP_VALIDATION.json`, kaynak ve log hashlerini içerir. Yeni GUI yok:
önceki4908 full GUI'nin909 kod kaynağı ve381 import modülü değişmedi; iki yeni
dosya bu kapanımın dışındadır. Önceki yayımlanmış JSON'lar da byte eşitliğiyle kontrol edildi.

Açık işler: Al/Ver lookup üreticisi birleşimi, read/string/helper acquisition,
native ABI/refcount/SEH/abnormal yollar, gerçek oyun gözlemleri ve gönderim.
Normal-return kanıtının runtime patch/başka sürüm/nontermination sınırları
`QUEST_LOOKUP_RETURN.md` içinde korunur. Test sayısı tamamlanma yüzdesi değildir.
