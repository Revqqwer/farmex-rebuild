# Kendi CRT zaman fixture'ı

Kendi x86 EXE yalnız sabit kimlikli standart CC32260MT kütüphanesinin `_localtime` ve `_sprintf` export'larını çağırır. Dışarıdan verilen32-bit epoch değerinin localtime çıktısını hemen dokuz int olarak kendi alanına kopyalar. Aynı alanları kaynakta gözlenen sırada sıfır dolgusu olmadan biçimlendirir. Bot/game modülü yüklenmez ve başka süreç okunmaz.

`build_merchant_crt_time_fixture.ps1` sabit SHA256'lı TinyCC ile derler. `work/check_merchant_crt_time_native.py` 15 epoch girdisinin native struct/biçim çıktısını own skaler modelle karşılaştırır. 15 normal gözlemde0 fark; bu kümede null localtime gözlenmedi. Negatif epoch DWORD'u da ayrı gözlemdir. Saat dilimi/CRT global davranışı host'un kendi sürecine aittir; oyunun globali olarak sunulmaz.

Zaman struct'ında `tm_mon=0` gözlemleri korunur. Kaynakta +1 bulunmadığı ayrı assembly incelemesiyle sabitlenmiştir; fixture bunu düzeltmez. Source managed string formatter, full lifetime/SEH, null pointer kopyası veya orijinal dosya üreticisi çalıştırılmış değildir.

CRT/EXE/kaynak hash'leri ve bütün native gözlemler `outputs/FarmexBot_merchant_CRT_zaman_native_kaniti.json` içindedir.
