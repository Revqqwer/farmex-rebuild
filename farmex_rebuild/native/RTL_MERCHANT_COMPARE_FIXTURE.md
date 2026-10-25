# Kendi x86 standart RTL karşılaştırma fixture'ı

`build_rtl_merchant_compare_fixture.ps1`, pinlenmiş TinyCC ile `rtl_merchant_compare_fixture.c` dosyasını derler. Ortak immutable Delphi UnicodeString hazırlığı `rtl_integer_fixture.c` içinden kullanılır. Derlenmiş exe çalışma dizininde tutulur; kaynak ZIP'e eklenmez.

CLI argümanları: mutlak standart RTL dosyası, `compare`/`ansi`/`int`, birinci UTF16 little-endian hex, ikinci UTF16 hex. `-` explicit nil'dir; boş argüman nonnull boş string'dir. Yalnız kendi süreç belleği kullanılır; external PID/handle/socket veya bot modülü parametresi yoktur.

Modül path eşleşmesi kontrol edilir, Initialize export'u çağrılır, EAX/EDX register ABI'si kullanılır ve normal dönüş ESP'si kaydedilir. İlk-exception gözlemcisi yalnız bu kendi süreci kapatır; EIP değiştirmez, istisnayı devam ettirmez ve bot unwind yapmaz. Header refcount=-1; UTF16 byte'ları ve uzunluk açıkça hazırlanır. Girdi4000UTF16 birimiyle sınırlıdır.

Fixture SHA256: `ac315613b9c272d9833e0596cbcb3e854581805d395f66cd9ce8298bd31858a9`. RTL SHA256: `7d98acb8fade7f0920c0f544eaf5525afaf8c8c1afb82e77544cf29ac75eddd8`. Üst çalışma dizinindeki `check_rtl_merchant_compare_native.py`77 vakayı ve `check_rtl_text_compare_models.py` mevcut native trace ile50 model karşılaştırmasını kaydeder. Sonuçların kapsamı ve ilk konsol encoding hatasının düzeltilmesi `RTL_TEXT_COMPARE.md` içinde açıklanır.
