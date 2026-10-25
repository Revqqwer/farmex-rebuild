# NPC User Trade Unicode üreticisi

4620 Python testi ve yeni tam yerel GUI1037 kontrol/11 form/18 sekme geçti.
Kayıt NPC_UNICODE_VALIDATION.json. Önceki4609 aşaması tarihsel kayıttır.

User Trade satırı Add/caption sonrasında tamamlanmış ANSI isim byte'larını
kullanır. Kaynak nullness ve ANSI başlık WORD codepage'i açık gözlemdir.
Header0 ve nonempty metinde ayrıca somut effective codepage gerekir;
host ACP tahmin edilmez. Nil doğrudan boş metne gider; nonnil counted empty
header gözlemini ister, fakat locale decoder/default kod sayfasını istemez.

Kendi Windows flags0 dönüşüm sonucu, RTL/00402d20/00403d84 normal dönüşlerinin
yerini almaz. Üç dönüş ayrı onaylanmadan satırın alt alanları yazılmaz.
Tüketilen gözlemler ve üretilen metin tutulur; poll tekrar decoder çalıştırmaz.
Başlamış Unicode child hazır metinle atlanamaz. Eski explicit hazır metin
sağlayıcısı child başlamadıysa desteklenir. NPC dalı geç Unicode girdisini
tüketmez. Silinen satır/profile geçişi geç metni yeni satıra yazdıramaz.

Pinli standart RTL ile kendi x86 süreçlerinde264 sonlu örnek ve bunların
ürün modeline karşılaştırması geçti. CP1254 strict Python decode'un reddettiği
81/8d/8e/8f/90/9d/9e byte'ları için kaynak referansın Unicode sonucu korunur.
Tam GUI gerçek düğmede81 örneğini, bekleyen RTL dönüşünü, korunan satır
önekini ve gizli formda devamı doğrular. Kaynak/RTL için1289 instruction
kaydı byte düzeyinde doğrulandı. Bu sayılar tam fonksiyon sayısı değildir.

Bu, captured veri akışıdır; oyun/bot/native helper yürütücüsü değildir.
Standart RTL sonlu referansı bütün heap/alias/lifetime/SEH/istisna veya
eşzamanlı runtime değişikliklerini kanıtlamaz. Botun runtime codepage/null
gözlemleri otomatik edinilmez. Güncel oyun profili/erişim, diğer sekmelerin
eksikleri ve canlı uçtan uca doğrulama devam eder. Oyun IO0.
