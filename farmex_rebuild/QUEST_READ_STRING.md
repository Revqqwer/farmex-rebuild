# Ad okuma yardımcısı: önekleri koruyan devam API'si

`QuestReadStringFrame(addressDWORD, countDWORD, initial_ansi, ...)`, 0045dca8
normal akışını kendi byte değerleriyle izler. Oyun veya yerel süreç belleğini
okumaz. Tüm girdiler açık yakalamalardır; native kod/DLL yüklemez.

Entry ve IsBadReadPtr normal dönüşünden sonra EAX ayrı beklenir. Nonzero EAX
doğrudan boş literal constructor yoluna gider; template ve memcpy yapılmaz.
Zero EAX yolunda512 byte sıfır template oluşturulur, verilen count kadar
yakalanmış byte kopyalanır. Count0 kopya çağrısını veya yaşam döngülerini atlamaz.

Kopya ve atama için `_prefix` receipt'leri outer normal dönüşlerden ayrıdır.
Kopya öneki tamamlanmışsa buffer saklanır; outer memcpy dönüşü beklerken yeni
byte yakalaması aynı kopyayı değiştirmez. Atama öneki tamamlandığında destination
değeri görünür; atama dönüşü, cleanup veya epilogue eksik olsa da geri alınmaz.
Normal cleanup sonrası kendi temporary değeri temizlenir, destination korunur.
Tamamlanma ve `owned_destination` dönüşü yalnız epilogue da bitince verilir.

Constructor ANSI sonucu varsayılan olarak açık immutable yakalamadır. Opt-in
`use_owned_cstring_model` sıfır template/buffer içinde ilk NUL'a kadar kendi
byte sonucunu üretebilir. Bu, native LStrFromPChar/codepage/refcount eşliği
değildir. Full512-byte kopyada NUL yoksa sonuç uydurulmaz: own türetme unresolved
kalır; gözlenmiş normal constructor sonucu ayrıca sağlanabilir. Readable
count>512 stack taşması çözülmemiştir; kopya kesilmez veya başarı sayılmaz.

Constructor normal dönüşü ayrıca gerekir. `temporary_ansi` constructor değerinin
kendi projeksiyonudur; yalnız destination_assigned öneki dış hedefteki bilinen
atamayı bildirir. Native heap/alias/yazma yarışları ve istisnalar modellenmiş sayılmaz.

17 yeni test ve toplam4977 test geçti. Önceki4960 full GUI'nin915 kod kaynağı,
385 import modülü ve yayımlanmış JSON byte'ları değişmedi; yeni iki dosya GUI
kapanımının dışındadır. Yeni GUI çalıştırılmadı. `QUEST_READ_STRING_VALIDATION.json`
kapsamı/log ve kaynak hashlerini tutar. İki PE'de334 instruction, guard/memcpy,
ANSI LStrFromPChar ve LStrAsg import zincirleri,512 sıfır template ve boş literal
doğrulandı. Eski kaynak/thunk adresleri sürüme göre raporda ayrı tutulur.

Bu API henüz lookup name_read üreticisine bağlanmadı. Sonraki iş, gerçek Al/Ver
akışındaki mevcut lookup'a bu alt üreticiyi bağlamak; ayrıca native RTL/SEH/
codepage/refcount, otomatik oyun gözlemleri ve canlı gönderim doğrulaması açıktır.
