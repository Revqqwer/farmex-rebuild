# Kendi x86 Merchant liste sırası referansı

`build_merchant_list_sort_fixture.ps1`, `merchant_list_sort_fixture.c` ve register-call altyapısı `rtl_integer_fixture.c` ile kendi x86 test executable'ını derler. Fixture standart RTL paketini explicit path ile açar/initialize eder; orijinal bot veya oyun modülü yüklemez. Kendi gizli STATIC/SysListView32 penceresi ve indeks+1 lParam tokenları kullanılır.

Argümanlar: pinned RTL yolu ve sütun. stdin: satır sayısı, her satır için seller/item/quantity/price sırasıyla dört UTF16 hex satırı. Fixture sınırları 64 satır ve alan başına 500 UTF16 birimidir; bunlar üretim modelinin sınırı değildir. Normal çıktı sort sonucu, kontrolün gerçek token sırası, karşılaştırma sayısı, LVITEM boyutu ve common-controls kimliğini içerir. Native ilk Delphi istisnası gözlenirse kendi süreç sonlandırılır; kaynak exception continuation iddiası yoktur. Bu hata çıkışında normal açık pencere kapatma sertifikası verilmez; kendi process kaynaklarını OS bırakır.

`work/check_merchant_windows_sort_native.py` immutable girdileri/ham izleri ve kaynak hash'lerini kaydeder. Rapor 31 normal sıra ve dört failure/scope sınırını karşılaştırır. Price preparation yalnız ASCII digits/dot kapsamında; fullwidth fiyat ayrıca kapsam sınırıdır. Kaynak VCL object layout, kullanıcı HWND'leri, oyun belleği, injection veya canlı eylem bulunmaz.
