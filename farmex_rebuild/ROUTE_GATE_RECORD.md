# Gate kayıt veri akışı

4630 Python testi geçti. Yeni API kodu app/smoke_ui import closure dışında;
4620 aşamasının tam GUI kaynak ve log hashleri aynıdır. Yeni GUI çalıştırılmadı.
ROUTE_GATE_RECORD_VALIDATION.json kapsamı sınırlar; gerçek kayıt kutucuğu,
paket sağlayıcısı ve rota listesi birleştirmesi henüz bağlı değildir.

| Paket ilk byte | Kayıt koşulu / parametre | Oluşan satır |
| --- | --- | --- |
|20 / alt byte01|Kayıt açık, ilk fresh zone32 veya ikinci fresh zone33; offset2 WORD ID>0; actor lookup nonzero; ad üretiminden sonra raw storage15 ve exact ANSI [Teleport Gate]|Delos Gate Open / - / -|
|33|Kayıt açık; offset1 DWORD unsigned|Gate Open / sayı / -|
|4b|Önce clock ve561f74/561f78=(tick,0), sonra kayıt açık; offset1 DWORD unsigned|Gate / sayı / -|
|55|Kayıt açık ve fresh zone koşulu; offset1 BYTE zero-extended|Delos Gate / sayı / -|

Zone çağrıları ayrı/fresh gözlemlerdir: ilk32 ise ikinci okunmaz; ilk33 tek
başına yetmez, ikinci33 olmalıdır. NPC ID0, actor0, storage!=15 veya ad
eşleşmemesi satır eklemez. Storage filtresi ad üretiminden sonradır.
Signed storage>=16 ise ad read count ham storage; aksi durumda50'dir.
Bu, manuel NPC ekleme callback'inin255 byte inline yolu değildir.

Kayıt kapalı4b dalı yine saat yazma intentini üretir. Model kendi writes
listesini tutar; oyun belleğine yazmaz. Başlangıçta kayıt kapalı diğer
dallar sonraki parser/zone/name verilerini tüketmez.33/4b kaynak biçimi
UTF16 %lu,55 biçimi %i'dir. FFFFFFFF unsigned4294967295 olarak tutulur.

Parser/lookup/name/karşılaştırma/formatter normal dönüşleri açık gözlemdir.
Name üreticisi bu aşamada opaque captured span'dir; pointer/copy/RTL
yürütülmez. Add/caption, formatter dönüşünden öncedir; bekleme tek satır
önekini korur. Tamamlanan adımlar poll ile yinelenmez. Silinen satırın
yerine geçen nesneye geç alan yazılmaz; cancel terminaldir. Kısa sağlanan
packet aralığı unresolved kalır; kaynakta kanıtlanmış uzunluk guard'ı yoktur.

İki pinli Richard sürümünde1508 instruction kaydı doğrulandı. Eski callback
004e3128, yeni004e3144'tür; yardımcı adresleri gerçek callsite'larından
ayrı çözülmüştür. Form+9a8 rota listesi, form+9e8 kayıt kutucuğudur.
ANSI comparison import'u LStrCmp; sabit ad/başlıklar ve format literal'leri
dosya byte'larıyla doğrulandı. Yeni başarılı REA decompile çağrısı yoktur.

complete yalnız kendi record veri dalını kapsar. Parent dispatcher return,
diğer opcode yan etkileri, native VCL/string lifetime/SEH/heap/istisnalar,
otomatik paket/helper edinimi ve canlı uyumluluk tamamlanmış sayılmaz.
Oyun/ağ erişimi ve oyun eylemi0.
