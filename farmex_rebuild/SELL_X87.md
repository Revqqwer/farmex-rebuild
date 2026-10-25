# Satış x87 hesabı ve CRT dönüşümü

18 Ekim 2026: `merchant_x87.py`, satış helper'ındaki signed-QWORD yükleme,
binary64 katsayı ile FMUL, FSUBP ve disk CRT `__ftol` dönüşümünün sınırlı normal
yolunu kesin rasyonel aritmetikle hesaplar. Host Python float aritmetiği,
`round(total*0.97)` veya matematiksel3/100varsayımı kullanılmaz.

Precision-control, bu çarpma ve çıkarma sonuçlarını24/53/64significand bitine
yuvarlar. Rounding-control için nearest-even, aşağı, yukarı ve sıfıra doğru
yönleri ayrı uygulanır. Bu mimari alanlar [Intel SDM Volume1, §8.1.5](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-1-manual.pdf#page=199)
ile karşılaştırıldı. FILD signed64 girdisi önce tam değeriyle alınır; sonra
her aritmetik sonucun precision/rounding aşaması ayrı hesaplanır.

## Disk yordamı

Korunan `cc32260mt_45b21b5cb5d13af3.dll` dosyası SHA256:
`45b21b5cb5d13af35bdc3a5c5ca058a8df679e579bed95c19aad0ac2dd423b8e`.
Doğrudan PE export tablosundaki `__ftol` ordinal2678/adres3222a778incelendi.
Ghidra17talimat/48bayt gövdeyi çıkardı; her kayıt yeniden disk baytlarıyla
doğrulandı. Rapor `outputs/FarmexBot_CRT_ftol_kod_kaniti.json`, kaynak çıktı
`outputs/Ghidra_CRT_ftol_kapsami.json`. Yerel Ghidra kanıtıdır, REA Evidence değildir.

Yordam CW'yi saklar, geçici değere0x0c01ORuygular, QWORD FISTP yapar, FCLEX
sonrasında asıl CW'yi geri yükler. Dolayısıyla son integer dönüşümü sıfıra
doğrudur; öncesindeki iki hesap ise kaynak CW'nin precision/rounding alanlarından
etkilenir. Model, katsayının kaynak binary64 baytlarını tam kesir olarak kullanır.
Yuvarlanan çarpım ve çıkarım kesirleri planda ayrıca gösterilir.

Bu bütün CRT analizi değildir. DLL çalıştırılmadı. Bulunan disk dosyasının
oyunda yüklü runtime olduğu veya mevcut oyun thread'inin bu CW ile çalıştığı
doğrulanmadı.

## Açık giriş sözleşmesi

`SellX87Sample(control_word,clean_context)` gerekir. CW verilmezse varsayılan
0x037fkullanılmaz. `clean_context=True`, temiz FP durumunu, en az iki boş x87
stack yuvasını ve bu hesap boyunca sabit CW'yi ifade eden açık gözlemdir;
native ölçüm yaptığımız anlamına gelmez. Yalnız tüm FP exception mask'ları açık,
desteklenen precision kodları ve olağan reserved bit düzeni kabul edilir.
Diğer bağlamlar gözlem açığı olarak kalır; trap/status/NaN/Inf emülasyonu yapılmaz.

Signed64 toplamdan başlayan bu sabit katsayılı normal ifade modellenir; genel
bir x87 emülatörü veya her ST(0) değeri için CRT replika değildir. İşlem
sonucu signed64 aralığı dışına çıkarsa tamamlanmış dönüş uydurulmaz. Kaynak
kimliği metadata'dır; her plan gerçek yüklü runtime doğrulamasınıFalsebırakır.

`SellSlotObservation.disk_crt_replay=True`, tail frame'inde bu modu seçer.
`x87_control_word` ve `x87_clean_context` açık verilmelidir. Aynı ulaşılan çağrıda
ham `ftol_qword` ile birleştirilemez. Bilinen bağlam veya mod seçimi frame
ortasında değiştirilemez. Ham dönüş gözlem yolu ayrı olarak korunur. Frame
sonucunun `ftol_source` alanı `observed` veya `local_disk_crt_replay` olur.
UI henüz bu tail/x87 girişleri için kontrol sunmaz; bağ API düzeyindedir.

## Bağımsız kendi x86 kontrolü

`native/sell_x87_fixture.c` kendi x86 programımızda FILD/FILD/FMUL/FSUBP ve
kontrol kelimesi değiştirilmiş FISTP/restore dizisini çalıştırır. FNINIT ile
fixture'a temiz stack sağlanır. Orijinal DLL yüklenmez veya çalıştırılmaz;
oyun süreci, driver, process handle, ağ veya oyun belleği kullanılmaz.
Sadece stdout'a integer sonuçlar yazılır.

`work/verify_sell_x87_native.py`, deterministic335QWORD girdiyi12CW ile
**4020örnekte** karşılaştırdı. Sıfır/negatif değerler, signed64 sınırları,
2^24/2^53çevreleri ve sabit seed'li kendi rastgele girdilerimiz dahil tüm
örnekler kesin modelle eşleşti. CW her örnekte geri yüklendi, fixture exit0.
Rapor `outputs/FarmexBot_satis_x87_native_testi.json`; son fixture SHA256:
`43e8916359112877fb6e4ee31ad1593e0946a23d6065c3eecdb5e40cb96c95ce`.
Önceki sürümün kaydı hash adlı ayrı dosyada korunur.

Derleyici sandbox'ta WinError623verdiği için yalnız bu kendi fixture'ımız
sandbox dışında derlenip çalıştırıldı. RunAs/oyun başlatma/oyuna erişim yoktur.
Kaynak ve deterministic header kaynak paketindedir; binary pakete eklenmez.
4020native örnek, Python birim test sayısına eklenmez ve canlı uyumluluk
kanıtı değildir. Gerçek runtime/CW, exception path'leri ve tüm native ABI açık.

Tam Python çalıştırmasında **1854 birim testi geçti** (7.431 saniye); bunun
13yeni testi kesin binary yuvarlama, bağlam gap'leri ve tail model bağını kapsar.
Önceki maliyet ve hazırlık gizli UI kontrolleri yeniden geçti. UI düzenlenmedi;
genel smoke son maliyet-modu aşamasındaki doğrulamadır.
