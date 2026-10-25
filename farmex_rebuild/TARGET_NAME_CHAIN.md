# UI tekrar kontrolü ve hedef isim okuyucusu

18 Ekim2026. `source_ui_name_scan.py`,0046601c normal UI duplicate aramasını
modeller ve `source_name_add.py` içine optional typed bağ sunar.
`source_target_name.py`,00462630 target-ID ve00466144 name-by-index normal
helper akışlarını modeller. İki sürümde990 talimat kaydı doğrulandı:
101UI scan+11ID+179name helper ve iki102talimat target-add caller gövdesi.
Rapor `outputs/FarmexBot_hedef_isim_ve_UI_sorgu_kod_kaniti.json`, üretici
`work/audit_target_name_helpers.py`. Bu disk/Ghidra kanıtıdır; REA Evidence
veya native yürütme değildir. Caller byte kapsamı tam olsa da tüm
fonksiyon semantiği/exception/native etkileri tamamlanmış sayılmaz.

## UI duplicate araması

Input ANSI copy normal dönüşünden sonra index0başlar. Her turda UI count
virtual14 ayrı okunur ve **signed count>index** sınanır. Negatif/zero count
gövdeye girmez. ANSI needle her turda yeniden Unicode'a çevrilir; bir önceki
iteration dönüşümü otomatik kullanılmaz. UI item virtual0C ve equality
helper normal dönüşü, sonra iki geçici Unicode cleanup ayrı gözlemlerdir.
Kaynak EAX'ı cleanup öncesi saklar, EAX'a geri alıp AL'ı sınar. Bilinen
üst24bit bu helper'ın match dönüşünde korunur; vector filter0046c1a0'ın
cleanup sonrası bilinmeyen üst EAX davranışıyla karıştırılmaz.

İlk eşleşme AL1 ile döner; sonraki count okunmaz. Liste tükenince EAX0.
Her iki yolda ANSI input cleanup gerekir. Kısmi iteration dizisi end-of-list
kanıtı değildir. Own UTF16 equality seçilirse row'un fresh converted needle
ve fresh UI item metinleriyle eşleşmesi doğrulanır; RTL/locale/fallback
eşdeğerliği bundan çıkarılmaz.

`NameAddObservation.duplicate_execution` optional planı ikinci getter'ın
post-conversion ANSI girdisine bağlar. Reached raw AL ile karıştırma veya
input uyuşmazlığı reddedilir. Eksik bound plan durdurur. Tam plan da ayrı
`duplicate_span_returned=True` gereksinimini kaldırmaz. İlk nonempty guard
skip'inde verilmiş bound veri çalıştırılmış gösterilmez. Üçüncü append
getter'ı hâlâ bağımsızdır; ikinci getter'dan kopyalanmaz.

## Target-ID ve isim helper'ı

00462630 global553E7C'nin gösterdiği root'u guarded DWORD ile alır; taze
global554044offset'i ekleyip ikinci guarded DWORD'u döndürür. Toplama
düşük32bit sarılır. Null ilk helper argümanı API örneği tüketmez; ama root0
elde edilmesi sonraki nonzero offset adresindeki çağrıyı atlatmaz. Örnekler
ortak immutable `SourceCoinObservation` taşıyıcısını kullanır; coin adresleri
ve coin sonucu target'a kopyalanmaz.

00466144 önce local Unicode init normal dönüşünü ister. Signed index0..2999
lookup'a gider; negatif veya3000ve üstü empty ANSI literal523705fallback'ına
gider. Null lookup aynı fallback'tır, unknown pointer değildir. Her fallback
assignment/cleanup normal span'ı gerekir.

FEC isim uzunluğu **tam DWORD**'dur; signed DWORD değer16eşiğiyle karşılaştırılır. Signed
uzunluk16'dan küçükse inline FE8adresinden**255bayt** istenir. Uzunluk16ve
üstüyse FE8dolaylı pointer guarded okunur ve tam DWORD uzunluğu kullanılır.
Bu,0046cfcc query'sindeki WORD/tam kısa uzunluk kopyasıyla aynı değildir.
Mevcut `npc_text_request`/`replay_text_copy` alt modelleri kullanılır;
512bayt üstü native overflow yeniden üretilmez, unresolved tutulur.

Copy/Unicode assignment/cleanup span'ı, ardından ANSI output conversion/
assignment/final cleanup ayrıca gerekir. Çıktı ANSI baytları ayrı gözlemdir;
codec tahmin edilmez. Optional yakalanmış kopya raw Unicode override ile
karıştırılamaz ve dönüşüm codepage boşluğu hayali empty isim üretmez.

## Target-add caller sınırı

İki düğme00462630'u üç ayrı yerde çağırır: ilk değer nonzero olmalı,
ikinci unsigned değer**en çok3000**, üçüncü değer name helper parametresidir.
İkinci0ve üçüncü negatif/3000, bağımsız örnekler değişirse ayrı yollara
gidebilir. ID3000helper'da empty isim üretir; caller'da ekstra nonempty
guard görünmez. Bu üç okuma tek stable hedef olarak modellenmiş sayılmaz.

Sonraki aşamada normal parent state/duplicate/refresh birleştirmesi
[SOURCE_TARGET_ADD.md](SOURCE_TARGET_ADD.md) içinde eklendi. Gerçek
target-button adapter'ı henüz eklenmedi. Canlı düğmeler etkin
değildir. Modeller oyun belleği okumaz/yazmaz ve koruma API'sini çalıştırmaz.

29yeni test dahil **2368 test geçti (7.165 saniye)**; target/scan/add odaklı35
test geçti. Signed count/fresh conversion, EAX preservation, bound caller
gates, target address wrap/null/missing, index3000, tam DWORD length,
inline255, codec gap ve unsafe copy sınandı. UI/native kaynak değişmedi;
bu aşamada UI/native smoke tekrarlanmadı. Canlı uyumluluk açık.
