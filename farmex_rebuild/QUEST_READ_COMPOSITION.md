# Ad okuma -> görev arama -> ANSI karşılaştırma -> Al/Ver

`QuestLookupObservation.name_reads`, iteration ordinal'ına göre typed
`QuestReadStringObservation` taşır. Lookup inline/indirect dallarında elde ettiği
copy address/count değerleriyle child reader'ı kurar. Mevcut opaque normal-return
yolu ayrıca korunur; her invocation/satırın kaynağı ilk girişte seçilip kilitlenir.
Bekleyen child, yalnız opaque outer normal receipt verilerek atlanamaz.

Reader'ın destination atama öneki, cleanup veya epilogue beklerken nested
planda görünür. Bu, lookup'taki name assignment'ın bittiği anlamına gelmez.
Önce child tamamlanır, sonra ayrı outer name_read normal dönüşü, ardından ayrı
name_assign normal dönüşü gerekir. Lookup ancak bu noktada `owned_name_values`
snapshot'ını yayımlar. Read/helper ve name assignment boşlukları filtreleri,
karşılaştırmayı ve ortak kuyruğu ilerletmez.

`use_read_name_operands=True` açık yerel politikası, typed ANSI karşılaştırma
sample'larında `use_owned_bytes=True` ise eksik left/right byte girdilerini
atanmış ad ve immutable argument-name snapshot'ından doldurur. Yakalanmış flag
yolu değiştirilmez; explicit operand'lar korunur. İkinci/fresh comparison kendi
explicit operand'ını kullanabilir. Köprü seçimi aynı satırda retry ile değişmez.
Opaque reader'dan bilinmeyen ad byte'ları uydurulmaz. Bu, native alias/codepage/
refcount ve eşzamanlı mutasyon eşliği değil, kendi immutable değer politikamızdır.

Gerçek Al/Ver düğmelerinde atama öneki görünürken pending cleanup'ın kuyruğu
bekletmesi, devamda atanmış `Low quest` adının ANSI karşılaştırmayı üretmesi ve
iki eylemin ortak kuyruğa ilerlemesi kontrol edilir. 13 yeni test; toplam4990
test ve tam GUI kaydı `QUEST_READ_COMPOSITION_VALIDATION.json` içindedir.
İki pinned PE'de2034 instruction, guard/copy/constructor/assignment import
zincirleri, zero-template, lookup/caller ve karşılaştırma yolları byte düzeyinde doğrulanır.

Hiçbir oyun/süreç belleği okunmaz veya değiştirilmez. Read/lookup/game
gözlemlerinin otomatik edinimi, native codepage/RTL/FPU/refcount/SEH ve gerçek
gönderim hâlâ açıktır. Stack overflow ve bilinmeyen C-string sonlandırması
başarıya çevrilmez; önceki API belgelerindeki "henüz bağlı değil" notları tarihseldir.
