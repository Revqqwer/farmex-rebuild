# Bağlantı kesilmesi yordamının normal kontrol bileşimi

`DisconnectRoutineFrame`, `00459970` yordamındaki iki context+6e dalını bağlar:
giriş/SEH hazırlığı, periyodik DC tüketicisi ve gönderici modelleri, özel yeniden
bağlanma yolu veya otomatik işlem seçimi, geri sayım ve ayrı çıkış sınırları.
Bu bir normal kontrol bileşimidir. Yardımcıların opak semantiği, exception/SEH,
native stack/register yürütümü ve gerçek oyun etkileri tamamlanmadığı için
**tam fonksiyon sertifikası değildir**.

| Kaynak aralığı | Model / talimat sayısı |
|---|---|
|59970–59981|Opak giriş/SEH hazırlığı6|
|59981–5998e|Context+6e kapısı3|
|5998e–59a6e|Özel ilk kurulum57|
|59a6e–59c05|Özel geri sayım122|
|59c05–59c14|Özel FS geri yükleme ve ortak çıkışa atlama3|
|59c14–59c5a|Periyodik DC kapısı17|
|59c5a–59e06|Otomatik işlem/alarm/relog kurulumu105|
|59e06–59fa0|Normal relog geri sayımı122|
|59fa0–59faa|Normal FS geri yükleme2|
|59faa–59faf|Ortak stack/return sınırı4|

Bu aralıklar441talimatı bir kez kapsar; kapsama sayımı tek başına semantik
doğrulama değildir. Kaynak kontrol yollarının modele bağlanmasını gösterir.

Özel yolda561f60 bot bayrağı durdurma yardımcısını koşullar. Context+74 zaten
doluysa doğrudan özel geri sayıma gidilir. İlk kurulumda553e46 **tam1** ise
context+70 alanına31, diğer BYTE değerlerinde1 yazılır.553e80 kökü ve55406c
offset'i ile byte okuyucu çağrılır. Sonuç **AL sıfır değilse**, kök/offset yeniden
okunarak ayrı0045de4c byte sıfırlama niyeti oluşturulur. Bu kaynak davranışı
yalnız kayıttır; bellek koruması değiştirilmez veya belleğe yazılmaz.

+74/+75 bayrakları tick'ten önce yazılır. Tick sonrası+78/+7c zaman,+80/+84
sıfır ve ayrıca+88 sıfır yazımları gelir. Tek UI reset zinciri ve00412ed0 opak
runtime snapshot sınırı vardır. Otomatik DC yolundaki page index seçimi burada
yoktur. İlk kurulumun aynı turunda geri sayım çalıştırılmaz.

Özel ve normal geri sayım aynı arithmetic/control çekirdeğini kullanır; kaynak
farkları sabit profillerle tutulur:

|Alan|Özel|Normal|
|---|---|---|
|Giriş|459a6e|459e06|
|Bekleme|context+70|context+94|
|Bildirim timestamp|553cdc/553ce0|553ce8/553cec|
|Disk suffix|521435|521464|
|Çıkış|459c05|459fa0|

Üst bileşim context kapısını bir kez tüketir. Normal yoldaki dört katmanlı
gönderici planı tamamlanmadan otomatik işlem modeline geçmez; tüketici ve dış
normal dönüşler ayrı kalır. Sonraki işlem/çıkış eksikse daha önceki payload,
stub ve timestamp kayıtları korunur. Child girişleri yalnız ulaşılan kaynak
kenarından türetilir; erken verilen dönüşler eksik child'ı atlayamaz.

Giriş, savedFS değeri, FS geri yükleme ve stack/return ayrı gözlemlerdir. İşlem1
normal dönüş yolunda FS zaten işlem modelinde geri yüklenmiş sayıldığından
ortak çıkışta ikinci FS geri yükleme niyeti eklenmez. Bu gözlemler native dönüş
veya exception tesliminin sertifikası değildir.

Model gerçek tick, kernel/VCL/RTL, kapanış, bellek, thread, kuyruk, alarm, ağ veya
oyun çağrısı yapmaz. `complete` yalnız açık gözlemlerle normal kontrol planının
sona ulaştığını ifade eder. Sıfır canlı uyumluluk ve tam fonksiyon sertifikası
durumu korunur.412874/412adc/412f48 hook tüketicileri, post-login toparlanması ve
gerçek yeniden oturum açma zinciri ayrı doğrulama gerektirir.
