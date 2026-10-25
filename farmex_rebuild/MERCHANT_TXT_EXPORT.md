# Yerel TXT dosya controller'ı ve Kaydet düğmesi

Gerçek Kaydet düğmesi `merchant_txt_export.py` controller'ını çağırır. Controller mevcut filtrelenmiş ve sıralanmış tabloyu, kaynak başlık/satır biçimiyle kendi dosyasına yazar. Kimlik byte'ları, dokuz localtime DWORD'u, çıktı klasörü ve metin/dosya yolu kod sayfaları açık `OwnedExportContext` girdileridir. Otomatik oyun bağlamı sağlayıcısı varsayılan olarak yoktur. Eksik bağlamda dosya oluşturulmaz ve panel bunu belirtir.

Kodlama yerel Windows flags0 politikasıdır; oyunun DefaultSystemCodePage değeri veya kaynak managed dönüşümlerinin eşliği sayılmaz. Metin kod sayfası ile dosya yolu kod sayfası ayrıdır. Bağlam sağlayıcısı her Kaydet basışında yeniden çağrılır. Ekrandaki tablo satırları beklenen snapshot ile uyuşmazsa sağlayıcıya veya dosyaya geçilmez. Profil yüklenince sağlayıcı ve son sonuç temizlenir; yalnız paneli yeniden çizmek sağlayıcıyı korur.

Başlık mevcut view/kategori/arama metninden kurulur; arama placeholder'ı kaynak gibi başlığa dahil edilir. Dosya adı açık identity ANSI byte'ları ve kaynak zaman ifadesiyle kurulur: ay ham/sıfır tabanlıdır, sayı dolgusu yoktur. Path `_Fiopen` C-string sınırı gibi ilk NUL'da kesilir; dosya yolu açık Windows kod sayfasıyla çözümlenir. Kendi writer'ı yalnız yapılandırılan çıktı klasörünün altında yazar ve eksik klasör oluşturmaz. Bu klasör sınırı kaynakta kanıtlanmış bir sanitize davranışı değildir; kendi uygulamanın açık farkıdır.

Dosya binary `wb` ile açılır; mevcut dosya kesilir. Önceden doğrulanan CRT metin çevirisi uygulandığından her LF→CRLF olur ve ayrıca text-mode dönüşümü yaptırılmaz. Otomatik BOM eklenmez. Header yazıldıktan sonra her satır fiyat/adet/item/satıcı sırasıyla kodlanır; çıktı kendi sıra sayacıyla numaralanır. Orijinal record_index veya gizli koordinat/PM/GİT değerleri dosyaya eklenmez.

Satır dönüşümü ya da yazma sonradan başarısız olursa dosyanın yazılmış öneki korunur. Kısa write ve close hatası incomplete sonuç verir; başarı yalnız bütün kendi yazma ve close adımları normal bitince bildirilir. `bytes_written`, own writer'ın kabul ettiği byte toplamıdır; close hatasında fiziksel kalıcılık garantisi değildir. Kaynak C++ stream width/fill/locale facet'leri, failure/exception ve managed lifetime davranışı ayrıca çözülmelidir.

Bu controller source `004b99f8` yordamını veya kaynak native yardımcılarını çalıştırmaz. Standart CRT'deki32 dosya ve15 zaman referansı daha önce ayrı fixture'larla ölçülmüştür. Gerçek oyun kimliği, saat dilimi/global kod sayfası ve orijinal botun ürettiği dosyayla karşılaştırma bu aşamada kanıtlanmış değildir.

Doğrulama kapsamı `MERCHANT_TXT_EXPORT_VALIDATION.json` ve `FarmexBot_merchant_TXT_yerel_arayuz_kaniti.json` ile kaydedilir. Kaydet düğmesi kendi açık fixture bağlamıyla gerçek geçici dosya yazan UI testine bağlıdır; bu fixture gerçek oyun bağlamı olarak sunulmaz.
