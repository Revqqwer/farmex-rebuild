# Kendi x86 koordinat float referansı

`build_rtl_coordinate_float_fixture.ps1`, pinned TCC ile `rtl_coordinate_float_fixture.c` aracını derler. Kendi process'inde yalnız pinned standart RTL LoadLibrary/Initialize yapılır. Argümanlar standart RTL absolute path ve UTF16LE hex girdi ya da `--stream`'dir. Stream stdin'den satır başına bir hex string alır; her çağrı aynı own initialized thread üzerinde çalışır.

Register ABI EAX UnicodeString, dönüş x87 ST0; kaynak gibi hemen FSTP32 ile DWORD sonuç bitleri saklanır. Önce/sonra x87 control/status word, stack pointer, ACP ve LCID'ler kaydedilir. Problar standart RTL exception oluşturursa ilk exception observer'ı yalnız kendi process'ini sonlandırır. Hata sonucu normal sayı veya başarıyla yakalanmış source unwind sayılmaz.

Araç CW'yi değiştirmez, başka PID/handle/HWND almaz, kaynak bot veya oyun modülü yüklemez. Hex girdi limitleri fixture'a özeldir. Kendi heap/string storage ve process cleanup sınırları oyun/runtime kimliği sertifikası değildir. Modeldeki kanonik signed32 kümesi ile genel parser çıktıları ayrı tutulur.
