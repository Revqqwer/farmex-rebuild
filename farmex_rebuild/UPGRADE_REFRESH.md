# Upgrade Listeyi Yenile akışı

4658 Python testi ve yeni tam yerel GUI1037 kontrol/11 form/18 sekme geçti.
UPGRADE_REFRESH_VALIDATION.json kapsamı kaydeder. Diğer Upgrade işlemleri
ve canlı item işlemleri tamamlanmış sayılmaz.

Actual btnUpgradeRefresh, shared Upgrade provider/timer/FIFO üzerinden
UpgradeRefreshObservation kabul eder. Provider yokken own adapter disabled
kalır;561f55 raw gate bilinmeden veya0 iken liste silinmez. Gate nonzero ise
Clear hemen olur; initial string/guarded root gözlemi eksikse eski liste geri
konmaz. Root0 tek başına envanter yok sayılmaz: offset + ikinci guarded read
gerekir. Inventory0 sonrasında bile final cleanup normal dönüşü beklenir.

14..41 slotlarının her birinde ayrı global5540ac offset gözlemi kullanılır.
Record0 diğer alanları tüketmez. Nonzero record+60/+64 pointer'ları ve
base/variant DWORD değerleri bağımsız guarded örnek ve normal dönüş ister.
Item ID unsigned base+variant%1000 lowDWORD'dur. İç ad üreticisi sağlanan
lookup/metadata pointer'larıyla item_name planına bağlanır. Yalnız ulaşılan
name değerleri cache'lenir; yetersiz capture byte aralığı tamamlanabilir.
Unsafe source overflow/unterminated yolları başarı sayılmaz.

Adın ANSI->Unicode dönüşümü aynı00403d84 child'ıyla açık null/header/effective
codepage ve ayrı normal receipt'lerden oluşur. Assignment, Unicode cleanup,
ANSI cleanup tamamlandıktan sonra metadata DWORD'u yeniden/fresh okunur;
grade unsigned%10 olur. Daha sonra ayrı metadata+44 BYTE5 filtresi uygulanır.
İlk variant/category değeri bu sonraki okumaların yerine kullanılamaz.
Dolayısıyla filtre dışı item bile daha erken ad üretiminde bekleyebilir.

Add sonrası caption slot-14 olarak yazılır; concat eksikse bu önek kalır.
Subitem name + ' (+' + grade + ')' biçimindedir. Satır cleanup ve son dış
cleanup receipt'leri başarıdan önce gerekir. Tüketilen okumalar/normal True
ve hazır adlar poll ile tekrar tüketilmez; henüz ulaşılmamış slotlar fresh
kalır. Guard request adresleri plan verisidir; süreç belleğine erişilmez.

Gerçek GUI senaryosu gate0/unknown, Clear prefix, null inventory/final cleanup,
28-slot tarama,0/27 caption, CP1254 içinde strict decoder'ın reddettiği81,
fresh grade, ad-before-filter, concat beklemesi/gizli form, silinen row token,
select-all handoff, reentrant FIFO ve profil iptalini doğrular. Yeni row'lar
kendi frontend politikamızla unchecked başlar. Own128-faz/100ms continuation,
FIFO ve token lifetime native hook/VCL/SEH/concurrency eşliği değildir.

İki pinli binary3136 instruction kaydı event/name/string/guard yardımcıları
için byte düzeyinde doğrulandı. Unicode copy/append/assignment importları
ve unsigned name storage karşılaştırması kontrol edildi. Önceki264 sonlu
standart RTL Unicode referansı korunur; canlı bot runtime codepage'i olarak
kabul edilmez. İç helper etkileri ve toplu cleanup span'leri açık normal
gözlemlerdir; native çağrılar çalıştırılmaz. Yeni REA decompile çağrısı yoktur.

Açık işler: otomatik gate/inventory/name/CP/normal edinimi; native bütün
helper/SEH/lifetime ve runtime eşliği; Upgrade start/stop/Armor ve gerçek
parameter callback bağları; diğer özellikler ve güncel oyun uçtan uca testleri.
Oyun bellek/ağ/eylem IO0.
