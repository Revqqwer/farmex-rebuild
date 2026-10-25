# Görev string/kayıt üretimi çekirdeği

4776 Python testi geçti. Yeni GUI çalıştırılmadı: önceki4744 testli tam GUI'nin
358 import-closure modülü ve önceki paketin JSON verileri değişmedi. Yeni API/
test dosyaları bu closure dışında. QUEST_RECORD_VALIDATION.json kanıtı kaydeder.

QuestPreparedFrame, tamamlanmış aday elemesini QuestRecordFrame'e bağlar. Ret
edilen adayda isim girdileri tüketilmez; kabul edilmiş filtre prefix'i isim
boşluklarında yeniden örneklenmez. Sonuç ready_for_append'dir; kaynak vector'a
eklenmiş kayıt veya panel satırı değildir. Gerçek Yenile/clear/list/NPC/sort
yaşam döngüsü henüz bağlı değildir.

28byte düzen native copy constructor ve assignment ile tüketen kodda izlendi:

| Offset | Mantıksal değer |
|---|---|
|0x00|Kaynak scan indeksi|
|0x04|Kaynak görev data pointer'ı|
|0x08|Script ANSI string byte'ları|
|0x0c|Script kaynak storage DWORD'u|
|0x10|Sonradan yeniden okunan minimum-level byte, zero-extended DWORD|
|0x14|Görünen görev adı ANSI byte'ları|
|0x18|NPC adı ANSI byte'ları|

Scriptstorage, data+48'den gelir; string uzunluğundan yeniden hesaplanmaz.
Kaynak4d7cd8 constructor'ı ve4d72c0 assignment bu scalar'ı kopyalar. Seçili
Take4d5a8c NPC'yi+18'den, script'i+8'den alır; refresh display helper'ına+14'ü
gönderir. Mantıksal typed record, native managed-string pointer/refcount/ABI
serileştirmesi değildir; aynı offsetlerde byte nesnesi ve DWORD izdüşümüdür.

Üç string layout'u ayrıdır. Görünen ad, data+50 DWORD'u ile4d51f0 lookup sonucu
metadata+20 storage ve+10 data alanından; kısa dal50 byte. Script, kaynak görev
data+48 storage/+38 data; kısa dal15 byte. NPC adı, data+1c anahtarıyla4d52c0 /
4d526c lookup sonucu metadata+14 storage/+4 data; kısa dal15 byte. Bu caller'lar
storage'ı signed32 olarak16 ile karşılaştırır. High-bit storage bu nedenle
inline dal seçer. Mevcut item-name unsigned dalı körlemesine kullanılmadı.
Inline dalda data-pointer DWORD okuması yoktur; yalnız long dalda yapılır.

Display lookup0 için erken boş-string branch'i yoktur: storage/address/guard
gözlemleri hâlâ gerekir. Buna karşılık NPC helper metadata0'da54a071'deki gerçek
boş literalden döner; NPC string alanlarına devam edilmez. Guarded read/helper
sonuçları açık gözlemdir. IsBadReadPtr sonucu nonzero ise source boş literal
yolu; zero ise count kadar captured byte512-zero-template'e kopyalanır ve ilk
NUL'da ANSI içerik biter. Copy>512 veya NUL'suz512, native taşma/overread sonucu
tahmin edilmeden unresolved kalır. Gerçek pointer probe/memcpy yapılmaz.

String normal dönüşü, yönetilen assignment/temporary cleanup span'leri,
fresh minimum byte ve NPC helper dönüşü ayrıdır. Eski snapshot'ın tamamını
yeniden vermek gerekmez. Record alanları hazırken NPC inequality veya cleanup
eksikse prospective record korunur; append izni verilmez. Kaynak exclusion
literal'i [Familiar Tamer] Kate'dir. İnequality sonucu açık captured boolean'dır;
native RTL karşılaştırma/alias davranışı byte nesnesinden tahmin edilmez.

18 yeni test: üç layout/inline pointer skip, indirect count, signed high-bit,
root0 ile NPC0 ayrımı, bad-read/overflow/unterminated yolları, partial byte/
helper return, yedi alan ve raw storage, fresh minimum, prefix freeze, empty NPC,
exclusion cleanup ve aday->record kompozisyonu.3070 instruction kaydı iki PE'nin
refresh/copy/lookup/record/consumer gövdelerinde yeniden byte doğrulandı. Bu
sayı native sertifika veya tamamlanan fonksiyon/proje yüzdesi değildir.

Vector capacity/allocation/insertion, source strings'in refcount/ownership/SEH
etkileri, gerçek panel/NPC liste üretimi, Quest details/compare/selected Take/Give
ve otomatik current-game/runtime edinimi açıktır. Yeni REA decompile veya oyun
bellek/ağ/eylem IO yapılmadı. Önceki QUEST_CANDIDATE/QUEST_METADATA kayıtları
kendi önceki kapsamlarıyla korunur; canlı uyumluluk doğrulanmış değildir.
