# Alış listesi hazırlama zinciri

`merchant_preparation.py`, `0041dec8` normal yolunu kendi değişmez kayıt vektörü üzerinde yeniden kurar. Bu saf plan VCL, yerel heap, exception handler veya oyun işlemi çalıştırmaz. Başlangıç/kısmi/tamamlanmış durumları birbirinden ayırır; eksik bir gözlem başarı, boş liste veya sıfır sayı olarak kabul edilmez.

## Okuma ve kayıt düzeni

Kaynak kontrol `frmMain/MainTab/sheetBuyMerchant/GroupBox55/LwAutoBuyMerchant`, form alanı `+0xcd4` olarak doğrulandı. Önce mevcut vektörün end/begin/range-erase normal dönüşü gerekir. Modelin kendi vektörü bu aşamadan sonra boşalır; gerçek heap silinmez.

Her döngüde ayrı signed `TListItems.GetCount` sonucu alınır. Sayı indeksten büyükse ilgili satır şu sırayla hazırlanır:

1. `0045f7f4`, TListItem `+0x20` caption alanını getirir. `0045ef80`, default argümanı 0 ile StrToInt64 yolunu çağırır. Caller yalnız EAX'ı item DWORD'una saklar; ardından Unicode geçicisinin temizliği gerekir.
2. `0045f6e0` ile **alt sütun indeksi 1** alınır. Aynı sayısal yardımcıdan dönen EAX adet DWORD'una saklanır; temizliği beklenir. Alt sütun 0 bu yolda okunmaz.
3. **Alt sütun indeksi 2** fiyat metnidir. Unicode→ANSI dönüşümünün normal dönüşü ve gerçek dönüştürülmüş byte'lar gözlemdir. Fiyat helper'ının EDX:EAX sonucu iki DWORD halinde saklanır: fiyat 64 bittir.
4. Fiyatın ANSI ve Unicode geçicilerinin iki ayrı temizliği tamamlandıktan sonra size/capacity sonuçları unsigned karşılaştırılır. Size < capacity, `0041dd9c` yerinde append; diğer yol end→`0041ddfc` büyüterek append planıdır. Normal append dönüşünden sonra kendi vektörümüze 16 baytlık mantıksal kayıt eklenir.

Kayıt `(item DWORD, quantity DWORD, price QWORD)` biçimindedir. Kaynak bu hazırlayıcıda Checked sorgulamaz; bütün ulaşılan satırlar değerlendirilir. Item adı gibi diğer alt sütunlar dönüşüme katılmaz.

## Fiyatın özel dönüşümü

`0045edfc` yalnız ASCII rakamlar ve nokta byte'larını kabul eder. Bir başka byte görülürse `00460fa4` EAX ve EDX'yi sıfırlar: bilinen sonuç QWORD 0'dır; sayısal parser bu dalda çağrılmaz.

Geçerli byte'larda uzunluk 0..3 ise metin değişmeden StrToInt64 yoluna gider. Uzunluk en az 4 ise bütün noktalar atılarak yeni metin oluşturulur ve o metin çevrilir. Dolayısıyla `1.2` ile `1.23` aynı yoldan geçmez: ilkinde parser `1.2`, ikincisinde `123` görür. `1.000` → `1000` olur. Nokta yerleşimi için ayrıca binlik gruplama denetimi eklenmedi.

Boş metin veya yalnız nokta predicate'i geçebilir; bu, StrToInt64'ün normal döneceğini kanıtlamaz. Model bu durumlarda sıfır uydurmaz. `local_decimal=True`, yalnız ASCII decimal signed64 alt kümesini hesaplayan açık bir yerel politikadır; Delphi'nin bütün sayı biçimleri, default/fallback ve exception davranışları değildir. Alternatif olarak gözlenen raw QWORD dönüşü sağlanabilir. İki parser kaynağı aynı ulaşılan yerde birlikte kullanılamaz.

## Eksik gözlem ve bağlama

`replay_buy_preparation(state, observation)` tam normal yolda yeni `state` döndürür. Eksikte giriş durumu `state` olarak kalır, bilinen temizleme/append prefix'i `prospective_state` içinde görünür; son satırın bilinen alanları `partial_fields` içindedir. Bu model politikası gerçek native kısmi etkilerin geri alındığı iddiası değildir. Native pointer/kapasite geçerliliği, allocator sonuçları, diğer thread'lerin mutasyonları ve exception unwinding eşdeğerliği doğrulanmış değildir.

`BuySetupObservation.preparation_inputs` bu plana bağlanır. Hazırlık tamamlanmadan çanta veya coin helper planına geçilmez. Tamamlandığında fiyat QWORD'u hazırlık planında korunur; mevcut `00420740` bütçe hesabı için fiyatın düşük DWORD'u alınır. Hazır satırlar veya normal helper-return marker'ı ile bağlı hazırlık aynı anda verilemez. Hazırlık sonrası vektörün sabit kaldığı hâlâ açık `stable_rows=True` varsayımıdır; alternatif taze count gözlemleri önceki API'de bulunur.

## Arayüz örneği

“Buy Merchant” örneği açıkken genel panel seçeneği de açıksa bağlı alış ListView satırları kullanılır. Panel seçeneği kapalıyken tek deneme satırının metinleri kullanılır. Eski doğrudan hazırlanmış satır üretimi kaldırıldı. Liste temizliği, string/append dönüşleri, kapasite ve fresh-count örnekleri kendi UI snapshot'ımıza aittir. ASCII dışı fiyat için otomatik kod sayfası varsayılmaz; dönüştürülmüş ANSI gözlemi eksik kalır. Örnek seçeneği varsayılan kapalıdır.

Kaynak kanıtı `work/audit_merchant_preparation.py` ile üretildi: eski/güncel iki dosyada 11 gövdenin **1452 talimat kaydı**, alan yazımları, fiyat koşulları, kabul edilen byte kümesi, ortak StrToInt64 import kimliği ve published ListView kaydı doğrulandı. Kayıt üst çıktı dizinindeki `FarmexBot_alis_listesi_hazirlama_kod_kaniti.json` dosyasındadır. Ghidra kayıtları REA Evidence veya canlı çalışma izi değildir.

On yeni test dahil 1699 birim testi geçti (6.131 s). Genişletilmiş gizli UI testi; panelde Checked=False satırın dahil edilmesini, item düşük DWORD/fiyat tam QWORD ayrımını, bütçeye düşük DWORD aktarımını ve kısa noktalı fiyatın eksik dönüş olarak beklemesini doğruladı.1037kontrol/11form/18ana sekme regresyonu da geçti. Bu Python/UI adımında native testler tekrar çalıştırılmadı.

Gerçek oyun çantası, coin, panel runtime'ı, yerel string/allocator/ABI, alış pazarı açma/aktarım ve sunucu sonucu bu doğrulamayla tamamlanmış sayılmaz.
