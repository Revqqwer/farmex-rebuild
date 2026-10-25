# Item kırma ayarlarının panel bağı

23 Ekim 2026. Yerel deneme sayfasındaki **Item Kırma Ayarları** seçeneği,
Item Kır sekmesindeki üç gerçek kontrolü tüketir: chAutoCrashItems,
txtCrashItemSpeed ve rdAbbys. Orijinal panel kontrol sayısı değişmez.
Toplam bağlı girdi378, bağlanmamış düzenlenebilir kontrol145 olur.

`ItemBreakSettingsTrial` üç alanın değişmez snapshot'ını alır. Etkinleştirme
ve hız, mevcut tipli üretici prefix'ine verilir. Sayı dönüşümü, helper normal
dönüşü ve metin temizliği ayrı yakalamalardır; bekleyen dönüş sırasında
önceden kabul edilmiş enable/hız store'ları korunur. Abyss getter'ı yalnız
ulaşıldığında panelden alınır. Kaynak tekDWORD reset planı yerel shadow'a
bir kez uygulanır. Abyss seçili değilse önceki+c alanı korunur;0 varsayılmaz.

Kaynak API'sindeki taze enable okuması bağımsız kalır. **Bu panel denemesi**
kendi stabil shadow'unda o baytı okur ve dış örneğin bunu değiştirmesini
reddeder. Bu sözleşme gerçek VCL yardımcılarının oyun sürecindeki alanları
koruduğunu kanıtlamaz. Başlat/durdur yardımcısı yalnız çağrı planıdır.

“Panel ayarlarını önizle” açıkça sentetik normal/helper örneği üretir.
Sayısal örnek yalnız signed decimal64 alt kümesini kullanır; kaynak RTL
parser'ının bütün sözdizimi çözülmüş değildir. Kaynakta olmayan minimum hız
kuralı eklenmez.−1 girdisi düşükDWORD ffffffff olarak saklanabilir. Hatalı
metin otomatik fallback'e çevrilmez; catch yolu için ayrı açık gözlem gerekir.

Snapshot değişirse eski örnek reddedilir. Panel-derived checkbox/text ve
yerel fresh-read değerleri çelişkili yakalamayla değiştirilemez. Sonraki
hatalı örnek daha önce kabul edilen store'ları geri almaz. Profil kaydı ve
yeniden yükleme üç gerçek alanın değerlerini korur. HP gibi ilgisiz deneme
girdileri bu ayar yolunu engellemez.

9 yeni test; toplam3950 test. Gizli UI kontrolleri gerçek checkbox/radio ve
metin widget'larını kullanır. Bu aşama ayar paneli bağıdır; otomatik worker,
manuel Button5 ve istek kuyruk API'leri ayrıca vardır ve burada gerçek
oyun işlemi olarak çağrılmaz. Önceki genel Item Kır politika denemesi de bu
kaynak ayar sertifikasının yerine geçmez. Diğer modlar/native/canlı uyumluluk
tamamlanmış sayılmaz.
