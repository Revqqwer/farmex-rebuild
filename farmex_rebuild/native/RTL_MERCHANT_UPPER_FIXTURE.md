# Kendi x86 RTL uppercase/conversion referansı

`build_rtl_merchant_upper_fixture.ps1` pinned TCC ile `rtl_merchant_upper_fixture.c` dosyasını derler. Kendi disposable x86 süreçte yalnız pinned standart RTL paketi açılır/initialize edilir. Orijinal FarmexBot/oyun modülü yüklenmez; başka PID/handle veya HWND kabul edilmez.

Argümanlar: standart RTL absolute path, `query` veya `ansi`, hex girdi. Query girdisi counted UTF16LE string; ANSI girdisi byte dizisidir. Query register ABI: EAX input UnicodeString, EDX output pointer; ardından EAX ANSI output pointer, EDX upper UnicodeString, ECX0 ile LStrFromUStr. ANSI register ABI: EAX original byte-string handle, EDX output pointer. Girdi sabit managed header refcount-1 kullanır; bu fixture'ın kendi storage'ıdır. Boş girdi nil olarak verilir.

Fixture iki çağrının stack durumunu, Unicode/ANSI çıktı byte'larını, output managed codepage alanını, gerçek own RTL DefaultSystemCodePage alanını, ACP ve LCID'leri kaydeder. İlk native istisna gözlemcisi yalnız kendi sürecini bitirir; native unwind/continuation taklidi değildir. Normal süreç de çıktıdan sonra biter, source managed cleanup sertifikası verilmez.

`work/check_merchant_upper_native.py`385 finite girdiyi her biri ayrı own süreçte çalıştırır; ham iz ve girdi/hash'leri rapora bağlar. Python modelinin `code_page` alanı işlem politikasıdır; fixture output header alanıyla aynı şey değildir. Nil ANSI sonuç header'ı yoktur. CP0 çözümü yalnız own initialized runtime'da ölçülmüştür, source loaded game kimliği ve codepage değeri açık kalır.
