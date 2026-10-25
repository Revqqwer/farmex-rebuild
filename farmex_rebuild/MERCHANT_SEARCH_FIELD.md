# Merchant arama kutusu — renk kapısı ve odak olayları

Önceki modelde `search_font_style` diye adlandırılan alan yanlıştı. Pinned VCL `TFont.SetColor` DWORD `+0x18` alanını karşılaştırıp yazar. `GetStyle` ise ayrı `FData+0x21` BYTE alanını okur. İki Richard sürümünde sonuç filtresi `Font+0x18 == 0` koşulunu kullanır. API alanı `search_font_color`, oturum parametresi `search_color` olarak düzeltildi. Siyah renk0 aramayı etkinleştirir; gri sistem rengi `0xff000011` placeholder aramasını atlar. Bu düzeltme DFM stil bitlerinden renk tahmini yapmaz.

`004b1724` Enter, yalnız mevcut Unicode metin placeholder'a tam eşitse metni boşaltır ve ardından rengi siyah yapar. Açık bir sonuç yenilemesi çağırmaz. `004b1808` Exit, yalnız metin tam boşsa placeholder'ı geri yazar, rengi clGrayText yapar, ardından `004bad1c` sonuç yenilemesini çağırır. Boşluklar kırpılmaz, normal metin değiştirilmez. Odak modeli UTF16 birimlerinin tam eşliğini kullanır; native literal dönüşümü veya orijinal managed string ömrü sertifikası değildir.

Gerçek yerel panelde `SetText` Tk değişkenini yazar; senkron OnChange eski rengi görür. Sonraki SetColor rengi değiştirir. Exit son yenilemesi yeni gri renkle placeholder filtresini atlar. Bu sıra önemlidir: yalnız son metin/rengi tek adımda güncellemek ara olayı kaybeder. Widget odak olayları doğrudan modele bağlıdır, gri görünüm için Tk SystemGrayText kullanılır. Kaynak ile piksel/theme eşliği iddia edilmez.

Kendi gizli panel testi gerçek FocusIn/FocusOut ve filtre olaylarını, başlık sırasını, açık arama byte gözlemini, ara SetText dönüşüm çağrısını ve profil sıfırlamayı kontrol eder.304 talimat/import/literal/gate kaydı iki pinned Richard sürümü ve VCL setter'ıyla diskten doğrulandı (`FarmexBot_merchant_arama_renk_kaniti.json`). DFM placeholder literal'i Türkçe1254 çözümlemede eşleşir; bu tek başına oyunun/runtime'ın gerçek kod sayfası kanıtı değildir. Kaynak Unicode/ANSI büyük harf dönüşümü, başlangıç kapısı ve tüm VCL/SEH davranışı hâlâ açıktır.

REA `analyze_function(0x004b1724)` isteği bu aşamada provider_timeout330000ms sonucuyla bitti. Yeni başarılı REA analizi sayılmadı; statik disk kanıtı ve kendi GUI yürütümü ayrı tutulur.
