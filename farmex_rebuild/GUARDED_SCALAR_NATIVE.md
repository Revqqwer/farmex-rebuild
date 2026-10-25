# Üç skaler yardımcının yerel talimat testi

Kaynak SHA256: `febdac805f370fb3ecc1ba5bf76482eb1f3d9b52c080113eb1dc9f12d2e45759`.
DWORD okuyucu `0045dc44` (26 talimat), byte okuyucu `0045dbdc` (26),
byte yazıcı `0045de4c` (20): toplam 140 özgün kod byte'ı.

`native/guarded_scalar_templates.h` kaynaktan çıkarılan gövdeleri içerir.
`native/guarded_scalar_fixture.c` bunları yalnız kendi ayırdığı kod ve veri
sayfalarında çalıştırır. Dört CALL operandı kendi API sarmalayıcılarına taşınır;
diğer byte'lar aynen korunur. Özgün DLL veya Delphi runtime yüklenmez.

12 yerel senaryo geçti: null okuyucular, gerçek DWORD/byte okumaları,
başarılı API dönüşünün üst EAX bitlerini koruyan AL okuması, kontrollü API
başarısızlıkları, null yazıcı başarısızlığı, tek byte yazımı ve ardından okuma.
Gerçek yazma yalnız kendi veri sayfasında gerçekleşir; komşu byte'lar korunur.
Başarı yollarında gerçek Windows VirtualProtect kullanılır; kontrollü başarısızlık
ve üst bit senaryoları API sarmalayıcısının açık test girdileridir.

Bu deney oyunun belleğini, korumalarını veya canlı uyumluluğunu sınamaz.
Kaynak yordamların VirtualProtect sonrasında korumayı geri yüklememesi ve byte
okuyucunun yalnız AL'yi değiştirmesi korunmuştur. Hata/exception yollarının tamamı
kanıtlanmış değildir. Derlenmiş EXE dağıtım paketine eklenmez.
