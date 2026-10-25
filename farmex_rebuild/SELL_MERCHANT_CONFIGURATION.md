# Satış pazarı scalar panel bağı

18 Ekim 2026: `merchant_configuration.py`, ortak `0041fea4` okuyucusunun SELL
alanlarını da kendi profilinden derler. Önceki BUY audit'i genişletildi: aynı
1128 talimat kaydı ve toplam24 published kontrol kaydı iki ikilinin baytlarıyla
doğrulandı. Bu, önceki1128'e ek yeni benzersiz talimat sayısı değildir. Güncel
rapor `outputs/FarmexBot_pazar_panel_ayar_kod_kaniti.json`; script
`work/audit_merchant_configuration.py`. Statik Ghidra/Delphi kanıtıdır; REA
Evidence veya native olay yürütmesi değildir.

| Profil girdisi | Nesne alanı | Kullanım |
| --- | --- | --- |
| SELL/BUY start | DWORD+00 | SELL önce gelir; BUY yalnız SELL kapalıysa okunur |
| Inventory sıra | BYTE+c8 | Runner'ın canonical `sell_inventory_order` seçimi |
| Yeniden kurma | BYTE+c9 | `reopen` |
| Yeniden kurma dakika | DWORD+cc | `reopen_minutes` |
| Ek bekleme saniye | DWORD+d0 | `extra_wait_seconds` |
| Stop/DC/Bank | DWORD+d4 | Ayrı IF'ler0/1/2 yazar, son checked kazanır |
| Alarm | BYTE+d8 | Derlenir; alarm çalıştırılmaz |
| Manuel rota | BYTE+d9 | Derlenir; rota başlatılmaz |
| Manuel rota combo Text | Ayrı Unicode Text | ItemIndex'ten türetilmez |
| Para değişimi alarmı | BYTE+e0 | Derlenir; canlı para izleme yoktur |
| Son para referansı | QWORD+e8/+ec | Tam64bit korunur; DWORD'a daraltılmaz |

Sayı metinleri için signed64 ASCII ondalık alt kümesi ve düşük DWORD politikası
BUY ile aynıdır. Gerekirse `numeric_results` ile ayrı açık EDX:EAX gözlemi
verilebilir. Hiçbir politika radyosu checked değilse önceki raw DWORD gereklidir;
stop uydurulmaz. Desteklenmeyen setup süresi ham derlemede korunur, mevcut
normal-saat runner köprüsü reddeder; clamp yapılmaz.

Para referansı ortak okuyucuda `00460fa4` yardımcısından gelir. Önceki fiyat
modeli aynı yardımcının ASCII digit/dot predikatını ve uzunluk>=4 nokta çıkarma
yolunu sağlar. `4.294.967.297` kendi yerel alt kümede4294967297 olur ve üst DWORD
kaybolmaz. `1.2` gibi kısa, noktalı ama decimal dönüşümü çözülemeyen girdi açık
kalır; ASCII predikatının reddettiği `abc` ise kaynak modelde bilinen0yoludur.
Native Unicode→ANSI, tüm parser biçimleri ve exception yolları doğrulanmadı.
Doğrudan `coin_qword` ayrı native helper sonucu gözlemi olarak verilebilir.

EnginePage `Sell Merchant` panel seçeneğinde scalar ayarlar başlangıçta alınır.
Varsayılan ek bekleme30s ile yerel setup kapısı91000ms'de açılır. Sıralama
flag'i `sell_inventory_order` alanına gider; eski `sell_all_inventory` izni
olarak kullanılmaz. Profil değişikliği yeni denemede alınır, çalışma anındaki
VCL olayları otomatik emüle edilmez. Kullanıcı tarafından başlatılan yerel
deneme, start checkbox'ının oyunda otomatik çalıştığı anlamına gelmez.

Satış listesi/çanta gözlemleri scalar bağdan ayrıdır. Sonradan varsayılan kapalı
liste hazırlama/setup seçeneği eklendi; [SELL_MERCHANT_PREPARATION.md](SELL_MERCHANT_PREPARATION.md).
Bu mod prepared kayıtları typed seçim API'sine verir ve eksik taze envanterde
bekler. Manuel rota Text eksikliği ve para parser gap'i config metadata'da
korunur; henüz uygulanmamış alarm/rota davranışları tüketilmiş sayılmaz.

Tam birim çalıştırmasında1796test geçti (8.459s). 12 yeni test gerçek profil varsayılanlarını, start kısa devresini, radyo yazma
önceliğini, canonical sıra alanını, raw DWORD/QWORD dönüşümlerini, dot kuralını,
Text/ItemIndex ayrımını ve desteklenmeyen süre reddini kapsar.
`work/verify_sell_merchant_panel_ui.py`, kendi gizli Tk arayüzünde91000ms
kapısını, reset sonrası ayarları ve64bit para değerini doğrular. Önceki BUY panel
testi de yeniden geçti. Genel gizli `smoke_ui.py`1037kontrol/11form/18sekme ve
mevcut davranış kontrolleriyle tamamlandı. Canlı oyun uyumluluğu ve native
alarm/rota etkileri açık.
