# Erişilmiş rota çıkış dalından pazar enable yazısı

18 Ekim 2026: `route_resume.py`, güncel004eb2c4/eski004eb2a8 yordamının yalnız
ortak `004eb9c9..004eb9f0` tail'ini modeller. Bu tail'e erişildiği dış sözleşmedir;
rota bittiğini veya önceki branch'lerin buraya geldiğini kendi başına tespit etmez.
İki başka enable writer'ı ve önceki erken çıkışlar bu modele dahil değildir.

Global553e7c → guarded DWORD root → taze global554020 offset → guarded BYTE
sonucu EAX → TEST AL akışı kullanılır. AL nonzero ise active ve enable kendi
giriş değerlerinde kalır; önceki bir enable1otomatik temizlenmez. AL0ise önce
object BYTE+5d9=0, sonra global BYTE561f6c=1 yazısı planlanır. Bunlar kendi
mapping/projection değerleridir; gerçek belleğe yazılmaz.

`source_coin.py` içine eklenen `plan_guarded_byte`, 0045dbdc normal dönüşlerini
modeller. Null argüman API istemeden EAX0, verilen VirtualProtect sonucu0ise EAX0
döner. Nonzero API sonucu için ayrı BYTE değeri gerekir. `MOV AL,[ECX]`, API
sonucunun EAX üst24bitini korur; model tüm EAX'ı BYTE'a indirgemez. Örneğin
API return100hex/BYTE0ile EAX100hex kalır, fakat caller AL0dalına girer.
API veya BYTE gözlemi eksikse0uydurulmaz. Null/failure/gerçek gözlenen0kökenleri
ayrı saklanır. Bu nedenle enable yazısı planlanması gerçek oyun predicate'inin
başarılı okunması veya rota başarısı değildir.

Root0/failure sonrası caller offset okumasına devam eder. Adres DWORD'da sarılır;
son BYTE argümanı0olabilir. Source normal dalını takip ederken ek null guard veya
başarı şartı uydurulmaz. VirtualProtect/bellek API'si çağrılmaz; protection/fault,
concurrency ve native helper yan etkileri emüle edilmez. Getter'ın gerçek oyun
alanı anlamı bu çalışmayla adlandırılmış veya kanıtlanmış sayılmaz.

## Dış callback ile kendi entegrasyonu

Testte kendi RouteStart enable0/active1çıktısı tail'in own girişidir. Tamamlanan
tail enable1çıktısı ayrı explicit post-enable örneği olarak MerchantCallback'e
verilir; post-master ve dış route-helper normal dönüşü ayrıca sağlanır. Böylece
yerel gate SELL phase çağrısına izin verebilir. Tail gap'inden native helper dönüşü
veya callback post-global'i otomatik üretilmez. Tail'den sonra native global
değişmediği varsayımı yapılmaz; gerçek taze callback gözlemi ayrı kalır.
Workbench henüz bu tail gözlemleri için kontrol veya otomatik binding sunmaz.

`work/audit_route_resume.py`, iki hash'li dosyada tail ile protected BYTE/DWORD
gövdelerinden **128 talimat kaydını** baytlarıyla doğrular. Root/offset/getter,
AL testi, iki store sırası, BYTE MOV AL ve size1/40hex/VirtualProtect import
kimliği ayrıca anchor kontrolleridir. Rapor:
`outputs/FarmexBot_rota_pazar_devam_kod_kaniti.json`.
Ghidra statik kanıtıdır; REA Evidence veya native yürütme değildir. Önceki
auditlerle örtüşen kayıtlar benzersiz kapsam veya fonksiyon tamamlanma sayılmaz.

10 yeni test dahil **2034 yerel test geçti** (6.979 saniye). EAX üst-bit korunması,
AL0/nonzero, null/failure/zero provenance, root0sonrası offset, adres wrap, eksik
gözlemler ve start→reached tail→fresh callback kendi zinciri sınandı. UI değişmedi;
UI smoke tekrarlanmadı. Gerçek rota bitişi, önceki helper yolları ve canlı
uyumluluk açık kalır.
