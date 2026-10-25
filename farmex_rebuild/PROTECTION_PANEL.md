# Ortak Koruma paneli ve yerel alan durumu

**Koruma Ayarları** denemesi, ortak0046b928 üreticisindeki50 kaynak üyesini gerçek own panel alanlarına bağlar. AntiCR, karşı ırk, bildirim, PM ve TP seçenekleri aynı kaynak sırasıyla ilerler. Bu bağlantı tüketici işçilerin eylemlerini veya native oyun ayarını uygulamaz.

`protection_fields.json`, byte doğrulaması yapılmış50 form üyesi/slot/path eşlemesinin kendi metadata projeksiyonudur. Özgün executable içermez. Checkbox/radio getter değerleri own bool panelden0/1 olarak gelir; alt seviye kaynak modeli hamAL değerlerini ayrıca destekler. Sayı metinleri profile değerinden alınır. Dört rota kutusunda profil indeksi yerine `ConfigurationPanel.combo_texts()` üzerinden gerçek görünen Text kullanılır. Dinamik rota listeleri bu sayede doğru metni üretir; indeks0, metin"0" gibi yorumlanmaz.

## Gözlemler ve örnek

Boş JSON kaynak girişinde bekler. Prologue/VCL/string normal dönüşleri, numeric helper çocukları ve dış parser normal dönüşleri ayrı alanlardır. Panel getter'ları ve Text değerleri çelişkili JSON ile değiştirilemez. Sayısal çocuklar yalnız ulaşılan iç aşamanın gözlemini tüketir; native parser veya catch yolu kendiliğinden tahmin edilmez. ANSI byte sonuçları açıkHEX gözlemidir.

**Panelden sentetik derleme örneği** düğmesi iki açık kendi politikası kullanır: signed-decimal64 sayı alt kümesi ve seçilmiş rota kod sayfasında yerel Windows dönüşümü. Desteklenmeyen sayı metninden native fallback/istisna tahmini yapmaz; örneği üretmeyi reddeder. Kaynak helper'ın catch-landing gözlemi kullanıcı/fixture tarafından açıkça verildiğinde model fallback'i destekler. Yerel Windows dönüşümünün used-default bilgisi JSON'da korunur; bunun kaynak RTL/oyun codepage'iyle eşdeğerliği kanıtlanmadı.

Snapshot;50 alanın değeri, rota Text'leri ve seçilmiş kod sayfasını kapsar. Panel/rota/codepage değişirse eski örnek reddedilir. Aynı giriş gözlem boşluklarında devam eder; tamamlanmış frame tekrar uygulanmaz. **Sıfırla**, kendi deneme durumunu bilinmeyen başlangıca getirir; panel tercihlerini değiştirmez.

## Önceki alanların korunması

Her normal kaynak store'u kendi `scalar_state` sözlüğüne, her mantıksal string ataması `string_state` sözlüğüne bir kez yansıtılır. Bunlar oyun belleği değildir. Cleanup beklerken önceki store/atamalar korunur ve sonradan geri alınmaz. Yeni panel snapshot'ı yeni producer invocation'ı başlatır, önceki yerel alanlar korunur.

Geç bir gözlem hatalıysa (örneğin ANSI HEX), sonuç geçersiz gösterilir ama frame'in daha önce kabul ettiği geçerli önek yerel duruma aktarılır. Deneme katmanındaki bu durum için ayrı regresyon eklendi; hatalı geç veri, yeni checkbox yazımını eski yerel değerin arkasında bırakamaz. JSON çözümlenememişse yeni gözlem tüketilmez.

Özellikle dört işlem radio grubunda hiç eşleşme yoksa yeni store üretilmez. Önceden bilinen değer tutulur; hiç store gözlenmediyse alan bilinmeyen kalır. UI özeti bu ayrımı gösterir. Sıfır değeri uydurulmaz. TP stop-radio else2 kuralı ayrı kalır.

## Doğrulama ve kapsam

On yeni birim testi ve gerçek fakat gizli own Tk arayüz testi;50 kontrol, dinamik Unicode rota Text'i, dört numeric/string gözlemi, kısmi cleanup/hatalı geç veri öneki, no-match sonrası eski enum değerinin tutulması, stale snapshot, tekrar uygulamama ve profil roundtrip'i denetler. Yerel Windows dönüşümü bu testte gerçekten kullanılır; özgün C++/RTL veya oyun yardımcıları çalıştırılmaz.

Scoped compiler kontrol sayısı310→354 oldu; envanter dışındaki düzenlenebilir kontrol sayısı212→168'e indi. Ortak Koruma için önce API-only olarak ayrılan44 alan artık bu UI denemesine bağlıdır. Bunlar özellik tamamlanma yüzdesi değildir. Sınırlı fonksiyon modeli sayısı145 olarak kaldı; mevcut fonksiyonun kaynak/panel kapsamı genişledi.

Mevcut iki REA çıktısı ve iki sabit sürümde1310 instruction kaydı yeniden eşleştirildi. Yeni REA çağrısı yapılmadı. VCL/native nesne kimliği, kaynak RTL eşdeğerliği, SEH/exception etkileri, işçi tüketicileri ve canlı uyumluluk açık kalır. `whole_producer_verified`, native ve live bayraklarıFalse'dır.

Kanıt: `outputs/FarmexBot_koruma_ortak_panel_bagi_kaniti.json`; kaynak akışı: [PROTECTION_SETTINGS.md](PROTECTION_SETTINGS.md).
