# Rota modu, hareket kapıları ve çıkış bileşimi

18 Ekim 2026. `route_motion.py`, güncel `004eb2c4` içinde `004eb6a6`
adresine ulaşıldığı sözleşmesiyle başlar. Önceki rota satırı yürütücüsü,
6d9/6da durumları, rota değiştirme ve entry koşulları bu API'ye dahil değildir.
Amaç, önceki `route_resume_paths.py` çıkışlarını gerçek üst dallarına bağlamaktır.

## Kaynak kararları

Global DWORD561f58 ilk okumada0 ise object BYTE574 okunur. Nonzero ise
signed index548 guard'ı okunur; indeks negatif değilse iki ilave taze indeks,
metin dönüşümleri ve arayüz güncellemesini içeren 004eb6cb..004eb711 span'ının
normal dönüşü ayrı gözlem ister. Guard indeksinden sonraki indeksler veya
metin içerikleri türetilmez.

Metric yardımcısının girdileri sırasıyla global562004 ve562000 signed DWORD
değerleridir. Kaynak FILD/FSTP ile float argümanları üretir, 00460548 ve CRT
__ftol çağrıları sonrasında düşük EAX DWORD'unu saklar. Model bu dönüşümleri
ve yordamları yaklaşık hesaplamaz: son EAX bağımsız, açık gözlemdir. Bu DWORD
signed32 olarak kullanılır. Fiziksel mesafe birimi veya helper içeriği bu
çalışmayla doğrulanmış sayılmaz.

Signed metric70'ten büyük veya1,5'ten küçükse süreye bağlı çıkış yoluna
gidilir. FILD girdisi tamsayı ve sabit1,5 tam temsil edilebilir olduğundan
kabul aralığı tam olarak2..70'dir. Kabul edilen aralıkta ayrı GetTickCount
DWORD sıfırla genişletilip tam QWORD56ff9c damgasından çıkarılır. Signed64
sonuç1500'den küçükse ortak çıkışa uğramadan dönülür.

Süre yeterliyse global BYTE561f7e nonzero hareket çağrısını engeller.
Aksi halde global553e7c→guarded DWORD root→taze global554034 offset→guarded
DWORD value zinciri okunur. Yalnız tam DWORD6 hareketi engeller. Root veya
getter failure0 olması ikinci offset/getter çağrısını atlamaz; adres32bitte
sarılır. Önceki guarded okuyucu null/failure/eksik gözlem ayrımları korunur.
Koordinatlar hareket için **yeniden okunur**; ilk metric girdileri tekrar
kullanılmaz. 004646b4 normal dönüşü ayrı gözlemdir. Mod0 bu çağrıdan sonra
doğrudan döner; ortak çıkışı çağırıp pazar izni uydurmaz.

İlk mod okuması nonzero ise kaynak global561f58'i yeniden okur. Taze değer2
değilse doğrudan ortak çıkış yolu çalışır. Taze değer2 ise önce global56fa88,
gerekirse56fa8c sıfır guard'ları okunur. İkisinden biri0ise isteğe bağlı
yardımcı içeren çıkışa gidilir. İkisi nonzero ise metric girdileri y/x
adreslerinden **taze** okunur; guard değerlerinden hesaplanmaz. Signed metric2'den
küçükse çıkışa gidilir. Diğer durumda aynı BYTE561f7e ve guarded DWORD==6
hareket kapıları vardır. Hareket için koordinatlar bir kez daha okunur.
Mod2 hareket yardımcısından sonra isteğe bağlı çıkış kontrolüne devam eder.

Çıkış planları kendi taze root/offset/BYTE gözlemlerini ister. Hareket
alanı554034 ile çıkış alanı554020 birbirine karıştırılmaz. Eksik çıkışta
kabul edilen active/enable girişte kalır; bilinen ön yazılar yalnız
prospective state olarak saklanır. Bu API saf yerel denemedir; helper yan
etkilerini emüle etmez, gerçek belleğe veya oyuna çağrı/yazı yapmaz. Durum
alanlarının korunması native helper'ın onları değiştiremeyeceğini kanıtlamaz.

## Kanıt ve doğrulama

`work/audit_route_motion.py` iki hash'li ikilide **260 talimat kaydını** disk
baytlarıyla doğrular. Dallar, taze okumalar,1.500ms karşılaştırması ve mod0
doğrudan dönüş/mod2 çıkışa devam farkı ayrı anchor'lardır. Her iki dosyada
float sabiti `0000c03f`=1,5; GetTickCount KERNEL32.DLL ve __ftol
CC32260MT.DLL import kimlikleri doğrulandı. Diğer auditlerle örtüşen kayıtlar
benzersiz kapsam artışı olarak sayılmaz. Bu Ghidra/disk kanıtıdır; REA Evidence
değildir. Rapor: `outputs/FarmexBot_rota_hareket_kapilari_kod_kaniti.json`.

19 yeni test dahil ilgili41 test geçti. Sınır değerleri, taze mod okuması,
sıfır koordinat kısa devresi, guard/metric/movement için bağımsız koordinatlar,
QWORD saat, tam6 karşılaştırması, null root sonrası ikinci getter, yardımcı
dönüşleri ve eksik çıkışın ön yazıları sınandı. Tam Python kontrolü:
**2065 test geçti (7.179 saniye)**.

Yerel entegrasyon testi mode0→timed exit→common tail→ayrıca verilmiş callback
post-enable/helper dönüşü→SELLphase1 zincirini kullanır. Bu native callback
veya canlı rota hareketi değildir. Workbench ve native kaynak değişmedi;
bu aşamada UI smoke/native fixture tekrarlanmadı. Bu API henüz rota ekranının
genel simülasyonuna bağlı değildir. Önceki rota entry/satır yürütücüsü, yardımcı
etkileri, gerçek hareket ve canlı uyumluluk açık kalır.
