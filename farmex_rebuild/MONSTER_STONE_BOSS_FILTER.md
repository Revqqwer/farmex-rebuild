# Monster Stone boss adı filtresi

`monster_stone_boss_filter.py`, `004c4f64` yordamının koşullu gözlem modelidir. Aday Unicode adını başlangıçta kopyalayan span, boş metin karşılaştırması ve temizliği ayrı normal dönüşler ister. Boş karşılaştırmasının düşük baytı sıfır değilse full EAX0 döner. Python metin eşitliğinden kaynak sonucu üretilmez.

Vektör, MS context+8 adresindeki nesnenin +10/+14 alanlarıdır; varsayılan context56216c için begin562184/end562188 olur. Her döngüde begin null kontrolü tazedir. Null değilse end ve çıkarma için begin ayrıca okunur. DWORD fark işaretli yorumlanır; negatifse3 eklenip SAR2 uygulanır. Sonuç unsigned olarak indeksle karşılaştırılır. Negatif fark otomatik boş liste kabul edilmez. Öğe karşılaştırması için begin dördüncü bir adımda yeniden okunur; önceki pointer dondurulmaz.

Her öğede aday yeniden004073a0 dönüşümüne girer;00505134 karşılaştırması ve004040f8 geçici temizliği ayrı span'lardır. Bunların codec/locale/eşitlik algoritmaları burada uygulanmaz. İlk düşük baytı sıfır olmayan sonuçta AL1 döner. Başarı yolu yalnız AL'yi yazdığı için model full EAX1 garantisi vermez. Başarısız yol full EAX0'dır. Yerel döngü bütçesi kaynak sonlanması değildir; bütçe bittiğinde sonuç açık eksikle kalır.

Başlangıçta0049f061,562174 nesnesini00476078 ile kurar. Nesne +10/+14/+18 alanlarını sıfırlar. Ardından13 literal string nesnesi004a1de0 ile aynı nesneye sırayla eklenir. Tüketicinin context+18 alanı bu nesnenin+10 alanıdır. Diskten doğrulanan başlangıç adları:

- Upertaurs
- Countral
- Indy Archer
- Obelisk
- Dragonia
- Rampage Orc
- Kekurisharesause
- Laonbelisk
- Revenge Knight
- Black Guard
- Alphabet
- Goddess Ymir
- Dungeon Keeper

`STARTUP_BOSS_NAMES` bu literal baytları taşır; çalışan oturumda listeyi sabitlemez veya native string karşılaştırması yerine geçmez. Başlangıç nesnelerinin kurulması/eklenmesindeki tüm exception ve allocation davranışı uygulanmış değildir. Sonraki değişiklikler dışlanmadığından canlı liste doğrulanmış sayılmaz.

`MSSelectorObservation.boss_filters` aday sırasına bağlı typed girdiler kabul eder. Seçici eriştiği adla aynı context üzerinde generated child oluşturur. Eksik child dış normal/EAX gözlemiyle atlanamaz; child tamamlandıktan sonra dış normal dönüş ve aynı düşük bayt gerekir. Devam çerçeveleri tüketilen pointer/karşılaştırmaları korur; henüz okunmayan liste alanları taze gelebilir.

10 yeni test; boş/null yollar, ayrı begin okumaları, negatif ve sarmalı fark, dinamik liste boyutu, yeniden dönüşüm, yalnız AL başarısı, cleanup boşluğu, tüketilmiş sonuçların korunması, bütçe ve child/parent ayrımını kapsar. Eski/güncel dosyalarda2798 kayıt doğrulandı:252 filtre gövdesi kaydı ve2546 başlangıç/container kaynak kaydı. Dört REA raporu disk assembly'siyle eşleşti. Bu kayıtlar yeni ikili keşif kapsamı veya tam fonksiyon/canlı sertifikası değildir.
