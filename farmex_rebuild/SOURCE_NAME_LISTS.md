# Beyaz/kara liste üreticisi ve sorgu bağı

18 Ekim 2026. `source_name_lists.py`, 0046c3b8 normal caller akışını modeller.
İki sürümde 1444 talimat kaydı ile dört published field ve dört published
method kaydı doğrulandı. Kanıt `outputs/FarmexBot_isim_liste_uretici_kod_kaniti.json`,
üretici `work/audit_source_name_lists.py`. Bu disk/Ghidra kanıtıdır; REA
Evidence veya canlı event dispatch kanıtı değildir.

Statik zincir artık liste rollerini ayırır:

| Kontrol | Form alanı | Vector | Süzgeç |
|---|---|---|---|
| AntiCRWhiteList | 3D4 | context+E0, begin F0/end F4 | primary 0046c1a0 |
| AntiCRBlackList | 3F0 | context+100, begin110/end114 | secondary 0046c2ac |

Text girişleri sırasıyla3D8/3E4'tür. Published method kayıtları text ekleme
ve double-click handler'larını source adaylarına bağlar; bu handler'ların
0046c3b8 çağrıları da disk baytlarıyla eşleşir. Handler iç yardımcılarının
tüm anlamı veya gerçek UI dispatcher çalışması bundan çıkarılmaz.

Üretici önce ANSI scratch başlatır, ardından **kara vector**, sonra **beyaz
vector** için end/begin/erase helper span'larını çağırır. Model, bu helper'ın
normal dönüşünden boş içerik çıkarmaz: `black_after_reset` ve
`white_after_reset` ayrı exact ANSI tuple gözlemleridir. Bunlar boş değilse
boş varsayılmaz. Eksik receipt veya içerik own denemeyi durdurur.

İki reset'ten sonra UI listeleri kara, ardından beyaz sırasıyla taranır.
Her turda count virtual çağrısı tazedir ve **signed count>index** kullanır;
negatif count gövdeye girmez. Item getter, Unicode→ANSI conversion ve ANSI
scratch assignment/temporary cleanup normal dönüşleri ayrıdır. Kesin
ANSI bayt çıktısı ayrıca gerekir; codec tahmin edilmez. Kaynakta trim,
küçük harfe çevirme, sıralama veya tekrar silme çağrısı bu aktarımda yoktur.
Own projeksiyon sıralı, yinelenen ve gömülü NUL içeren byte string'leri korur.

00409f6c size ve00409f94 capacity ayrı taze DWORD sonuçlarıdır. Unsigned
size<capacity ise00409fbc yolu kullanılır, normal dönüş EAX'ı vector+14'e
yazılır; bu EAX ayrı gözlemdir. Aksi halde0040a01c yolunda çağıranın böyle
doğrudan store'u yoktur. Insert helper/allocator/refcount etkileri tam
çözülmüş değildir: planın içerikleri own byte-list projeksiyonudur.
Tamamlanmayan plan `.state` olarak giriş state'ini tutar, bilinen kısmi
listeyi `prospective_*` alanlarında gösterir. Bu native rollback iddiası
değildir. Son ANSI scratch cleanup normal dönüşü de gereklidir.

`filter_refreshed_names` explicit `stable_same_invocation=True` ve codec
ile tamamlanmış own listeyi isim süzgecine bağlar. Primary beyaz, secondary
kara listeyi alır. Kaynak count/base gözlemleri ayrıca gerekir; sentetik
pointer veya native codepage üretilmez. Stable count uyuşmazlığı reddedilir.
Ancak ulaşılan satırlar dönüştürülür: ilk eşleşmeden sonraki çelişkili veya
dönüştürülemeyen kayıt incelenmiş sayılmaz. Kaynak conversion/equality/
cleanup receipt'leri doldurulmaz. İsteğe bağlı own UTF16 eşitlik politikası
ayrı kalır; gerçek RTL semantics sertifikası değildir.

16 yeni test dahil **2292 test geçti (7.648 saniye)**; producer/filter/query
odaklı57 test geçti. Signed count, fresh shrink, unsigned size/capacity,
temizlik gözlemi, her helper boşluğu, kısmi state, aynı isim tekrarları,
gömülü NUL ve stable-codec köprüsü sınandı. UI/native kod değişmedi; bu
aşamada UI/native smoke tekrarlanmadı. Sonraki panel güncellemesinde own
metin ekleme/temizleme/silme bağlandı: [NAME_LIST_CONTROLS.md](NAME_LIST_CONTROLS.md).
Raw üretici kendi UI'sının native yürütmesi sayılmaz. Add/remove/persistence helper içleri,
gerçek heap/RTL ve canlı uyumluluk açık; oyun belleğine erişim yapılmadı.
