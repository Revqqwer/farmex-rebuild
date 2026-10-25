# Relog geri sayımı ve işlem devamı

`relog_countdown.py`, `00459970` içindeki `459e06`–`459fa0` normal kontrol
yollarını kapsar:122talimat. `DisconnectRecoveryFrame`, önceki işlem modelini
bu bölüme yalnız gerçek `459e06` devam adresi üzerinden bağlar. İlk relog kurulum
yolu `459fa0` adresine atladığından aynı poll içinde geri sayıma sokulmaz.
Farklı poll'lerin yakalanmış değerlerini otomatik olarak aynı saymaz.

| Aşama | Kaynaktan uygulanan davranış |
|---|---|
| Bekleme | context+75 sıfırsa çıkılır. Tick çağrısı ve EAX dönüşü ayrı gözlenir. Context+78/+7c tazeDWORD okumaları ile64bit çıkarma yapılır. |
| Saniye |00503e75 helper'ının normal dönüşü ayrı gerekir; sonuç bitleri önceden doğrulanmış `source_math64.divide64_bits` ile signed64/1000 olarak türetilir. Negatif bölüm sıfıra doğru yuvarlanır. |
| Kalan | Context+94 tazeDWORD değeri eksi bölümün **düşükDWORD** sonucu düşük32bit tutulur. Signed32 karşılaştırmada sıfır/negatifse yalnız+75 sıfırlanır. Yeni relog çağrısı veya tamamlanma olayı üretilmez. |
| Bildirim aralığı | Ayrı tick değeri ile553ce8/553cec tazeDWORD'ları arasında64bit çıkarma yapılır. Negatif fark ve1000'den küçük fark atlanır; tam1000 geçer. |
| Metin |521464 disk literalinde ` Saniye Sonra Relog Atilacak..` bulunur. Constructor, sayı, boş Unicode nesnesi, birleştirme, ANSI dönüşümü ve üç cleanup ayrı opak sınırdır. Runtime metin byte'ları türetilmez. |
| Kuyruk | Ayrı size/capacity dönüşleri unsigned karşılaştırılır. Fast dalda taze561f48 okunur;00409fbc dönüş EAX'ı561f48'e yazım niyeti olur. Slow dalda ayrı iterator ve0040a01c dönüşleri gerekir; kaynakta olmayan doğrudan561f48 yazımı eklenmez. |
| Zaman damgası | Kuyruk helper normalinden sonra üçüncü tick ve EAX ayrı alınır;553ce8 düşükDWORD ve553cec yüksek0 yazılır. Son ANSI cleanup dönüşü eksikse bu yazımlar korunur. |

Tick sarılması32bit modüler geçen-süre hesabı olarak düzeltilmez: kaynak64bit
çıkarma yaptığından sarılma negatif süreye ve beklemenin artmasına yol açabilir.
Bu davranış kaynak modelinde korunur. Eski `support_engine.advance_relog` kendi
yüksek seviyeli simülasyonudur; bu kaynak hesabının sertifikası değildir.

Önceki modeldeki `relog_start` etiketi yalnız opak `00412ed0` çağrı sınırının
adıdır. Çağrının kendisi başarılı relog, thread başlatma veya yeni oturum açma
kanıtı sayılmaz. Asıl relog aşamalarının+74/+75 bayraklarını nasıl tükettiği
ayrı analiz gerektirir.

Tüm okumalar, yazımlar, kuyruk ve çağrı niyetleri yereldir. Windows/VCL/RTL,
oyun, ağ veya süreç API'si çalıştırılmaz. Ayrı native normal dönüş gözlemleri
kontrol devamını ifade eder; helper başarısı veya oyunda teslim kanıtı değildir.
Exception/SEH/ABI, string/queue helper'larının iç semantiği, tam441talimatlık
fonksiyon, callback/scheduler ve canlı uyumluluk sertifikası verilmez.

Kaynak kanıtı: iki sabitlenmiş sürümde441caller+57division+1tick import thunk,
toplam998talimat kaydı byte doğrulanır.122talimatlık bounded aralık bu toplamın
içindedir; tekrar toplanmaz. Mevcut caller ve division REA kanıtları kullanılır.
