# Satış listesi hazırlığı ve setup kapısı

18 Ekim 2026: `merchant_sell_preparation.py`, kaynak `0041da48` normal yolunu
mevcut ortak liste algoritmasıyla uygular. İki sürümde168'er talimatlı SELL/BUY
gövdeleri; yalnız exception metadata adresi, prepared-vector tabanı (`+a8/+f0`),
ListView alanı (`+c4c/+cd4`) ve gövde içi adresler normalize edilince eşleşir.
Kaynak BUY wrapper'ının davranışı korunur; ayrı SELL state'i `SellPreparedRow`
kayıtları üretir. `SellPreparationRow/Observation` ortak gözlem sözleşmesinin
alias'larıdır; native nesneler değildir.

`work/audit_sell_preparation.py`, iki ikilide bu gövdeler ve setup/cost caller
bağlamından toplam1162talimat kaydını ve SELL published ListView kaydını disk
baytlarından doğrular. Rapor `outputs/FarmexBot_satis_hazirlik_kod_kaniti.json`.
Statik Ghidra/Delphi kanıtıdır; REA Evidence veya native yürütme sonucu değildir.
Bu kayıtlar önceki auditlerle örtüşür; benzersiz talimat toplamına eklenmez.

## Liste üreticisi

Önce normal clear/erase dönüşü, sonra her döngüde taze signed GetCount gerekir.
Her ulaşılan satırda caption→item, subitem1→adet, subitem2→fiyat sırası izlenir.
Checked alanı bu kaynakta okunmaz. Sayısal görünümlü `Item` adı olan subitem0
ID veya miktar yerine kullanılmaz. Item/adet düşük DWORD, fiyat tam QWORD'dur.
Aradaki string/ANSI cleanup ve append normal dönüş kapıları korunur.

Fiyatın Unicode→ANSI sonucu açık byte gözlemidir; workbench yalnız ASCII
metin alt kümesinden kendi örneğini oluşturur. Native parser/codec/heap
eşdeğerliği doğrulanmadı. Eksik append veya sonraki count gözleminde tamamlanan
yerel prefix `prospective_state` içinde gösterilir; kabul edilen giriş state'i
değiştirilmez. Hazırlanan kayıtlar typed SELL seçicisine yeniden metin çevirmeden
verilebilir. Bu aktarım satışın gerçekleştiği anlamına gelmez.

## 0042060c çağıranı

`merchant_sell_setup.py` şu sırayı modeller:

1. `0041da48` bound hazırlık planı veya ayrı açık normal dönüş gözlemi.
2. Yerel eşleşme sayacı0başlangıcıyla `004203e4` çağrısı. Dönen maliyet EDX:EAX ve
   adresle değiştirilen eşleşme sayısı ayrı gözlemlerdir; liste uzunluğundan
   uydurulmaz. Sonradan sabit vektör ve taze EAX dizileri için bound maliyet
   modeli eklendi; [SELL_MERCHANT_COST.md](SELL_MERCHANT_COST.md).
3. `0046258c` taze coin EAX okuması; count0olsa da önce bu sonuç gerekir.
4. Maliyet QWORD + sıfır genişletilmiş coin DWORD,64bitte sarılarak toplanır.
5. Eşleşme sayısı0ise sonuç1. Değilse signed64 toplam>=0x7d2b74ff
   (2099999999) ise bildirim/string bloğunun ayrı normal dönüşünden sonra2;
   daha küçük toplamda0. Bu değerler yerel helper kodlarıdır, sunucu ACK'i değildir.

Decompiler `0042060c` için count0varsayarak bazı dalları erişilmez göstermişti.
Assembly'de sayacın adresi helper'a verildiğinden bu varsayım kullanılmadı;
üç dönüş dalı korunur. Native bildirim/string etkileri uygulanmaz. Açık
`over_limit_span_returned` gözlemi bunların gerçekleştiğini tek başına kanıtlamaz.

`MerchantSnapshot.sell_setup_inputs`, source setup sonucunu runner phase2'ye
bağlar. Aynı anda legacy setup_result verilemez. Hazırlık veya sonraki gözlem
eksikse tamamlanmış setup üretilmez. Plan yeniden çalıştırıldığında yeni gözlem
örneğidir; native callback içinde dondurma/devam, istisna, yeniden giriş veya
aynı anda vektör değişimi emüle edilmez.

## Workbench bağlantısı

SELL ekranında varsayılan kapalı “Satış listesi hazırlayıcısını bağla” seçeneği
yeni denemede alınır. Panel seçeneği açıkken SELL ListView, kapalıyken ayrı
örnek satır kullanılır. Maliyet QWORD/eşleşme sayısı/coin DWORD alanları açık
helper örnekleridir; boş giriş bilinmeyen değer olarak kalır. Gerçek envanterden
hesaplanmaz. Sayılar normal setup zaman kapısından ve liste planından sonra
okunur; ulaşılamayan bozuk alanlar erken hata üretmez.

Setup tamamlanınca hazırlanan kayıtlar phase3 typed seçim modeline verilir.
API'de kaynak session reset/6801handoff frame'i de eklendi; [SELL_SESSION.md](SELL_SESSION.md).
Bu frame'in UI bağı henüz yoktur; önceki workbench yolu aynı kapsamda kalır.
Taze item/used/adet ve native tail dönüşü yokken legacy sentetik seçiciye
düşülmez. Workbench henüz bu taze envanter gözlemlerini sağlamaz, burada açık
gözlem bekler. Seçeneği çalışma sırasında kapatmak captured modu değiştirmez.
Oyun okuma/yazma, paket gönderme, alarm veya banka işlemi yapılmaz.

15 yeni test; gerçek SELL yolu, clear/append/count gap'leri, signed count,
raw alan genişlikleri, seçiciye kayıt aktarımı, byref count, coin sırası,
limit eşitliği, signed64 sarma ve runner bağını kapsar. Tam birim çalıştırması
1811test ile geçti (8.672s). `work/verify_sell_preparation_ui.py` işaretsiz
satır, fiyat QWORD, lazy maliyet alanları, boş eşleşme sonucu1ve envanter gap'inde
legacy bypass olmamasını doğrular. Önceki BUY panel testi de yeniden geçti.
Genel gizli `smoke_ui.py` de1037kontrol/11form/18sekme ve mevcut davranış
kontrolleriyle geçti. Sonraki lazy coin-girdi düzeltmesi ayrı hazırlık UI testiyle
yeniden sınandı; genel smoke o aşamada tekrar edilmedi. Maliyet normal sabit-
vektör modeli sonradan eklendi. Canlı uyumluluk ve native heap/etki eşdeğerliği açık.
