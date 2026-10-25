# Satış hazırlığına geçiş süresi

18 Ekim 2026: `merchant_sell_setup_delay.py`, aşama 2'deki ana saat kapısını ve
hazırlık yardımcısından önceki iki arayüz span'ını verilen gözlemler üzerinde
planlar. `MerchantSnapshot.sell_setup_delay_inputs` ile runner'a bağlanır.
Bu alanlar için workbench kontrolleri henüz eklenmedi; API kapsamıdır.

Kaynak sıra: extra wait DWORD +d0 → DWORD +61 → GetTickCount → sıfır
genişletilmiş tick eksi tam QWORD başlangıç damgası +8 → DWORD çarpım 1000
→ CDQ ile signed32 sonucunu signed64 genişletme → signed64 karşılaştırma.
ADD ve IMUL taşmaları korunur. Python'un sınırsız tamsayılarıyla doğrudan
`(extra+61)*1000` karşılaştırması bu ham alanın bütün değerlerinde eşdeğer değildir.

Elapsed >= interval ise önce `0042117e..004211c1`, ardından
`004211c4..0042121a` normal dönüşleri gerekir. İkisi tamamlanmadan `0042060c`
hazırlık yardımcısı erişilmiş sayılmaz. Yardımcının gerçek çalışması ve sonucu
bundan ayrı `SellSetupObservation` bağıyla modellenir; bu kapı tek başına
hazırlık başarısı, oturum kurulması veya oyun sonucu değildir.

Süre dolmamışsa `004217d7..00421924` countdown/string/UI span'ı için ayrı normal
dönüş gerekir. Bu span içinde ikinci bir GetTickCount ve geniş aritmetik helper
çağrısı vardır. Model bu ikinci tick'i ilk örnekle doldurmaz, gösterilecek saniyeyi
hesaplamaz ve helper etkilerini emüle etmez; bütün span opaque dönüş gözlemidir.
Planın `remaining_ms` alanı ana kapıdan hesaplanan kendi tanı bilgisidir, kaynakta
gösterilmiş veya sonradan gözlenmiş UI metni değildir.

Ham başlangıç damgası dışarıdan verilen source alanıdır. Legacy `started_ms` veya
`setup_started_ms` ile otomatik eşlenmez. Bound mod bu gözlemden hesaplar; kendi
monotonic saatinin ilerlemesi eksik source tick veya UI dönüşünü tamamlamaz.
Normal merchant yanıt dalındaki eşleşen kapatma yanıtı +8 üreticisi olarak
statik kodda belirlenmiştir; aşağıdaki bağ bu scoped üreticiyi kullanır. Başka
üreticiler, ilk başlangıç ve gerçek callback'e tutarlılık bütünüyle kanıtlanmadı.
Her çağrı kendi gözlem planıdır;
native callback durdurulmaz veya devam ettirilmez. Bound giriş yokken eski
deneme politikası ayrı kullanılmaya devam eder.

`work/audit_sell_setup_delay.py`, iki sabit hash'li dosyadan **346 talimat
kaydının** baytlarını doğrular. ADD/IMUL/CDQ, tam QWORD çıkarma, signed yüksek
ve unsigned eşit-yüksek düşük karşılaştırma, hazırlık callsite'ı ve iki ayrı
GetTickCount import kimliği ayrıca kontrol edilir. Adresi değişen opaque
wrapper çağrıları rol etiketiyle normalize edilir; bu helper gövdelerinin veya
iç etkilerinin eşdeğerliğini kanıtlamaz. Rapor:
`outputs/FarmexBot_satis_hazirlik_suresi_kod_kaniti.json`.
Ghidra statik kanıtıdır; REA Evidence veya native yürütme değildir. Örtüşen
talimat kayıtları benzersiz toplam kapsam sayılmaz.

9 yeni test; eksik ana tick/damga, 90999/91000 sınırı, iki ayrı ready dönüşü,
ADD/IMUL taşması, negatif signed64 elapsed, üst DWORD ve runner'ın erken setup
çağırmaması davranışlarını sınar. **1931 yerel test geçti** (6.853 saniye).
Birleşik senaryo ilk UI dönüşünde setup'a erişemediğini, ikinci dönüşle ilerlediğini
ve sonraki callback'lerde yeni tick örneği kullandığını doğrular. Bunlar kendi
test girdileridir; gerçek oyun verisi veya VCL yürütmesi değildir. UI bu aşamada
değişmedi; yeni UI smoke çalıştırılmadı. Native etkiler ve canlı uyumluluk açık.

## Kapatma yanıtından başlangıç damgası

`sell_setup_delay_from_reply`, verilen `MerchantReplyState.setup_stamp_qword`
alanını hazırlık gözlemine taşır. Yeni tick veya UI dönüşü uydurmaz. Daha önce
çözülmüş `004d8f4e..004d8faf` normal merchant dalında subtype 27/02, byte 2'deki
actor DWORD'u `00462650` sonucuyla eşleşirse GetTickCount sıfır genişletilerek
global 5697e0 tabanının +8/+c alanlarına yazılır; close pending +18 sonra temizlenir.
Aktif tarayıcının önce tükettiği dal bu merchant yazısını yapmaz. Bu producer,
önceki `FarmexBot_pazar_yanit_kod_kaniti.json` içindeki 472 talimatlık kapsamda
yeniden doğrulandı; bu sayıya yeni ve benzersiz kapsam eklenmiş gibi bakılmaz.

`merchant_snapshot_from_reply`, bound SELL hazırlık gözlemi verildiğinde bilinen
ham başlangıç damgasının reply state ile eşleşmesini ister. Bu modda damga legacy
`setup_started_ms` içine konmaz; onun epoch/future guard'ıyla karıştırılmaz.
Eksik raw damga eksik kalır. Legacy timestamp override ve çelişen ham damga
reddedilir. Bound gözlem verilmezse önceki normal-clock adapter davranışı sürer.
Established damgası ve diğer aşamaların saat projeksiyonları bu değişiklikle
genel olarak çözülmüş sayılmaz.

8 yeni test ile **1939 test geçti** (6.761 saniye). Birleşik model artık açık-pazar
fixture'ından close intent'e, ayrı verilen eşleşen kapatma yanıtına ve oradan
ham başlangıç damgalı hazırlık kapısına ilerler. Close pending'in intent sonrası
kurulması ayrı own fixture'dır; native kapatma caller'ı çalıştırılmış değildir.
Yanıt örneği canlı yakalama veya sunucu ACK'sı olarak etiketlenmez. İlk başlangıç
damgası ve tam yeniden açma döngüsünün native uyumluluğu açık kalır.
