# Pet ayarları ve çalışma akışı

Bu aşama Pet bölümüne ait iki yerel API ekler. `pet_settings.py`, ortak ayar
üreticisinin `0040a3ac..0040a4ad` aralığını; `pet_engine.py`, `0040fc1c`
yordamının gözlenen normal yollarını planlar. Planlanan çağrılar veya alan
yazımları oyunda uygulanmaz. Sonraki Pet panel aşaması altı gerçek kontrolü
bu API'lere bağlar; güncel bağ `PET_PANEL.md` içinde açıklanır. Otomatik oyun
gözlem sağlayıcısı bağlı değildir. Bu belgenin ilk API aşaması kaydı
`PET_BEHAVIOR_VALIDATION.json` tarihsel kapsamı korur.

## Ayarlar

| Kontrol | Bağlam alanı | Kaynak davranışı |
| --- | --- | --- |
| Otomatik Pet Çıkart | `+1a8` BYTE | Getter AL değeri |
| Saldırı / Guard / Loot | `+1ac` DWORD | Öncelik sırasıyla 1 / 2 / 3; hiçbiri seçili değilse yazım yok |
| Pet'i Otomatik Besle | `+1b0` BYTE | Getter AL değeri |
| Besleme metni | `+1b4` DWORD | Yakalanmış signed64 dönüşümünün alt DWORD'u; catch varsayılanı 10 |

Kaynak burada yüzdeyi 0–100'e sıkıştırmaz. Metin dönüşümü dış RTL'den yakalanan
normal/catch gözlemlerine dayanır; Python'un sayı ayrıştırması kaynak parser'ın
yerine geçirilmez. İç dönüşüm, dış çağrı dönüşü ve geçici metin cleanup'ı
ayrıdır. Son cleanup beklerken daha önce oluşan scalar yazım öneki korunur.
API girişi, üst yordamın SEH kurulumundan sonraki belirli aralıktır; bütün ayar
üreticisinin yürütüldüğü iddia edilmez. Altı event wrapper'ı initialization
byte'ı sıfır değilse ortak üreticiyi çağırır; bu wrapper'lar yalnız statik
olarak incelenmiştir.

## Çalışma yordamı

İlk otomatik çıkarma/besleme bayrakları kapalıysa yordam döner. VIP ve tedarik
yardımcılarının düşük AL sonucu, karakter BYTE alanı ve ayrı float/FPU sonucu
sonraki kapılardır. Float karşılaştırmasının sabiti `0.0`'dır; model değerden
FPU durumu uydurmaz, `FNSTSW AX` gözlemini ister.

Pet yokken otomatik çıkarma bayrağı yeniden okunur. Class dönüşü tam 6 ise
veya gerekli nesne kontrolü başarısızsa ilerlenmez. Aktör ve hedef durumu ayrı
kök/ofset okuma çağrılarıdır. `0040fd31` adresindeki TEST, CF'yi temizlediği
için ardından gelen JC normal yürütmede hedef kontrolünü atlatmaz. Gerekirse
hedef yeniden okunur. Son kapıdan sonra üç bağlam alanı yazılır ve summon
yardımcısı çağrılır; normal dönüş başarılı oyun eylemi anlamına gelmez.

Pet varken güncel mod hedef modla karşılaştırılır. Eşit değilse unsigned
saat farkının 1000 ms olması yeterlidir. Gönderilecek mod tekrar okunur;
yardımcı normal döndükten sonraki taze saat saklanır ve besleme yoluna
girilmez. Eşik altındaki mod beklemesi beslemeyi engellemez.

Besleme kapısı unsigned 5000 ms'dir. Açlık sonucu düşük WORD olarak sıfırla
genişletilir; eşik signed DWORD olarak karşılaştırılır. 14–41 dahil slotlar
sırayla taranır. Üç yiyecek kimliğinden ilk eşleşme kullanılır. Eşik üstünde
olsa veya hiçbir slot eşleşmese de son taze saat `00553c58` alanına yazılır.

## Kanıt ve sınırlar

İki korunmuş Richard sürümünde toplam 648 komut kaydı, form alan kayıtları,
altı published-method kaydı ve GetTickCount import kimliği doğrulandı.
`FarmexBot_Pet_davranis_kod_kaniti.json` girdilerin hash'lerini ve komutları
kaydeder. Yeni bir REA sağlayıcı çağrısı yapılmadı; mevcut Ghidra/PE kanıtları
kullanıldı.

`PetFrame` sadece ulaşılan ham gözlemleri ve True normal dönüşleri tüketir.
Tüketilmiş saat/slot/alan değerleri beklerken değiştirilemez; gelecekteki
okumalar ayrı kalır. Helper gövdeleri, native FPU/VCL/RTL/SEH, exception ve
eşzamanlı değişiklik yolları bu API tarafından yürütülmez. Tam fonksiyon veya
canlı eşlik sertifikası verilmez. Önceki native HP/MP fixture deneyi ayrı bir
kapsamdır; Pet kodunun native yürütülmesi anlamına gelmez.
