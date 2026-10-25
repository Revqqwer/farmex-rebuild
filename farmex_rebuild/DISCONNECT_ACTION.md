# Bağlantı kesilince işlem seçimi

`disconnect_action.py`, `00459970` içindeki `00459c5a`–`00459e06`
aralığının 105 talimatlık normal kontrol yollarını modeller. Önceki periyodik
DC modeli ve dört katmanlı gönderici bileşimiyle henüz birleştirilmemiştir.
`support_engine` içindeki eski yüksek seviyeli relog simülasyonu bu kaynağın
tam davranış sertifikası olarak kullanılmaz.

Sıra: context+8a etkinlik, global561f60 üzerinden bot durdurma yardımcısı,
context+8b alarm, context+74 başlatılmış bayrağı, context+8c işlem etkinliği.
Başlatılmışsa model `459e06` geri sayım devamına ulaşır; geri sayımı çalıştırmaz.
Varsayılan context562194, daha önce byte doğrulanmış callback çağrısının değeridir.

| İşlem | Kaynak yol ve model sınırı |
|---|---|
| 0 / PC Kapat | 521457 disk literalinde `shutdown -s` bulunur. String kurucusu sonrası **yerel string pointer** ayrı alınır; sıfırsa521463 boş literal fallback olur. WinExec ve cleanup için ayrı normal dönüşler gerekir. Hiçbir komut çalıştırılmaz. |
| 1 / Oyunu Kapat | GetCurrentProcess **argümansızdır**; önceden PUSH0, sonraki TerminateProcess çıkış kodudur. Yakalanan handle ile çağrı niyeti kaydedilir. Dönüş gözlenirse yerel savedFS değeriyle FS0 geri yükleme niyeti ve459faa devamı kaydedilir. Gerçek süreç kapanması doğrulanmaz. |
| 2 / Relog At | +74 ve+75 bayrakları **tick çağrısından önce** yazım niyetine dönüşür. Tick dönüşü ve EAX ayrı alınır; +78 düşükDWORD, +7c yüksek0, +80/+84 sıfır yazımları korunur. Üç bağımsız UI kök zinciri ve iki sanal çağrı arasında GetPageIndex bulunur; fullDWORD sonucu aktarılır.412ed0 başlangıç yardımcısı opak kalır. |

Üç mod karşılaştırması aynı alanı ayrı ayrı yeniden okur. Model, aralarında
değişen değerleri temsil eder. Alarmın kurucudan dönen EAX adresindeki DWORD
okuması ile komutun yerel pointer okuması birbirine karıştırılmaz. Eksik dönüş
veya değer geldiğinde önceki yazım/çağrı niyetleri korunur, sonraki okuma yapılmaz.
Adres aritmetiği düşük32bit olarak tutulur; BYTE girdiler255 ile sınırlıdır.

`JailObservation` yalnız ulaşılan noktaların değerlerini ve ayrı normal dönüş
onaylarını taşır. Kernel argümanları fiziksel PUSH sırasındadır; VCL register
argümanları etiketlidir. `complete`, yalnız belirtilen devam adresine varıldığını
gösterir. Constructor/cleanup/alarm/stop/VCL/start yardımcıları, hata/SEH yolları,
ayar üreticisinin bu alanlara bağlanması, gerçek native etkiler ve canlı oyun
uyumluluğu açık kalır. Python modeli hiçbir Windows API çağrısı yapmaz.

Kanıt: eski ve yenilenmiş sabitlenmiş modüllerde441caller+5importthunk, toplam892
talimat kaydı byte doğrulandı; bunlar105talimatlık kapsamın tamamlandığı anlamına
gelmez. Mevcut REA caller analizi yeniden kullanılır, yeni analiz çağrısı yapılmaz.
Disk literal doğrulaması runtime string içeriğini veya işlem başarısını kanıtlamaz.
