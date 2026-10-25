# Zone/Town durdurma koşullarının kaynak bağı

`control_stop_binding.py`, tamamlanmış kendi Kontrol Ayarları üretici planındaki
BD/BE bayraklarını iki ayrı paket işleme modeline bağlar. API aşamasıdır;
arayüzdeki Kontrol Ayarları ekranı hâlâ yalnız ayar üretimini önizler.

Zone için mevcut `IncomingTPDispatchFrame` ve `TPFrame` kullanılır.
`0x27` paketinde byte2 sıfır değilse ilk bölge sorgusu normal dönmelidir.
Tam EAX, byte2'den farklıysa BD bayrağı (`562251`) okunur; sıfır değilse
`0040ae0c` için `(0,561f34)` fiziksel PUSH sıralı durdurma çağrı planı oluşur.
Sonraki TP cooldown, ayrı bölge sorguları ve koruma dalları mevcut modelde kalır.
Zone eşitse veya byte2 sıfırsa BD okunmaz. Yeni bir Zone yordamı kopyalanmadı.

`town_request.py`, güncel `004e3144` fonksiyonunun yalnız Town yolunu ekler:
prologue normal dönüşünden sonra `06,10,20,33` opcode karşılaştırmalarının
başarısız yolları, `004e35de` içindeki `0x48` dalına ulaşır. BE (`562252`)
sıfır değilse aynı durdurma çağrısı istenir. Bu çağrı normal döndükten sonra,
veya BE zaten sıfırsa, kaynak EAX=1 üretir ve normal RET0xc kuyruğuna gider.
Bu değer paket teslim edildi, iptal edildi veya sunucu onayladı anlamına gelmez.
Diğer eşleşen dallar kendi gövdelerinde durur; sonraki dallar tamamlanmış sayılmaz.

Yalnız erişilen bayrak kendi ayar snapshot'ından türetilir. O anda çelişen gözlem
reddedilir. Daha önce kabul edilmiş bayrak, durdurma dönüşü beklenirken sonraki
gözlemle değiştirilmez. Native işleyici daha sonra bayrağı yeniden değiştirebilir;
bu köprü açıkça sabit yerel denemedir. Gerçek packet pointer/uzunluk kimliği,
hook kurulumu, stop yordamının bütün etkileri, ABI/SEH ve oyun uyumluluğu açık kalır.

9 Town ve 8 bağlantı testi eklendi. Kaynak kanıtı: yeni Town REA analizi,
korunmuş TP REA kanıtı ve iki sabit PE görüntüsündeki talimat baytları.
