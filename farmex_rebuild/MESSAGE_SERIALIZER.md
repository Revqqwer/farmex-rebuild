# Mesaj paketleme kapsamı

`message_serializer.py`, REA ile incelenen Richard `004c9b74` normal yolunun kendi belleğimizde çalışan sınırlı modelidir. Gerçek oyuna paket göndermez. `SerializedChannelCycleFrame`, zaman döngüsü → kanal seçimi → paketleme → kendi kuyruk kaydı zincirini ayrı yardımcı/üst çağrı dönüşleriyle birleştirir.

Paket `10` başlığıyla başlar. Tanınan mode değerlerinde ardından bir wire BYTE, küçük endian uzunluk WORD ve yakalanmış metin baytları gelir. Mode→wire eşlemesi: `0→1, 1→5, 2→3, 3→6, 4→14, 5→15, 7→7 … 17→17, 34→34`. Mode6,18–33 ve unsigned34 üzerindeki değerler yalnız başlıkla kuyruk çağrısına ilerler. Kanal yardımcısındaki `0/2/3/1/4/34`, wire üzerinde `1/3/6/5/14/34` olur.

Argüman kopyasından sonra mesaj parametresi yeniden okunur; sıfırsa `005479b4` boş CString adresi seçilir. Yerel string uzunluğunun WORD okuması, boşluk kontrol DWORD'u, kopyalama DWORD'u ve kopyadan sonraki indeks artışı birbirinden ayrı gözlemlerdir. Bu değerler eşit varsayılmaz. String/data/memcpy/cleanup ve enqueue normal dönüşleri ayrı kalır. Kuyruk kaydı oluşup daha sonraki cleanup beklerse kayıt tekrarlanmaz.

Kaynakta görünür uzunluk sınırı yoktur. Nominal paket alanı512 bayttır; ardından yalnız daha önce tüketilmiş dört baytlık CString pointer yereli gelir. Canlı indeks paket+516 adresindedir. Model, header sonrası512 bayta kadar kopyayı (toplam516 bayt) kapsar; indekse taşan kopyaları `source_stack_alias_copy` olarak açık bırakır. Bu, orijinalde bir güvenlik kontrolü bulunduğu iddiası değildir. Oluşturulmamış bir kuyruğa alınacak kuyruk sonunu da sıfırlarla doldurmaz: `uninitialized_enqueue_tail` ile bekler. Tam stack alias davranışı, exception yolları, native string/CRT/heap davranışı ve gerçek gönderim doğrulanmamıştır.

13 yeni test:18 mode, default delikleri, null pointer seçimi, bağımsız uzunluk okumaları,512/513 sınırı, eksik baytlar, sıfır kopya, indeks taşması, cleanup beklemesinde prefix ve kuyruk idempotansı, gate0 ve birleşik çağrı zinciri. Tam Python koşusunda4010 test geçti. Önceki UI kaynakları değişmedi; bu API modeli gerçek Flood paneline bağlanmış değildir.
