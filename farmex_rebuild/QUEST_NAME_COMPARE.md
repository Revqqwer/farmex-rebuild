# Görev adı: ANSI karşılaştırma devam API'si

Görev aramasının çağırdığı eşitlik wrapper'ı current00505134 / canonical00505118
üzerindedir. İç compare wrapper'ı current00505174 / canonical00505158, önce
00402e18 SETA yolunu, gerekirse00402e30 SETC yolunu çağırır. İki yol da aynı
`rtl260.bpl!@System@@LStrCmp$qqrv` importunu kullanır: bu ANSI string yoludur.
Başka yerlerdeki Unicode SETZ modelleri bu wrapper'a doğrudan uygulanmaz.

`QuestNameCompareFrame` bu sırayı explicit normal dönüşlerle izler. İlk
LStrCmp'nin CF/ZF bilgisi SETA sonucunu belirler. CF1, ZF bilinmese de SETA0'ı
kanıtlar; CF0 ise ZF gerekir. SETA1 olduğunda ikinci karşılaştırma yapılmaz.
Diğer yolda ikinci/fresh LStrCmp yalnız SETC için CF ister. İkinci çağrı ilk
çağrının sonucunu veya operand snapshot'ını kullanmaz. Compare wrapper1,
FFFFFFFF veya0; dış wrapper SETZ ve AND EAX,1 ile temiz0/1 üretir.

Bir helper'ın tüketilmiş flag/operand öneki ve seçilen politika retry'da
korunur. İlk CF gelmişken ZF eksikse CF yeniden örneklenmez. Kısmi owned-byte
girdilerinde tüketilen taraf korunur. Wrapper normal dönüşleri tamamlanmadan
nihai EAX verilmez; çağrı token'ları yeniden üretilmez.

Varsayılan API yakalanmış bayrakları ister. Açık `use_owned_bytes` politikası,
iki ayrı çağrı için immutable post-load ANSI byte dizilerini unsigned byte
sırasıyla karşılaştırabilir. Bu politika Unicode decode, case-fold veya NUL
sonlandırma yapmaz; embedded NUL karşılaştırmaya dahildir. Kod sayfası veya
native RTL/alias/heap/refcount eşliği kanıtı değildir. Owned girdiler ile
yakalanmış CF/ZF aynı çağrıda karıştırılamaz.

17 yeni test ve toplam4950 test geçti. Yeni GUI yok: önceki4933 tam GUI'nin
912 kod kaynağı ve383 import modülü değişmedi; iki yeni dosya bu kapanımın
dışındadır. Önceki yayımlanmış JSON dosyaları da byte eşitliğiyle kontrol edildi.
Kaynak bağı iki PE'deki668 komut, LStrCmp/IsBadReadPtr/memcpy import kimlikleri,
512 byte sıfır template ve bad-read boş literal kontrolünü içerir.

Bu API henüz lookup name_compare üreticisine bağlanmadı. Ad okuma yardımcısının
IsBadReadPtr kontrolü, memcpy/constructor/assignment/cleanup alt üreticileri,
native RTL/SEH ve gerçek oyun gözlemleri açık. Güncel kayıt
`QUEST_NAME_COMPARE_VALIDATION.json`; önceki Al/Ver birleşimi korunur.
