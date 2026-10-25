# Satış callback'inin coin alarmı kapısı

18 Ekim 2026: `merchant_sell_coin_alarm.py`, `00420f33..00420f9b` prefix'ini
verilen gözlemler üzerinde modeller. Bu kod phase0..6 ayrımından önce çalışır.
Fonksiyonun daha erken VCL/string başlangıcı ve ortak epilog bu modelin dışında
kalır. Coin ve alarm yardımcıları native olarak çağrılmaz.

Kaynak önce enable BYTE +e0 okur. Sıfırsa coin EAX veya referans gerekmez.
Nonzero ise `0046258c` için taze coin DWORD EAX sonucu istenir ve EDX sıfırlanır.
Önce reference QWORD'un high DWORD +ec alanı karşılaştırılır. High nonzero ise
low +e8 okunmadan mismatch dalına geçilir. High sıfırsa low ile EAX karşılaştırılır.
Bu unsigned artış veya azalış eşiği değil, zero-extended DWORD ile QWORD eşitliğidir.
Her iki yönde coin değişimi aynı dalı açar. Eşitlikte alarm dönüşü gerekmez.

Mismatch dalı `00420f59..00420f9b` string/hazırlık, `00404260` çağrısı ve cleanup
span'ının normal dönüşünü ayrı ister. Native ses, mesaj veya harici bildirim
üretilmez. Model yalnız kaynakta çağrıya erişildiğini planlar. Bu prefix referans
coin'i güncellemez; değişim sonraki callback'te hâlâ varsa alarm yolu yeniden
planlanabilir. Otomatik debounce, yeni referans veya tek-sefer bayrağı eklenmez.

`MerchantSnapshot.sell_coin_alarm_inputs`, aktif SELL runner'da phase işleminden
önce tüketilir. Eksik coin/referans/normal dönüş phase'i ilerletmez. BUY yoluna
uygulanmaz. Raw değerler verilmediğinde legacy deneme modu ayrı kalır; bu,
native caller'ın bu koşulu atladığı anlamına gelmez.

## Panel ve deneme arayüzü

`sell_coin_alarm_from_panel` derlenmiş +e0 ve tam QWORD +e8 alanlarını gözleme
taşır; güncel coin veya helper dönüşü uydurmaz. `Sell Merchant` denemesinde
**Panel ayarlarını kullan** seçimiyle alınan configuration bu prefix'e bağlanır.
Coin alarmı enable ise ayrı güncel coin örneği boş kaldığında beklenir. Mismatch
durumunda yalnız ayrı **Alarm işlemi normal döndü (örnek)** kutusu dönüş örneğidir;
genel ready kutusu bunun yerine geçmez. Kaynak prefix tamamlanmadan daha sonraki
setup maliyeti/liste girdileri parse edilmez. Coin alarmı kapalıysa örnek coin
metni okunmaz. Çıktı yerel plan ve canlı doğrulama=false bilgisini gösterir.

Bu, fail-policy alarmı +d8 ile aynı koşul değildir; o dalın alarm/route etkileri
bu değişiklikle tamamlanmış sayılmaz. Workbench girişleri elle verilen örneklerdir;
oyundan coin okunmaz ve gerçek alarm span'ı çalıştırılmaz.

## Kanıt ve test

`work/audit_sell_coin_alarm.py`, eski ve güncel sabit hash'li dosyada **54 talimat
kaydının** baytlarını doğrular. Enable, helper callsite, zero-extension, high/low
okuma sırası ve JZ/JNZ eşitlik akışı ayrıca anchor kontrolleridir. Rapor:
`outputs/FarmexBot_satis_coin_alarm_kod_kaniti.json`.
Ghidra statik kanıtıdır; REA Evidence veya yardımcı gövde/ABI yürütmesi değildir.
Örtüşen talimat kayıtları benzersiz fonksiyon tamamlanması sayılmaz.

8 yeni test dahil **1965 yerel test geçti** (7.553 saniye). Ayrı gizli own UI
kontrolü panel→prefix bağını, eksik coin/alarm dönüşünü, sonraki setup alanlarının
erken okunmamasını ve referansın değişmemesini doğrular. Önceki satış maliyeti
arayüz kontrolü de geçti. Genel UI smoke/görsel layout onayı bu aşamada yapılmadı.
Orijinal bot veya oyunla etkileşim, native alarm ve canlı uyumluluk doğrulanmadı.
