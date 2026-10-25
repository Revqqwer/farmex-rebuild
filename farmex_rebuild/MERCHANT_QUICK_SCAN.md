# Tek tarama — dört cached ID veri modeli

`merchant_quick_scan.py`, `004bfc5c` yordamındaki sabit gözlem değerlerini modeller. Başlangıç lookup aralığı1..5000 dahildir; eksik mapping girdisi boş lookup sayılmaz. Kaynak dört cached item ID'si okur;12-slot yanıt decoder'ı bu akış yerine kullanılmaz.

Sonuç vektörü ve liste temizliği source intent olarak kaydedilir; gerçek UI/native yardımcı çalıştırılmaz. Actor pointer0 veya active getter'ının AL=0 olması o actor'ın sonraki alanlarını atlar. Geçerli actor'da alış/satış byte'ı iki kez, ayrı gözlemlerle okunur. İlk AL=0 ise yerel bayrak0, ikinci AL=1 ise1 yazılır; diğer durumlarda önceki byte korunur. Gövdede başka doğrudan bayrak ataması görülmedi. İlk stack byte'ı bilinmiyorsa0/1 uydurulmaz; gerektiğinde açık gözlem istenir. Bayrağın değeri sonraki actor'a taşınabilir.

Entity ID getter sonucu satıra kullanılmasa da kaynak tarafından okunur; model bunu atlamaz. X/Y açık `_ftol` EAX DWORD'larıdır; Python float/rounding kullanılmaz. Satıcı adı explicit ANSI copy helper çıktısıdır. WORD slot tabanı +4 adımlarında16-bit taşar; her adres actor pointer'a bundan sonra eklenir. Dört ID'nin tamamı ilk metadata lookup'tan önce okunur.

Item adının base kaynağı kategori0/2/5/11 için lookup, diğerleri için extension ailesidir. Kategori2/5/11'e `(+extension_id%10)`,11/12'ye ` (Reverse)` eklenir. Kategori1 için normal yanıt yolundaki suffix kuralı kopyalanmaz. Base ANSI byte'ları açık copy çıktısıdır; yeniden encode edilmez. Kaydedilen kategori taze ve ayrı gözlemdir. Miktar, alternatif miktar, fiyat ve son bayrak bu akışta0 yazılır. Mesafe veya scan SELL/BUY ayar filtresi bu gövdede varsayılmaz; son source `004bad1c` rebuild'i kendi view filtresini ayrı uygular.

Model, sonradan bir veri boşluğunda önceki record önekini korur. Tüm5000 lookup tamamlanmadan final rebuild intenti üretmez. Dönen `complete`, yalnız own veri projeksiyonunun girdilerinin tamamlandığını anlatır; source lookup/copy/codec/append veya final VCL helper'ının normal döndüğünü kanıtlamaz. Tek çağrılık modeldir, native resumable frame değildir.

İki Richard sürümündeki1998-instruction gövde ve12-instruction düğme callback'i dahil4020 kayıt disk byte'larıyla karşılaştırıldı. Seçili döngü sınırları, bayrak store'ları, dört metadata kategori dalı, suffix literal'leri, miktar/fiyat sıfırları ve ftol importları ayrıca sabitlendi. Tam instruction byte uyumu bütün1998 instruction'ın davranış eşliğini kanıtlamaz.

İlk API aşamasında14 yeni testle toplam4344 Python testi geçti. Sonraki tablo/düğme aşamasında toplam4352 test ve tam GUI1037 kontrol/11form/18sekme geçti. Gerçek Tara düğmesi açık immutable snapshot ve kod sayfasıyla bu modeli tüketir; otomatik oyun metadata/veri sağlayıcısı hâlâ bağlı değildir. Model yeni pakete dahil edilir. Güncel kapsam MERCHANT_QUICK_TABLE_VALIDATION.json, ilk API aşaması tarihsel olarak MERCHANT_QUICK_SCAN_VALIDATION.json içindedir.
