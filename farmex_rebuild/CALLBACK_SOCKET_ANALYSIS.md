# Callback içindeki soket ve oturum akışı

21 Ekim 2026. Bu belge statik çözümlemedir; çalışan ağ istemcisi veya canlı oyun doğrulaması değildir.

## Kanıt kapsamı

Dokuz yeni REA/Ghidra fonksiyon çıktısı, eski ve güncel Richard görüntülerindeki on fonksiyonla karşılaştırıldı. Onuncu fonksiyon mevcut hazırlık çağrısıdır. Toplam **3.492 instruction kaydının baytları** sabit SHA-256 ile seçilmiş disk görüntülerinden doğrulandı. Bu sayı önceki analizlere eklenen benzersiz instruction sayısı değildir; hazırlık çağrısı ve bazı yordamlar önceki kapsamlarla kesişir.

Denetim: `work/audit_callback_socket.py`; tam kanıt: `outputs/FarmexBot_callback_soket_yapisi_kaniti.json`. Kayıtta her iki sürümün adresleri, instruction baytları, import çağrıları ve dokuz REA evidence kimliği bulunur. Winsock ordinal import adları güncel REA thunk adlarıyla ayrıca karşılaştırıldı. Adres eşlemeleri tek tek belirtildi; genel adres kaydırma kuralı kullanılmadı.

| Rol | Eski Richard | Güncel Richard | Instruction |
|---|---|---|---:|
| Soket/oturum yoklaması | 004fc940 | 004fc95c | 876 |
| Soket oluşturma | 004e3f4c | 004e3f68 | 83 |
| Bağlanmayı başlatma | 004e4220 | 004e423c | 69 |
| Veri alma sarmalayıcısı | 004e4208 | 004e4224 | 10 |
| Veri gönderme sarmalayıcısı | 004e41f0 | 004e420c | 10 |
| Soketi kapatma ve yeniden oluşturma | 004e42f4 | 004e4310 | 33 |
| Alınan mesajı işleme | 004fa3b0 | 004fa3cc | 287 |
| Periyodik mesaj hazırlama | 004f9f4c | 004f9f68 | 339 |
| WORD okuma imleci | 004fac41 | 004fac5d | 10 |
| Hazırlık çağıranı | 0046edb0 | 0046edb0 | 29 |

## Hazır sonucu hangi anlama geliyor?

Hazırlık yordamı 0046edb0, 55424c nesnesiyle 004fc95c çağırıyor ve dönen AL değerini kontrol ediyor. Büyük yardımcı yalnızca bir nesne varlık kontrolü değil; soket/oturum durum makinesidir. **AL=1 sonucu bağlantı kurulduğu veya oyuna bağlanıldığı anlamına gelmez.** Yeniden deneme bekleme aralığında ve bazı hata sonrası bekleme yollarında da AL=1 döner. Üst EAX bitleri, yalnız MOV AL kullanılan dönüşlerde ayrıca bilinmez.

Nesne +338 DWORD alanı üç açık dala ayrılır:

1. **Durum 0:** +1bae ve +1bad bayrakları sıfırlanır. İlk +1be0/+1be4 zaman damgası gerekirse başlatılır. +1bac bayrağı sıfırken önceki denemeden itibaren 60.000 ms beklenir. Bayrak açıkken 56ffdc değeri sıfırsa 467cc4 yardımcısına fiziksel PUSH sırası 20,3 ile gidilir; dönen DWORD ile 60.000 çarpımı düşük DWORD'a kırpılıp işaret genişletilir. Eşik gelmeden AL=1 döner. Eşik geldiğinde +1bd8/+1bdc güncellenir ve bağlanma yardımcısı çağrılır. Sonuç 0 ise durum 2; 0x2733 ise durum 1 olur. Diğer sonuçlarda kapatma/yeniden oluşturma ve bayrağa bağlı bekleme yolu vardır.
2. **Durum 1:** Yazılabilirlik ve istisna fd_set alanları hazırlanır; select ve __WSAFDIsSet sonuçları izlenir. Yazılabilirlik dalı durum 2'yi yazar. Zaman aşımı +330/+334 başlangıcı ve +32c alanıyla karşılaştırılır. Bu dalı yalnız “bağlantı tamam” kabul eden model eksik olur; istisna, select hatası ve zaman aşımı dalları da vardır.
3. **Durum 2:** Okunabilirlik ve istisna fd_set alanlarıyla select kullanılır. Veri önce dört baytlık başlığa, sonra beklenen kalan gövde miktarına göre alınır. Parçalı başlık ve gövde ayrı sayaçlarda tutulur. recv pozitif değilse WSAGetLastError okunur; 0x2733 yolu beklemeye döner. Başka hatalar kapatma yoluna gider. Kaynakta recv=0 da bu ortak hata sorgusundan geçer; bunu standartlara göre farklı davranacak şekilde düzeltip eşdeğer saymak doğru olmaz.

Yoklama ve zaman kontrollerinde GetTickCount sıfır genişletilip iki DWORD'luk saklanan zamanla SUB/SBB yapılır. Bu işlemler bütün dallarda basit DWORD sarma farkı olarak değiştirilemez. Dal sınırları ve işaretli üst DWORD karşılaştırmaları korunmalıdır.

## Oluşturma, bağlanma ve kapatma

Oluşturma yordamı gerektiğinde WSAStartup(0x202), mevcut soket için closesocket, ardından socket(2,1,6), setsockopt ve ioctlsocket çağırır. Kaynakta ioctlsocket komutu 0x8004667e, işaret edilen DWORD değeri 1'dir. Başarısız ayar yolları soketi kapatıp alanı ffffffff yapar.

Bağlanma yordamı nesne +320 metin alanını gethostbyname'e verir; +324 WORD portunu htons'tan geçirir. Oluşan 16 baytlık adres yapısı ve nesnenin soket alanıyla connect çağrılır. Başarısız connect sonucu WSAGetLastError üzerinden döner. Bu incelemede +320/+324 alanlarının kurucusu veya gerçek sunucu adresi doğrulanmadı.

Kapatma yordamı shutdown(s,2) ve closesocket(s) çağırır; soketi ffffffff, durum ve bağlantı başlangıcını sıfır yapar. +340/+344 alanlarını yeni zamanla doldurur; başlık/gövde sayaçlarını temizler ve oluşturma yardımcısını tekrar çağırır. Dolayısıyla adı yalnız “close” olan ve yeniden oluşturmayı atlayan bir uygulama eşdeğer olmaz.

## Alınan çerçeve ve mesaj dalları

Başlık AA 55 baytlarıyla kontrol edilir. WORD uzunluk değeri ayrı imleç yardımcısıyla okunur. Çift değer yolunda 0xc504, tek değer yolunda 0xe0c0 eklemesi WORD taşmasıyla yapılır. Çözülen değer 1..27 sınırında olmalıdır. Biriken çerçevenin sonunda 55 AA aranır; uygun dal mesaj işleyicisini çağırır. Bu gözlemler tam protokol/şifreleme sertifikası değildir; veri dönüştürme yardımcıları ve tampon kurulumları ayrıca incelenmelidir.

Mesaj işleyicisinin ilk çözülen bayta göre dalları arasında şunlar vardır:

- 11: GetCurrentProcess ve TerminateProcess çağrı yolu.
- 12: İki korumalı okuma ardından shutdown(s,2) çağrı yolu; hedefin canlı soket kimliği doğrulanmadı.
- 14/15: 40ae0c bot durdurma yardımcısına sırasıyla 1/0 bayrağıyla giden yollar.
- 50 ve üzerindeki baytlarda 100'e bölümün kalanına göre dallanma. Kalan 1 yolunda okunan DWORD sıfır değilse 555dcc, dakika/saat alanları, 555df9 ve 555df8 bayrakları ile zaman damgası güncellenir. Kaynak sıfır kontrolü unsigned olduğundan yüksek biti açık DWORD'ları otomatik reddetmez; sonraki dakika/saat bölmeleri işaretlidir.
- Kalan 2 ve üzerindeki dal, bazı değerlerde 555dd4 alanını değiştirir ve 46b8fc üzerinden 4fab88 callback'ini yerleştirme çağrısına ulaşır. Bu dal yalnızca 2..7 değerlerinden ibaret değildir; diğer kalanlar da ortak çağrıya düşebilir.

Süre alanlarının ve bot durdurma yardımcısının kullanılması, bu soketin bot oturumu/yönetimiyle ilişkili olduğuna güçlü statik işarettir. Bunun oyun sunucusu soketi olduğu, gerçek sunucunun güvenilirliği, mesajların doğrulanması veya lisansın kabul edildiği kanıtlanmadı. Uzak mesaj dalları bağımsız sürümde çalıştırılmadı.

## Periyodik giden mesaj

4f9f68 karakter/durum okuyucularını çağırır, çalışma modu ve bot durum bayraklarını seçer, 512 baytlık tamponu temizler ve serileştirme yardımcılarıyla mesaj oluşturur. 4fc95c içindeki 30.000 ms eşiği bu hazırlık ve gönderme yoluna ulaşır. Aynı yordamda ilk oturum damgasına göre 600.000 ms ve son denemeye göre 60.000 ms birleşik koşulu üzerinden kapatma yolu da bulunur. 3.540.000 ms hata sonrası bekleme karşılaştırmaları ayrı dallardadır.

Alanların kesin tel sırası, metin kodlaması, bütün serileştirme yardımcıları, dönüştürmeler, gönderilen baytların canlı örneği ve sunucu cevabı henüz doğrulanmadı. send sarmalayıcısında tek çağrı görülmesi, kısa gönderimler için güvenilir teslim garantisi vermez.

## Sonraki doğrulama sınırları

- +320/+324 alanlarının üretimini, 55424c nesnesinin kurulumunu ve hangi bağlantı rolüne ait olduğunu kaynak üzerinden izlemek.
- Mesaj okuma/yazma ve dönüşüm yardımcılarını tek tek çözmek; taşma, kısmi I/O ve hata yollarını korumak.
- Oturum sunucusuyla iletişim kanıtını, oyun belleği/ABI/callback bağlantısı kanıtından ayrı tutmak.
- Native çalıştırma, istisna/SEH davranışı, eşzamanlı alan değişimleri ve canlı profil kimliğini ayrıca doğrulamak.

Bu aşamada ağ isteği ve oyun işlemi sayısı **0**. Üretim davranışı değiştirilmedi; önceki **3.308** yerel test sonucu bu yeni statik bulguların canlı doğrulaması sayılmadı. Kapsamlı davranış modeli sayısı **140** olarak kaldı; dokuz yeni REA incelemesi otomatik olarak dokuz tamamlanmış fonksiyon diye sayılmadı.
