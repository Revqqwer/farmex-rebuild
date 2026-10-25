# Satış sırası ve liste eşleşmesi

18 Ekim 2026: `merchant_sell_selection.py`, `00420aac` (liste sırası) ve
`00420ca8` (çanta sırası) yardımcılarının seçim prefix'lerini modeller.
`work/audit_sell_selection.py`, iki sürümde bu gövdeler/caller/ayar bağına ait
762 talimat kaydını ve published kontrol kaydını disk baytlarından doğrular.
Rapor: `outputs/FarmexBot_satis_secim_kod_kaniti.json`. Ghidra/Delphi statik
kanıtıdır; REA Evidence, native yürütme veya oyun gözlemi değildir. Tam yardımcı
gövdelerinin bayt doğrulaması, tamamının uygulanmış olduğu anlamına gelmez.

Kaynak `chSellMBotInvSort` kontrolü formda `+e48` üzerinden okunup nesnenin
BYTE `+c8` alanına yazılır. Etiket “Itemleri Inventory Item Sırasına Göre Diz”dir.
`+c8` açıkken caller slot14..41 üzerinden `00420ca8` çağırır. Yardımcı hâlâ
hazırlanmış listedeki ID eşleşmesini arar. Bu seçenek çantadaki bütün eşyalara
satış izni değildir.

`MerchantSettings.sell_inventory_order` bu anlamdaki yeni açık ayardır.
Önceki `sell_all_inventory` alanı geriye uyum için sıra seçimi alias'ı olarak
korunur; gerçek sell-all izni anlamına gelmez. İki alan açıkça çelişirse reddedilir.
Legacy bağlı olmayan yol yalnız sınıflama/slot niyetleri üretir ve hâlâ tam
kaynak seçim veya gerçek satış sonucu değildir.

## Seçim sırası

Çanta sırası, caller'ın verdiği tek slotu işler: taze item EAX0 ise used-byte
ve vektör okunmaz; used-byte sıfır değilse vektör aranmaz. Aksi halde normal,
sabit prepared-vector gözlemindeki ilk ID eşleşmesi seçilir. Aynı ID'li sonraki
liste satırı öncelik almaz. ID listede yoksa `unmatched` olur.

Liste sırası, caller'ın verdiği prepared-row'u alıp slot14..41'i sırayla arar.
Used-byte yalnız item ID eşleşince okunur. Kullanılmış eşleşen slot atlanır.
İlk kullanılmamış eşleşme seçilir. Bu yardımcıda ayrı ID0 kontrolü yoktur;
ham prepared row0 ve item EAX0 eşleşmesi modelden keyfi olarak silinmez.
Bu, native hazırlayıcının böyle bir satır üretmesini kanıtlamaz.

Eşleşince ilk taze `00463538(slot)` EAX sonucu, istenen adetle signed32
karşılaştırılır. Daha küçükse helper ikinci kez çağrılır ve ikinci taze EAX
doğrudan kullanılır. İkinci değere yeniden clamp uygulanmaz; ilk sonuç eksik
ikincinin yerini tutmaz. Fiyat, gözlenen prepared QWORD'un düşük DWORD'udur.

Vektör boyutu/heap davranışını emüle etmek yerine açık `stable_rows=True`
gözlem sözleşmesi gerekir. Item sonuçları ve used byte dizilerinin0indeksi
mutlak slot14'tür. Eksik ulaşılan değerler gözlem açığıdır. API kendi belleğini,
listeyi veya verilen tuple'ları değiştirmez; helper'in ham dönüş EAX'ını
uydurmaz. `unmatched` başarı veya sunucu reddi değildir.

## Runner bağı ve sınırlar

`MerchantSnapshot.sell_selection_inputs` ile SELL phase3'te bu seçim modeli
kullanılır. Caller slot/index eşleşmesi denetlenir. Eşleşmeyen tamamlanmış
seçim yalnız traversal sayacını ilerletir, satış niyeti üretmez. Bilinmeyen
vektör boyutu boş liste sayılmaz. Eşleşmiş seçim, helper'in kalan
pending/yazma/clock/accumulator/FPU/tampon/kuyruk kısmının normal dönüşüne ait
ayrı `sell_slot_helper_returned=True` gözlemi olmadan caller sayacını ilerletmez.
Bu alan oyuna işlem uygulamaz veya ACK kanıtlamaz.

Kalan normal tail'in own state/buffer/queue planı sonradan eklendi;
[SELL_SLOT_TAIL.md](SELL_SLOT_TAIL.md). Native tail çalıştırılmadı. Planlanan prefix native üzerinde çalıştırılmış
veya dondurulmuş değildir; tekrar çağrı yeni gözlem örneğidir. Native callback
eşzamanlılığı, istisna, vektör değişimi ve tekrar giriş davranışı doğrulanmadı.
SELL scalar panel bağlantısı eklendi; [SELL_MERCHANT_CONFIGURATION.md](SELL_MERCHANT_CONFIGURATION.md).
Satış ListView üreticisi ve typed kayıtların UI aktarımı eklendi;
[SELL_MERCHANT_PREPARATION.md](SELL_MERCHANT_PREPARATION.md). Yeni mod eksik
taze envanter gözleminde bekler; tail UI gözlemleri, native yürütme ve canlı veri hâlâ açık kalır.

16 yeni test; listede olmayan eşya, sıfır ID kısa devresi, used-byte sırası,
ilk duplicate,28slot araması, signed adet ve iki taze adet, bilinmeyen vector,
ayrı tail normal dönüşü, caller sayacı ve eski/yeni sıra alanı çakışmasını sınar.
Tam birim çalıştırmasında1784test geçti (7.530s). Bu değişiklikte UI değiştirilmedi;
genel smoke son panel bağlantısı aşamasında geçmişti. Canlı uyumluluk açık.
