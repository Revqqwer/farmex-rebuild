# Aday isim süzgeçleri

18 Ekim 2026. `source_name_filter.py`, 0046c1a0 ve 0046c2ac normal çağrı
akışlarını modeller. Primary vector context+E0 (begin F0/end F4), secondary
vector context+100 (begin110/end114) kullanır. Sonraki üretici incelemesi
primary'nin beyaz, secondary'nin kara liste olduğunu bağladı; ayrıntı
[SOURCE_NAME_LISTS.md](SOURCE_NAME_LISTS.md). İki sürümde her iki 93
talimatlık gövde ve Unicode giriş constructor wrapper'ı doğrulandı: toplam
446 kayıt. Kanıt `outputs/FarmexBot_isim_suzgeci_kod_kaniti.json`, üretici
`work/audit_source_name_filter.py`. Bu disk/Ghidra kanıtıdır; REA Evidence
veya gerçek oyun yürütmesi değildir.

Girişte Unicode copy/refcount span normal dönüşü ayrı gözlemdir. Index0'dan
başlanır; her turda count için begin ve gerekirse end taze okunur. Begin0
ise end okunmaz ve count0'dır. Diğer durumda düşük32 SUB, signed negatifse
ADD3, SAR2 uygulanır. Döngü koşulu unsigned count>index'dir. Bozuk/negatif
pointer farkını güvenli sıfır saymak kaynak davranışını değiştirir; model
bu yüzden bu aritmetiği aynen tutar, eksik sonraki gözlemde durur.

Gövde count begin'i yeniden kullanmaz: slot base ayrı taze örnektir. Slot
adresi `(base + index*4) mod 2^32` olur. 00403d84 normal conversion dönüşü,
00505d3c karşılaştırması ve geçici Unicode cleanup dönüşü ayrı tutulur.
Karşılaştırma EAX'ı cleanup öncesi stack'e kaydedilir; sonra EDX'e alınarak
DL sınanır. Cleanup'ın dönüşü eşitlik sonucunun yerine kullanılamaz.
İlk eşleşmede AL1 ve input cleanup ile dönülür; sonraki count okunmaz.
Eşleşmede üst EAX bilinmediğinden tam EAX1 denmez. Liste bittiğinde saklanan
XOR EAX sonucu nedeniyle normal dönüş EAX0'dır. Her iki çıkışta input
cleanup normal dönüşü gerekir; eksik dönüş tamamlanmış sonuç sayılmaz.

Giriş constructor'ında küçük harfe çevirme kanıtı yoktur. Mevcut
`UnicodeEqualityObservation` açık ZF gözlemiyle veya açıkça seçilmiş kendi
UTF16 eşitlik politikasıyla kullanılabilir. İkinci yolda metinler gerçekten
input ve dönüştürülen slot metniyle eşleşmelidir. Case folding/normalization
yapılmaz. Bu yerel politika yüklü RTL'nin locale/refcount/exception
davranışını kanıtlamaz; source conversion/cleanup receipt'lerini doldurmaz.

Rota adayında `primary_name_execution` / `secondary_name_execution` optional
typed planları bağlar. Ulaşılan filtrede raw AL ile karıştırma, yanlış kind
ve query ismiyle uyuşmazlık reddedilir. Eksik plan bloklar. Tam plan için de
`primary_name_returned=True` / `secondary_name_returned=True` ayrıca gerekir.
Ulaşılmayan filtreye verilen veri çalıştırılmış sayılmaz. Query isim çıktısı
bilinmiyorsa bound isim eşleşmesi doğrulanmış kabul edilmez.

18 yeni test dahil **2276 test geçti (8.069 saniye)**; isim/query/entry/
callback odaklı 70 test geçti. Null/empty, değişen count/base, signed delta,
DWORD sarılması, ilk eşleşme, cleanup boşlukları, explicit UTF16 ve bound
query hataları sınandı. UI/native kod değişmedi; UI/native kontrolü bu
aşamada tekrarlanmadı. Canlı uyumluluk, liste helper etkileri, RTL/native
helper ve eşzamanlı bellek etkileri açık. Modeller oyun belleğine erişmez.
