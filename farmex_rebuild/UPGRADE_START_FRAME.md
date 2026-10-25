# Upgrade başlat/durdur: yerel API aşaması

`upgrade_start_frame.py`, kaynak 004f7af8'in sırasını ortak, source-clock etkin
`UpgradeRunner` üzerinde adım adım uygular. Bu aşama gerçek panel düğmelerine
henüz bağlanmadı; worker aktarımı ve canlı veri sağlayıcısı da tamamlanmadı.

Başlatma önce kendi düğme durumlarını değiştirir; ayrı end/begin/erase normal
dönüşlerinden sonra kuyruğu temizler. Parametre üreticisindeki cached ANSI scroll
değeri açık kod sayfasıyla çözülür. Scroll araması 14..41 slotlarını dolaşır;
bulunamazsa -1 saklanır ve satır döngüsü yine devam eder. Her satırda güncel
satır sayısı/işaret durumu okunur. Seçili caption Int32 dönüşümü, cleanup ve append
normal dönüşleri ayrı ayrı beklenir. Mod yalnız son aşamada 1 olur.

Durdurma modu düğme işlemlerinden önce 0 yapar. Kuyruğu, scroll indeksini ve
iki zaman damgasını korur. Başlatma da zaman damgalarını sıfırlamaz. Eksik gözlemde
bilinen değişiklikler korunur; tamamlanmamış işlem başarı olarak bildirilmez.
Geçersiz caption için varsayılan sayı veya native exception sonucu uydurulmaz.

`upgrade_scroll_frame.py`, ulaşılan key/name girdilerini tutar; devam etmek için
önceki snapshot'ın yeniden verilmesi gerekmez. Alt isim okuyucusu aynı kuralı
`mining_slot_name.plan_slot_name` üzerinden uygular. ANSI uzunluğu, case ve NUL
korunur. Her slottaki dönüşüm byte'ları açık gözlemdir; otomatik edinilmiş değildir.

Testler sıralamayı, kesintide korunan değişiklikleri, yeniden denemede çift append
olmamasını, fresh satır sayısını, geçersiz caption'ı, boş/eksik kod sayfasını,
sayılmış NUL'u, iptali ve alt isim devamını kapsar. Yerel worker'ın zaten bekleyen
işi varsa yeni frame reddedilir; bu kendi eşzamanlılık politikamızdır.

`UPGRADE_START_FRAME_VALIDATION.json` tam Python test sonucunu ve kod hash'lerini
kaydeder. 328 kaynak instruction kaydı iki retained PE'den yeniden karşılaştırılır.
Bu, native UI/RTL/allocator eşliği veya oyunda çalışma kanıtı değildir. GUI yeniden
çalıştırılmadı; dağıtım ZIP'i önceki doğrulanmış 4677 aşamasında bırakıldı.
