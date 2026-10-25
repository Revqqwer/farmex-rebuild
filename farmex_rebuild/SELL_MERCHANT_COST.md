# Satış maliyeti ve eşleşme sayısı

18 Ekim 2026: `merchant_sell_cost.py`, `004203e4` normal yolunu hazırlanmış,
sabit bir vektör ve açık taze helper sonuçları üzerinde modeller.
`work/audit_sell_cost.py`, iki ikilide334talimat kaydının baytlarını ve kritik
branch/okuma/çarpım/toplam/sayaç talimatlarını doğrular. Rapor
`outputs/FarmexBot_satis_maliyet_kod_kaniti.json`. Bu334kayıt önceki1162lik
hazırlık audit'inin alt kümesidir; sayılar benzersiz toplam olarak eklenmez.
Ghidra statik kanıtıdır; REA Evidence veya native CPU yürütme sonucu değildir.

Helper önce slot14..41için `object+59+slot` used byte'larını0yapar. Yerel
QWORD toplam0başlar; dışarıdan verilen DWORD byref sayacı helper içinde
başlatılmaz. Bound42060ccaller başlangıcı0zorunludur. Tüm bellek yazımları
yalnız yerel `writes`/prospective mask planıdır; gerçek bellek değiştirilmez.

## İki sıra

Liste sırasında her prepared row için slot14..41yeniden taranır. Item helper
her uğranan slotta taze çağrılır. Item eşleşirse used byte kontrol edilir;
aynı slot başka satırda ikinci kez kullanılmaz. Yinelenen liste ID'leri ayrı
uygun slotları tüketebilir. Ham listedeki ID0için ayrı erken çıkış yoktur.

Çanta sırasında her slot bir kez okunur. Item0ise liste okunmadan atlanır.
Diğer ID'lerde ilk eşleşen prepared row kullanılır. Aynı ID'li sonraki satır
o slot için seçilmez. Her slot yalnız bir kez gezildiği için bu dal eski used
byte'ını test etmez; yine eşleşen slotun byte'ını1olarak planlar.

Prepared kayıtlar immutable tuple'dır. Ulaşılan vector-count noktalarında
`stable_rows=True` gerekir; bu, yerel örneğin sabitlik sözleşmesidir. Native
heap/pointer aritmetiği veya callback sırasında değişen vektör modeli değildir.
Çanta sırasındaki28item sonucu0ise vektöre hiç ulaşılmaz; o durumda sabitlik
gözlemi gerekmeyebilir. Boş liste sırası ise item helper'ı çağırmaz.

## Adet ve maliyet

İlk taze adet EAX sonucu istenen adetle signed32 karşılaştırılır. Küçükse
ikinci taze adet EAX doğrudan alınır; tekrar clamp yapılmaz. Her eşleşmede:

```text
term = lowDWORD(chosen_quantity_DWORD * price_QWORD.lowDWORD)
sum = lowQWORD(sum + zero_extend(term))
count = lowDWORD(count + 1)
```

Kaynak IMUL sonrasında EDX'i sıfırlar. Bu yüzden signed negatif bir çarpımın
yüksek kısmı toplamda korunmaz. Örneğin0xffffffff*2terimi4294967294olarak
eklenir. İki ayrı0xffffffffterimi ise8589934590toplamı verir. Fiyatın yüksek
DWORD'u bu yardımcıda çarpıma girmez. Eşleşme sayısı adet pozitifliği veya
satış başarısı sayısı değildir.

`item_results` ve `quantity_results` mutlak slot dizileri değil, **çağrı
sırasındaki** taze EAX sonuçlarıdır. Liste sırasında aynı slot farklı helper
çağrılarında farklı sonuç verebilir. Eksik sonuç0sayılmaz. Eksik planda sonuç
cost/count alanları bilinmeyendir; prefix toplam/sayaç/used-mask ayrı
prospective alanlarda gösterilir. Yeniden planlama native içinde dondurma/devam
etme değildir; yeni bir gözlem örneğidir.

## Setup ve workbench

`SellSetupObservation.cost_inputs` bu modeli bağlar. Hazırlık da bound ise
kayıtlar onun tamamlanan state'inden gelir; opaque hazırlık yolunda ayrı
`cost_rows` gerekir. Aynı anda ham cost/count verilemez. Cost tamamlanmadan
coin helper'ına geçilmez. Tamamlanınca normal42060csigned toplam/limit kapısı
kullanılır; native bildirim ve gerçek oyun sonucu üretilmez.

SELL workbench'inde, hazırlık modu içinde ayrıca varsayılan kapalı “Envanter
örneklerinden maliyet hesapla” seçeneği vardır. JSON alanları yukarıdaki taze
çağrı sırasına göre kendi örnekleridir. Ham maliyet/eşleşme alanları bu modda
okunmaz. Item/quantity/coin alanları yalnız ulaşılan kapıda işlenir; boş stable
vektörün ulaşmadığı bozuk JSON erken hata vermez. Seçim yeni denemede alınır.

Setup bütçe hesabındaki gözlemler phase3satış seçiminde tekrar güncel veri
sayılmaz. Typed seçici yeni item/used/adet gözlemleri ister; legacy sentetik
yola otomatik geçiş yoktur. Çalışan oyuna erişilmez, envanter okunmaz, paket
gönderilmez. Oyun adaptörü ve native tail hâlâ açık kalır.

15yeni test; sıralama farkı, duplicate/used slot, taze çağrı dizisi, iki adet
okuması, signed32 ve düşük çarpım/QWORD carry, fiyat yüksek DWORD'u, prefix
gap, sayaç sarılması ve setup bağını kapsar. Tam çalıştırmada1826test geçti
(8.704s). `work/verify_sell_cost_ui.py`6maliyet/1eşleşme türetme, ham alanları
yoksayma, lazy kapılar, boş liste ve phase3'te yeni veri gereğini doğrular.
Önceki ham maliyetli hazırlık UI testi ve genel gizli smoke1037kontrol/11form/
18sekme ile geçti. Native CPU/heap/gerçek helper ve canlı oyun uyumluluğu
bu kontrollerle kanıtlanmadı.
