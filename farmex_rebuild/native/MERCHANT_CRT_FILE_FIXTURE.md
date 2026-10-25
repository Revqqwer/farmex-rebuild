# Kendi CRT dosya fixture'ı

`merchant_crt_file_fixture.c` kendi x86 sürecinde sabit kimlikli standart CC32260MT kütüphanesini yükler; `_Fiopen`, `_fwrite` ve `_fclose` export'larını çağırır. Bot modülü veya oyun yüklenmez, başka sürece erişilmez. Çıktı adı basename ile sınırlıdır ve dosya yalnız fixture EXE'sinin bulunduğu klasöre yazılır.

Derleme `build_merchant_crt_file_fixture.ps1` ile SHA256'sı sabitlenmiş TinyCC kullanır. Checker `work/check_merchant_crt_file_native.py` her dosyaya kendi uzun ön verisini koyar, mod2 veya130 ile fixture'ı çağırır ve dosya byte'larını karşılaştırır. Metin modunda her LF CRLF olur; binary modunda byte'lar aynıdır. Her iki mod mevcut kendi dosyasının kalan kuyruğunu siler. Fixture hex girdisini açık byte uzunluğuyla fwrite'a verir; C-string NUL kesilmesi ayrıca source ostream helper'ının semantiğidir ve bu fixture'ın yaptığı işlem değildir.

32 sonlu normal örnek geçti. Host ACP1254 bilgisi raporlandı; fixture herhangi bir Unicode→ANSI dönüşümü yapmaz. C++ ostream buffer/width/fill/locale facet'leri, write/close hataları, izin/yol hataları, disk dolması ve kaynak exception zinciri bu sonuçla kanıtlanmış değildir.

Kanıt `outputs/FarmexBot_merchant_CRT_dosya_native_kaniti.json` içinde CRT/fixture/kaynak SHA256'ları, girdi/çıktı byte'ları ve her çağrının normal dönüş değerleriyle tutulur. Özgün çıktı dosyasıyla karşılaştırma veya canlı uyumluluk sertifikası değildir.
