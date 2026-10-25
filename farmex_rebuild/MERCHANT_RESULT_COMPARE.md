# Merchant sonuç karşılaştırması

`merchant_result_compare.py`, `004b94d4` callback yardımcısının normal sonuç projeksiyonunu ve `00460fa4` fiyat ayrıştırıcısının kendi byte/sayı modelini sağlar. Arayüz sıralama motoru değildir.

Sütun 0 `CompareText`, sütun 1 `AnsiCompareText` kullanır; bu iki native karşılaştırmanın EAX sonuçları ayrı açık gözlemlerdir. Python casefold veya alfabetik sıralama ile doldurulmazlar. Sütun 2 önce birinci, sonra ikinci adet için `StrToInt` çağırır. İki normal EAX dönüşü açıkça sağlanmadıysa sonuç alanı yazılmaz. İstisnada varsayılan adet uydurulmaz.

Sütun 3, iki fiyat metnini ANSI'ye dönüştürüp `00460fa4` ile ayrıştırır. Yerel API yalnız açık ASCII fiyat metnini dönüştürür; diğer Unicode metinde native kod sayfası dönüşümünü ister. `0045edfc` doğrulayıcısı logical ANSI uzunluğu boyunca yalnız 0..9 ve nokta karakterlerine izin verir. Başka karakter varsa fiyat sıfırdır. Embedded NUL da diğer geçersiz karakterler gibi reddedilir; sessizce metin sonuna kırpılmaz.

Doğrulayıcı boş metin ve yalnız noktalara izin verebilir; bu, sayıya dönüşümün başarılı olduğu anlamına gelmez. Üç byte veya daha kısa metin doğrudan sayıya çevrilir. Daha uzunsa bütün noktalar silinir. Bu yüzden `1.0` parse hata yoluna giderken `1.00` sayısal 100 olur. Eksik/geçersiz sayısal sonuç, kendi modelde `needs_native_parser_exception_path` olarak kalır. Genel native exception/unwind eşliği doğrulanmadı. Normal sayı dönüşümünde önceki native scalar karşılaştırmalarla doğrulanan `rtl_integer.py` modeli kullanılır.

Adet ve fiyat karşılaştırmaları `SUB EBX,EAX` ile düşük DWORD üzerinden yapılır. Fiyat ayrıştırıcısının EDX değeri kullanılmaz. Örneğin 4.294.967.295 ile sıfırın karşılaştırma sonucu signed -1'dir; bu normal matematiksel büyüklük karşılaştırması değildir. Bu nedenle Python sayısal sıralamasıyla düzeltilmedi. Böyle bir comparator genel girdilerde tutarlı toplam sıralama sağlamayabilir; VCL'nin gerçek sıralama algoritması ayrıca incelenmelidir.

4 ve sonraki sütunlarda callback sonuç alanını yazmaz. Önceki outparam değeri korunur; sıfır sonucu uydurulmaz. Parser veya dönüştürme eksikliğinde de tamamlanan ilk fiyat gözlemi korunur ve sonuç yazılmış sayılmaz.

Pinned VCL incelemesi: SHA84ea9ebb... dosyasındaki `AlphaSort` önce `HandleAllocated` kontrol eder. Handle yoksa false döner. Varsa kendi `GetHandle` sonucuyla `SendMessageW(hwnd, 0x1030, 0, DefaultCompare)` çağırır; dönüş DWORD'u sıfırdan farklıysa true üretir. `plan_merchant_alpha_sort` bunu yalnız istek ve dönüş planı olarak modeller; mesaj göndermez ve callback adresini çalıştırmaz. Eksik handle/dönüş gözlemi açık kalır. True sonucu gerçek sıra kanıtı değildir.

Aynı VCL'de DefaultCompare sonuç slotunu `PUSH ECX` ile ayırır; event callback öncesinde sıfırlamaz. Callback bu slota yazmazsa eşitlik sıfırı varsayılamaz. Bu statik gözlem, oyunda aynı VCL dosyasının yüklendiğini veya native kontrolün sırasını doğrulamaz. İki VCL gövdesinde 63 talimat diskten çözülüp kritik mesaj/delegate operandları denetlendi: `FarmexBot_merchant_VCL_siralama_kaniti.json`. Native DLL yüklenmedi. Üç yeni AlphaSort plan testi eklendi; bu aşamanın tam test sonucu `MERCHANT_VCL_SORT_VALIDATION.json` içindedir.

11 yeni test ve iki sürümde 1154 bayt-doğrulanmış talimat kaydı bu kapsamı denetler. Kanıt: `FarmexBot_merchant_siralama_kaniti.json`. Yeni başarılı REA analizi yoktur; mevcut Ghidra çıktısı ve pinned importlar kullanıldı. Yerel callback modeli; native metin karşılaştırması, genel `StrToInt`, VCL sıralama yürütümü, sonuç paneli ve hücre tıklama davranışlarının tamamlanması anlamına gelmez. Son doğrulanmış dağıtım ZIP'i değiştirilmedi.
