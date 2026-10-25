# Görev yenileme: aday eleme çekirdeği

4758 Python testi geçti. Yeni GUI çalıştırılmadı:4744 testli önceki tam GUI'nin
358 app/smoke import-closure modülü hash düzeyinde değişmedi. Yeni iki API/test
dosyası bu closure dışında. QUEST_CANDIDATE_VALIDATION.json kapsamı kaydeder.

Bu aşama004d6668 yenilemenin yalnız bölge karşılaştırma sonuçlarını ve tek aday
eleme zincirini modeller. Gerçek Yenile düğmesine bağlı değildir; liste temizleme,
managed string/vector prefix, isim/script edinimi, kayıt oluşturma, NPC unique
liste ve son sort/cleanup henüz uygulanmış sayılmaz. eligible_for_name_stage
yalnız sonraki isim aşamasına geçilebildiğini söyler; görüntülenmiş görev değildir.

Kaynak önce NPC combo'yu temizleyip HEPSI ekler ve ItemIndex0 setter'ını çağırır;
sonra görev listesini temizler, vector erase ve managed string hazırlığını yapar.
Bu prefix statik kaynakta izlendi; yeni API bu UI etkilerini çalıştırmaz. Setter'ın
native OnChange davranışı ayrıca kanıtlanmadan nested callback uydurulmaz.

Region mapping ham zone DWORD karşılaştırması değildir. Kaynak0046209c sonucu
004620bc ile ada çevrilir; refresh Moradon/Luferson/EMC/Karus Eslant/Human Eslant
eşitlik sonuçlarından21/1/2/11/12 üretir. İlk true eşitlikte durur; tümü false ise
0 ve tarama öncesi cleanup yolu vardır. Yeni resolver equality sonuçlarını açık
girdi alır; eksik sonuç false sayılmaz. Native ANSI/RTL karşılaştırma ve zone
adı yardımcılarının yürütüldüğü iddia edilmez.

Kaynak aday aralığı0..30000 dahildir. Pointer0 adayı atlar. Pointer+1b mapped
zone ile eşleşmelidir. +1a iki ayrı fresh okumada önce3, sonra4 dışında olmalıdır.
+19 ilk okuma3 ise nation wildcard'dır; aksi halde ikinci byte ile00462690'ın
tam EAX DWORD'u karşılaştırılır. +18 ilk okuma5 ise class wildcard'dır; aksi
halde ikinci byte004d4f60'ın yalnız AL'iyle karşılaştırılır. Class helper'ın
bilinmeyen dönüşüne varsayılan enum0 verilmez; AL sonucu açık gözlemdir.

+24 byte4 olmalı, +30 byte pozitif olmalıdır. +05 üç ayrı fresh okumada sırasıyla
0 olmama,100 olmama ve minimum-level değerini sağlar.00462670 EAX'iyle son
karşılaştırma signed32'dir. Sonra+20 DWORD'u004d5244'e verilir; dönüş AL2 ise
aday atlanır. Böylece aynı adresteki okumaları tek snapshot'a indirgeyen farklı
bir davranış eklenmez. Byte wildcard dışındaki yardımcılar eksikse ret sonucu
uydurulmaz. Tüm read/call kayıtları yerel plan ve captured değerlerdir; gerçek
adrese bellek erişimi yapılmaz.

Frame yalnız ulaşılan normal receipt/değerleri saklar. İlk okuma tamamlanıp
ikinci okumada boşluk varsa ilk değer korunur, ikinci değer yeni gözlemden gelir.
Normal dönüş biliniyor ama EAX/AL bilinmiyorsa bu da ayrı boşluktur; helper request
tekrar listelenmez. İsim aşamasına ulaşmadan tamamlanan ret yolları sonraki alanı
tüketmez. Bu kaynak gözlem sırasını modelleyen bir API'dir; normal receipt'lerin
kendisi gerçek helper çalıştırması veya native SEH/concurrency eşliği değildir.

14 yeni test: beş bölge/ilk eşleşme/unsupported, erken null ve ret yolları,
wildcard lazy tüketim, nation fullDWORD/class-status lowAL ayrımı, üç farklı
minimum byte, signed level sınırı, pending normal/EAX ve fresh ikinci okuma,
slot0/30000 sınırı, tamamlanmış frame idempotence. 2676 retained instruction
kaydı iki Richard refresh gövdesi ve ilgili helper'lardan yeniden doğrulandı.
Bu sayı bitmiş fonksiyon veya proje tamamlanma yüzdesi değildir.

Sıradaki aşama isim/NPC verisi ve source28byte record/vector üretimini elemekten
geçen bu zincire bağlamak; ardından gerçek yenileme/list/NPC kontrolleri. Quest
details/compare/selected Take/Give, diğer özellik açıkları, native/runtime/otomatik
veri edinimi ve canlı uyumluluk da sürer. Yeni REA decompile veya oyun bellek/
ağ/eylem IO yapılmadı; kaynak retained PE/Ghidra/DFM kanıtıdır.
