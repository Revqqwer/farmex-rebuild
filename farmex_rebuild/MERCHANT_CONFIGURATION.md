# Alış pazarı panel ayarları

SELL scalar alanları da sonradan eklendi: [SELL_MERCHANT_CONFIGURATION.md](SELL_MERCHANT_CONFIGURATION.md).
Genişletilmiş audit aynı1128talimat için24published kontrolü doğrular ve güncel
`FarmexBot_pazar_panel_ayar_kod_kaniti.json` raporunu üretir. Aşağıdaki12alanlı
BUY raporu önceki scoped kayıttır; sayılar birbirine eklenmez.

18 Ekim 2026: `merchant_configuration.py`, ortak `0041fea4` panel okuyucusunun
BUY alanlarını kendi profilimizdeki açık değerlerden derler. İki sürümde
okuyucu/sayı yardımcısı/9 olay gövdesinden toplam1128 talimat kaydı ve12 published
kontrol kaydı dosyadan doğrulandı. Audit: `work/audit_merchant_configuration.py`;
rapor: `outputs/FarmexBot_alis_panel_ayar_kod_kaniti.json`. Ghidra ve Delphi tablo
kanıtıdır; REA Evidence nesnesi veya native olay yürütme sonucu değildir.

| Profil girdisi | Kaynak nesne alanı | Davranış |
| --- | --- | --- |
| SELL start, sonra gerekirse BUY start | DWORD+00 | SELL checked ise1; değilse BUY checked ise2; ikisi de kapalıysa0 |
| ReMerchant checked | BYTE+110 | Açık bool örneğinin0/1 izdüşümü |
| ReMerchant dakika Text | DWORD+114 | Sayı yardımcısının düşük DWORD'u |
| ExtraWait Text | DWORD+118 | Sayı yardımcısının düşük DWORD'u |
| Stop, DC, Bank radio | DWORD+11c | Ayrı IF'ler sırasıyla0/1/2 yazar; son checked kazanır |
| Inventory limit Text | DWORD+120 | Sayı yardımcısının düşük DWORD'u |
| Alarm checked | BYTE+124 | Derlenen alan; gerçek alarm değildir |
| Manuel rota checked | BYTE+125 | Derlenen alan; rota yüklenmez |
| Manuel rota combo | Ayrı Unicode Text | ItemIndex'ten uydurulmaz; açık Text gözlemi gerekir |

Hiçbir politika radyosu checked değilse kaynak önceki DWORD'u korur. Açık
`initial_policy_dword` olmadan derleme bu alanı eksik bırakır; runner köprüsü
otomatik stop varsaymaz. Start okuması da kısa devrelidir: SELL true olduğunda
BUY start değerinin varlığı gerekmez. Bu yapı, profil bool'larının bozuk/karışık
durumunda VCL'nin radyo gruplarını nasıl güncelleyeceğini emüle etmez.

Yerel sayı dönüştürme politikası signed64 aralığındaki ASCII ondalık metindir;
düşük DWORD alınır. Native parser'ın tüm biçimleri ve hata/exception/fallback
davranışı doğrulanmadı. `numeric_results` ile o kontrol için açık EDX:EAX QWORD
gözlemi verilebilir. Geçersiz metin otomatik varsayılan değere çevrilmez. Derleme
ham DWORD'ları korur; mevcut runner'ın hâlâ normal saat kullanan setup alanları
desteklenen sınırın dışındaysa settings köprüsü reddeder, clamp yapmaz.

EnginePage `Buy Merchant` panel seçeneği açıkken başlangıçta yeniden kurma,
dakika, ek bekleme, boş yuva eşiği ve hata politikasını bu derlemeden alır.
Önceki manuel threshold alanı bu yolda okunmaz. Asıl ListView hazırlama modeli
aynı profilin satırlarını ayrıca tüketir; unchecked BUY satırları da kaynak
normal yolundaki gibi hazırlanır. Liste mutasyon/ekle/sil düğmeleri bu scalar
derleyicinin kapsamında değildir.

Varsayılan profil ek bekleme30, yeniden kurma dakika20, limit0 ve politika
stop verir. Gizli own-UI kontrolünde hazırlık kapısı yerel normal saat modelinde
91000ms'de açıldı. Profildeki scalar değişiklikler yeni denemede alınır; native
OnClick/OnChange güncellemeleri çalışma sırasında otomatik emüle edilmez.
Start modu derlense de örnek sayfası kullanıcı tarafından başlatılan denemedir;
oyunda otomatik start yoktur. Alarm ve manuel rota bayrakları henüz gerçek
consumer'a bağlanmadı. Banka rotasının Text/ANSI/başlatma etkileri açık kalır.

11 yeni birim testi gerçek katalog varsayılanlarını, kısa devreyi, radyo yazma
önceliğini, önceki state eksikliğini, düşük DWORD dönüşümünü, ham helper
gözlemini, combo Text ayrımını ve aralık reddini kapsar. Tam birim çalıştırması
1768 test ile geçti (8.479 saniye). `work/verify_merchant_panel_ui.py` kendi
gizli Tk arayüzünde panel→settings→hazırlık→açma akışını ve reset sonrası yeni
ayarları doğrular. Güncellenmiş genel gizli `smoke_ui.py` kontrolü de1037kontrol,
11form/18sekme ve mevcut davranış kontrolleriyle geçti; panelden gelen30s ek
bekleme bu kontrolde de kullanıldı. Canlı oyun uyumluluğu veya tüm ortak okuyucunun SELL/native
etkileri bu sonuçlarla kanıtlanmaz.
