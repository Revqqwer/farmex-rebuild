# Genie kupon ayarı senkronizasyonu

`genie_coupon_sync.py`, Richard içindeki `004576ec` fonksiyonunun yalnız
`00458143..004581b9` aralığını modeller (33 talimat). Önceki beş bayrağı
üreten 35 talimatla isteğe bağlı bağlanabilir. Bu, tüm fonksiyonun çözümü değildir.

Kaynak önce iki DWORD yardımcısı ve güncel ofsetlerle hedef adresi hesaplar;
ardından context+BA bayrağını yeniden okur. Önceki header yazımını bu yeni
okumanın yerine geçirmeyiz. Bayrak açık ve okunan AL sıfırsa bir yazma niyeti,
bayrak kapalı ve AL tam birse sıfır yazma niyeti üretir. Diğer byte değerlerini
normalleştirmez. Adres işlemleri 32 bit taşmayı korur; bekleme sınırında hesaplanan
adres saklanır. Yardımcı normal dönüşü, yazmanın gerçekleştiği kanıtı değildir.

11 yeni test; tüm Python paketi 3822 test geçti. Arayüz değişmedi;
önceki 1037 kontrol/11 form/18 sekme testi bu aşamada yeniden çalıştırılmadı.
Model oyuna yazmaz, kupon kullanmaz ve oyun içi etkiyi doğrulamaz.

Kaynak kanıtı: `FarmexBot_Genie_kupon_sync_kaniti.json` (üst outputs klasörü).
Yardımcıların sınırlı yerel talimat testi: [GUARDED_SCALAR_NATIVE.md](GUARDED_SCALAR_NATIVE.md).
