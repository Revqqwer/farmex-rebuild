# Merchant TXT biçimi — bağımsız skaler API

`merchant_txt_format.py`, kaynak `004b99f8` içindeki normal başlık ve satır birleştirmesini modeller. Bu skaler modül dosya açmaz; gerçek Kaydet düğmesinin `merchant_txt_export.py` controller'ı tarafından tüketilir. Önceki `plan_vendor_txt_export` placeholder'ı ayrı tarihsel API olarak kalır.

Başlık, mevcut üç kontrol metninden kurulur:

    view + " - " + category + " - Filtre : " + search + " \n"

Arama placeholder'ı veya gri renk özel olarak elenmez. Kaynak kontrol okuma sırası arama, kategori, view'dır; son ifade ters operand stack sırasından gelir. Başlık Unicode olarak kurulur, daha sonra kaynak codepage0 ANSI dönüşümünden geçer. Bu API ANSI başlık dönüşümünü açık byte girdisi olarak ister; UTF-8 veya kaynak çalışma zamanının varsayılan kod sayfası tahmin edilmez.

Kaynak satırın son düzeni sıra numarası, satıcı, item, adet ve fiyattır. Etiketler özgün dar literal byte'larıyla korunur: satıcı etiketindeki `FD` byte'ları Unicode üzerinden yeniden kodlanmaz. Alan gözlem sırası fiyat→adet→item→satıcıdır. `index+1` işaretli DWORD `%i` biçimidir. Ekrandaki ListView satırları kullanılır; ham kaydın PM/GİT/koordinat sütunları bu ifadeye eklenmez. Sıralama ve filtreleme dışa aktarılan satır snapshot'ını belirler; bu API ayrıca sıralamaz veya filtrelemez.

`MerchantTxtAnsiRow` alanları, kaynağın Unicode→ANSI dönüşümünden sonraki açık byte gözlemleridir. Normal birleştirme eşit/uyumlu encoding altında skaler byte izdüşümüdür; farklı kod sayfalı AnsiString tag'leri, native dönüştürme ve managed lifetime eşliği kanıtlanmaz. Eksik alan sonraki satırların okunmasını durdurur; önceki header/satır insertion parçaları korunur.

Stream insertion `char_traits<char>::length` kullandığından her parça ilk NUL'da kesilir. Sonraki parça ayrı işlenir. Model, bu normal C-string insertion parçalarına standart CRT'nin gözlenen metin çevirisini uygular: her LF→CRLF, mevcut CR korunur. Böylece zaten CRLF içeren bir parça CRCRLF olur. Otomatik BOM eklenmez.

Dosya yolu kendi base byte'ları ve iki kaynak yardımcı çıktısından birleştirilir. Yardımcı çıktıları açık girdidir; Python zamanı veya uydurulmuş karakter adı kullanılmaz. Exact timestamp/kimlik helper semantiği, native stream width/fill/locale, open/write/close hata yolları ve GUI export henüz açık.

Kaynak kanıtı `FarmexBot_merchant_TXT_bicim_kod_kaniti.json` içindedir: iki Richard sürümünün ana gövdesi ve ilgili yardımcıları, codec/CRT import zincirleri, dar literal'ler ve source getter indeksleri disk byte'larıyla doğrulandı. CC32260MT `_Fiopen` mod2 tablo girdisi `w` olarak sabitlendi.

Kendi x86 CRT fixture'ı 16 metin ve 16 binary dosya örneğinde çıktı byte'larını karşılaştırdı:32 örnek,0 fark. LF/CRLF, NUL, 0x1A, bütün byte değerleri, mevcut dosyanın kesilmesi ve BOM eklenmemesi gözlendi. Fixture kaynak C++ ostream'i veya botu çalıştırmaz. Kapsam `native/MERCHANT_CRT_FILE_FIXTURE.md` ve `FarmexBot_merchant_CRT_dosya_native_kaniti.json` içindedir.

İlk API aşamasında9 yeni testle toplam4305 Python testi geçti. Sonraki controller/UI aşamasında toplam4330 test ve tam GUI1037 kontrol/11form/18sekme geçti; format API'si yeni pakete dahil edilir. Güncel kapsam MERCHANT_TXT_EXPORT_VALIDATION.json içindedir. Otomatik oyun bağlamı ve source native stream eşliği hâlâ açık olduğundan tam TXT/oyun uyumluluğu sertifikası değildir.
