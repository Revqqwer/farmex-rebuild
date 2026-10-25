# Merchant yanıtı — yerel sonuç zinciri

`merchant_scan_results.py`, değişmez yanıt byte'larını `merchant_scan_reply_data` ile okur; açık actor/item metadata girdilerini kaynak alanlarına bağlar; mevcut filtre ve sütun modelleriyle yerel sonuç satırları üretir. Bu bağımsız değer zinciri, özgün yordamın metadata çağrıları/record append/inline UI işlemleriyle iç içe yürütümünün emülatörü değildir.

Actor seller metni ve post-conversion X/Y DWORD'ları açık girdilerdir. Oyun lookup'u, float okuyucu veya `__ftol` yerine Python yuvarlaması kullanılmaz. Actor bilinmiyorsa dolu slotun kaydı tamamlanmış sayılmaz. Ham boş slotlarda yeni sonuç kaydı üretilmez.

Item metadata girişi native isim yardımcısının base adını, ad oluşturma anındaki kategori byte'ını, record yazma anında tekrar okunan kategori byte'ını ve extension tablosundan okunan DWORD'u ayrı tutar. İki kategori eşitlenmez. Extension DWORD'un unsigned 10'a bölümünden kalan kullanılır; bu digit ham item ID'nin son hanesi varsayılmaz.

Ad kategorileri 1/2/5/11 için `base(+digit)` son eki eklenir. 11 ve 12 için ayrıca ` (Reverse)` eklenir. Böylece kategori11 `base(+digit) (Reverse)`, kategori12 `base (Reverse)` olur. Kategori0 için upgrade son eki eklenmez. Kaynak concat çağrı zinciri, literal baytları ve LStrCat3 importu pinlenerek denetlendi. Native ANSI/Unicode, string heap ve isim yardımcısının iç davranışı hâlâ açıktır.

Record eşlemesinde price ham DWORD, iki slot WORD'u sıfır genişletilmiş +0x20/+0x24 alanları, ikinci kategori okuması +0x1c, remainder byte +0x1d ve son byte sıfırdır. Item ID ve slot index kendi provenance kaydında korunur. Önceki kayıtlar sırayla tutulur; kaynaksız deduplication eklenmez. Eksik metadata tamamlanan record önekini korur. Arama için normalize isim yoksa da önceden tamamlanan record eklemesi geri alınmaz.

Yanıt yordamı satırları inline ekler; filtre seçiminin tam listeyi yeniden oluşturmasıyla aynı olay değildir. Bu nedenle `build_merchant_result_rows(..., finalize_rebuild=False)` kullanılır: clear, sort-column reseti ve AlphaSort istekleri üretilmez. Önceki tam rebuild API'sinin varsayılan davranışı korunur. Yerel önizleme mevcut kayıtların sabit görüntüsünden hesaplanır; native taze kontrol okumaları ve gerçek GUI mutation sırası doğrulanmaz.

10 yeni test ve toplam 4141 test geçti (`work/merchant_scan_results_full_tests.log`). Ham yanıt→metadata→ad→filtre→sütun zinciri, bağımsız kategori okumaları, eksik metadata/arama önekleri, duplicate kayıtlar ve rebuild etkilerinin eklenmemesi kontrol edildi. İki Richard sürümünde 4284 talimat kaydı, alan operandları ve concat import zinciri denetlendi (`FarmexBot_merchant_yanit_sonuc_bagi_kaniti.json`). Yeni başarılı REA analizi yok; mevcut Ghidra ihracatı kullanıldı.

`.complete` yalnız bu yerel değer zincirinin ulaşılan kapsamını belirtir. Native parse/finish normal dönüş makbuzları, genel istisna yolları, devam ettirilebilir native frame veya gerçek sıralama sertifikası üretmez. Kısmi öneği önceki kayıt olarak verip aynı payload'ı baştan oynatmak otomatik resume değildir; kaynakta olmayan idempotans iddia edilmez. Gerçek actor/item lookup, native dönüşümler, panel oturumu ve PM/GİT eylemleri tamamlanmadı.
