# Rota klasörü, panel seçimi ve profil bağı

Güncelleme: Diğer8tür de aynı own katalog/profile/runtime Text akışına
bağlandı. [GLOBAL_ROUTE_PANEL.md](GLOBAL_ROUTE_PANEL.md) güncel10-combo
kapsamını ve1082talimatlık ayrı source producer denetimini açıklar. Aşağıdaki
iki-combo ve “diğer8stand-in” notları önceki aşamayı anlatır. Native runtime
ve canlı uyumluluk hâlâ açıktır.

18 Ekim2026. Ayar panelindeki **Rota klasörü** düğmesinden bir klasör seçilir.
Tedarik veya Kontrol/karakter ölümü bölümündeki rota combosu açılınca o klasör
yeniden taranır. `read_local_route_catalog` Python os.scandir ve explicit
1254/65001 Windows codec'iyle kaynakta doğrulanmış byte filename politikasını
uygular. Rota editörünün klasör/kod sayfası alanları aynı ayarları gösterir.

`.R` uzantısı, en az3bayt isim, sırasını/tekrarını koruma ve boş katalogda
placeholder davranışı korunur. Yerel adapter dizin türünü ayrıca süzmez.
Klasör açma OS hatası kaynak opendir-null yoluna benzer biçimde boş
vector/placeholder üretir; önceki own seçenekler temizlenir. Tarama sırasında
OS hatasında o ana kadar okunan eşleşmeler gösterilir. İki hata da ayrıca
kaydedilir ve sağlıklı/tam tarama sayılmaz. Kayıplı filename dönüşümü veya
10000entry bütçesi çözülmemiş helper/yerel sınır olarak kalır; bu durumda
önceki own seçenekler korunur. Ayrıntı: [ROUTE_CATALOG_TERMINATION.md](ROUTE_CATALOG_TERMINATION.md).
os.scandir CRT locale/record ordering veya native readdir'in
yerine doğrulanmış eşdeğer sayılmaz. Dosya içeriği tarama sırasında açılmaz.

Başarılı refresh yalnız açılan combonun seçeneklerini değiştirir; own seçim
-1e sıfırlanır, kullanıcı dosyayı seçer. Bu reset own UI politikasıdır;
native Clear/Add'ın pencere etkileri ayrıca doğrulanmayı bekler. Diğer rota
seçimi, listeler ve scalar ayarlar korunur. Eski DFM'deki tek placeholder
üzerinden yüksek ItemIndex'in dosya adına eşit olduğu varsayılmaz.

Rota editöründe **Tedarik/dönüş için panelde seçili rota dosyasını kullan**
varsayılan açıktır. ConfigurationPanel gerçek own seçenekleri+seçili indeksi
Unicode Text'e dönüştürür; Supply compiler580/584 metinlerini doldurur.
RoutePage bu metni explicit codec ile kayıpsız ANSI'ye dönüştürüp mevcut
manual-first/cyclic override seçimine, `.R` importer'a ve yerel yürütücüye
aktarır. Seçim yoksa boş isim kaynak unselected error yolunu kullanır;
oyuna hareket veya paket gönderilmez. Legacy manual seçenek kapatılarak
denenebilir; diğer8türün runtime filename global'leri hâlâ explicit stand-in.

Kendi JSON profilinin **version3** biçimi values/lists yanında iki rota
combonun seçeneklerini, klasörü ve kod sayfasını saklar. Bu, Farmex INI
biçimi değildir. Aynı snapshot'ta seçenek+indeks saklanması profil yeniden
açıldığında dosya adını korur; açma otomatik klasör taraması yapmaz. Sonraki
DropDown klasörü yeniden tarar ve seçimi sıfırlar. Codepage alanı olmayan
ilk v3snapshot'ları1254kabul edilir. Version1/2profil yükleme desteklenir;
eski profil yüklendiğinde önceki dinamik seçenekler/klasör/codepage temizlenir.

Profil kontrolü seçim sınırlarını tüm son state üzerinde uygular; dinamik
metadata yalnız iki bilinen rota combosu için geçerlidir. Hatalı seçenek,
indeks, liste veya metadata yüklemesinde Profiles state'i değiştirilmez.
Save validation bozuk veriyle eski profil dosyasını değiştirmez. Seçenekler
Unicode olarak saklanır; klasörün hâlâ var olduğu veya dosyanın aynı içerik
olduğu profile metadata'sından çıkarılmaz.

Önceki12test gerçek own geçici klasör/upper-lower uzantı/Unicode/dizin entry,
lossy codepage/bütçe, dinamik selection, v3roundtrip, legacy reset,
invalid-profile atomicity ve unrelated bounds isolation sınar. Gizli own UI
kontrolü iki comboda gerçek event, Türkçe dosya adı, farklı wait adımı,
profil sonrası gerçek render, eksik klasör ve seçimsiz yüklemeyi sınar.
Bu, native/runtime/live parity kanıtı değildir. Önceki disk kanıtları
Richard1196/CRT223talimattır; bu UI bağlantısı yeni native talimat sayısı eklemez.
