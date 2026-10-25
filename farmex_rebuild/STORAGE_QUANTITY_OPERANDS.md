# Depo miktar yazıcısı — 19 Ekim 2026

19 Ekim uzun miktar kopyası:10/11karakter için değişmiş kaynak pointer ve sıralı BYTE gözlemleri bağlandı. Kopya verisi özgün metinden ayrı, eksik okumada hedef yazımı yok. **2551 test geçti (6.539 saniye)**. Mevcut222talimat kapsamı yeniden doğrulandı. UI değişmedi/tekrarlanmadı; native/canlı uyumluluk açık. Ayrıntı: [STORAGE_QUANTITY_SPILL.md](STORAGE_QUANTITY_SPILL.md).

`storage_quantity_operands.py`, 004653a8 normal miktar yazıcısının verilen gözlemlerle çağrı/yazım sırasını üretir. Yeni `StorageQuantitySamples`, mevcut `NativeHelperObservation.operand_samples` alanından item akışına bağlanır. Oyun belleği okunmaz veya değiştirilmez.

Önce signed DWORD miktarın normal decimal/ANSI dönüşümünün ayrı dönüş gözlemi ve eşleşen ANSI baytları gerekir. Bunlar verilmeden cache veya yazım planı tüketilmez. Kaynak IntToStr importu doğrulandı; native formatter/conversion/destructor etkileri doğrulanmadı. Bu sözleşmeye uymayan biçimler için sonuç uydurulmaz.

553d20 cache'i sıfırsa korumalı kök okumasının sonucu önce cache'e yazılmak üzere kaydedilir. Sonraki global ofset ve ADD işleminin taze cache girdisi ayrıca istenir. ADD sonucu DWORD'a sarılır. Kök null veya açık koruma başarısızlığı sonucu sıfır olabilir; source yine ofset ekler. Önceki store sonraki gözlem boşluğunda kaybolmaz.

Sonraki dört işlem hedef cache'i birbirinden bağımsız yeniden okur:

1. Hedefte 14 bayt sıfırlama isteği; ayrı memset dönüşü.
2. Tam miktar metnini kopyalama isteği; ayrı ilk memcpy dönüşü.
3. Taze hedef+10 alanına uzunluğun düşük baytını kopyalama isteği; ayrı ikinci dönüş.
4. Taze hedef+28 alanına sıfır bayt kopyalama isteği; ayrı üçüncü dönüş.

Ardından ANSI cleanup dönüşü beklenir. Bunların tamamlanması bile dış helper normal dönüşünün yerine geçmez; item caller ayrıca `normal_returned=True` ister. Eksik dönüşte yalnız o noktaya kadar ulaşılan yazım istekleri gösterilir; bunlar gerçekten yazılmış baytlar sayılmaz. Eski sabit sözlük modeli ayrı kalır.

Kaynak başlangıçta sekiz baytlık tampon hazırlar. Dokuz karakterlik metinde son bayt, tamponun devamındaki saved source pointer'ın düşük baytına yazılır. Aynı iterasyonda kaynak bayt önce okunur ve bundan sonra döngü biter; sonraki memcpy saved pointer yerine LEA tampon adresini kullanır. Bu normal yolun dokuz karakterlik çıktısı modellenir. On veya on bir karakterde değişmiş pointer tekrar okunur; gerekli adres/değer gözlemleri olmadığı için bu yollar **unresolved_stack_buffer_overwrite** kalır. Native güvenlik veya sağlıklı dönüş sonucu çıkarılmaz.

15 yeni test dahil **2541 test, 7.402 saniye** geçti. Dört farklı hedef, sıfır cache'in iki yazımı, taze ADD girdisi, null/başarısız kök, DWORD taşması, ara dönüş boşlukları, format sözleşmesi, dokuz karakter ve çözülemeyen uzun yollar denetlendi. Yeni model API üzerinden kullanılır; UI gözlem alanı eklenmedi.

İki korunmuş ikilide 222 talimat kaydı disk baytlarıyla ve IntToStr/_memset/_memcpy importlarıyla doğrulandı. Frame setup ve geçici cleanup sınırları opaktır; hedefleri sabitlenmiş olsa da gövdelerinin eşdeğerliği bu kapsamda kanıtlanmadı. Kapsam önceki denetimlerle örtüşür. Bu Ghidra/disk kanıtıdır, REA Evidence değildir.

Güncel host süreç sorgusu 19 Ekim 04:06:37 UTC'de 274 süreç içinde exact KnightOnLine/FarmexBot/Loader eşleşmesi bulmadı. Bu, geçmiş erişim engelinin çözüldüğü anlamına gelmez. Canlı aktarım, native kopyalama/formatting/cleanup etkileri ve gerçek oyun uyumluluğu hâlâ açıktır.
