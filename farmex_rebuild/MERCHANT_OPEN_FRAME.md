# Alış açma çağrısının sırası ve devamı

`merchant_open_frame.py`, BUY caller'ın yalnız phase3 kesitini (`00422c5a..00422c89`) modeller. Önceki `merchant_open.py` formatter/yerel kuyruk bileşimine çağıranın alan sırası eklendi. Native thread, stack, korumalı yazma veya oyun işlemi yürütülmez.

## Alanların sırası

| Aşama | Kaynak davranış | Yerel plan |
|---|---|---|
| Phase kontrolü | Object `+4 == 3` | Diğer phase için `not_applicable`; bütün caller çalışmış sayılmaz. |
| Bekleme işareti | BYTE `+48 = 1` | Saat bilinmese de prospective pending1 görünür. |
| Saat | `GetTickCount` | Aynı çağrıda bir kez gözlenir; eksikte ayrıca istenir. |
| Başlangıç zamanı | DWORD EAX → `+50`, yüksek DWORD 0 → `+54` | Tick sıfır genişletilerek QWORD saklanır. |
| Açma yardımcısı | `0042086c` | Önceki tampon/yazma-planı/iki-enqueue zinciri. |
| Dönüş | Yardımcı normal döndükten sonra DWORD `+4` artırılır | Ayrı `helper_returned=True` gözlemi olmadan phase4 kabul edilmez. |

Önceki UI adımında phase bekleme zamanı yardımcı tamamlandıktan sonraki deneme saatinden alınıyordu. Yeni bağlantı, yardımcıdan **önceki ilk yakalanmış tick'i** kullanır. Yardımcıda beklemek bekleme başlangıcını yenilemez.

## Aynı çağrıyı sürdürme

`BuyOpenFrame` giriş caller durumunu ve kendi kuyruğunu tutar. Eksikte `state` ve `queue` girişte kalır; sıralı alan/akümülatör/kuyruk prefix'i `prospective_state` ve `prospective_queue` içindedir. Bu politika native etkilerin geri alındığı anlamına gelmez.

Gözlemler aynı invocation'a ait olmalıdır. Bilinen başlangıç pointer'ı, free/coin sonucu, slot okuması, hazırlanmış kayıt, count ve seçili-satır global pointer'ı sonradan değiştirilemez. Boş `None` alanları tamamlanabilir. Bu, önceden bir değer tahmin edip daha sonra çalışma anı gözlemi gibi değiştirmeyi engeller. Yeni gerçek çağrı için yeni frame gerekir. Karışık snapshot, vector veya native pointer eşzamanlılığının çözülmüş olduğu iddia edilmez.

Normal-return bayraklarında False, normal tamamlanmanın henüz doğrulanmadığını belirtir; daha sonra True ile tamamlanabilir. Bu bayraklar native fonksiyonun gerçek dönüş değeri değildir; exception sonrası native stack'i devam ettiren bir araç bulunmaz. Daha önce tamamlandığı bilinen yardımcı False'a geri çevrilemez.

Tam formatter sonucu elde edilince tamponlar dondurulur. Sonraki helper-return boşluğunda değişen yeni formatter girdileriyle yeniden yapılmaz. Kısmi formatter planı, aynı bilinen snapshot'tan saf hesapla tekrar kurulabilir; gerçek okuma/yazma veya allocator çağrısı tekrarlanmaz.

İlk enqueue tamamlanıp ikincinin örneği eksik kalırsa ilk kopya ve ID korunur; yeniden enqueue edilmez. Tamamlanmış enqueue'a ait sonraki örnekler artık kullanılmaz. Hâlen tick bekleyen enqueue için bilinen bağlantı kapısı değiştirilemez. İki kaydın tamamından sonra bile toplam helper normal dönüşü ayrıca gerekir. Sonraki `step()` çağrısı `already_complete` döndürür; ikinci kez phase artışı veya kopya yapmaz.

## Arayüz bağlantısı

“Buy Merchant” phase3, bir frame oluşturur ve helper gözlemleri eksik olsa bile pending/clock prefix'ini gösterir. Tam normal yolda önceki runner açma geçişi bir kez uygulanır; bekleme zamanı frame'in ilk tick'iyle sabitlenir. Hazırlık phase2→3 geçişinde yeni frame ve akümülatör oluşturulur; eski yerel kuyruk korunur. Yeni deneme kuyruğu da sıfırlar.

Yeni phase2→3 hazırlık geçişinde eski açma sonucu göstergesi de temizlenir; daha önceki tamamlanmış frame yeni denemeye aitmiş gibi gösterilmez. Yerel kuyruk korunur ve sonraki açma yeni ID'lerle yeni kayıtlar ekler.

Frame girişi, saat ve helper/producer bayrakları UI'nin sentetik gözlemleridir. Kaynak pending BYTE'ı gerçek oyun belleğine yazılmaz. Sonraki phase4/5 bildirimleri, producer cevabı ve bütün Merchant döngüsünün kaynak saati/taşma davranışı bu dar eklemenin tam native eşdeğeri değildir.

## Kanıt

`work/audit_merchant_open_frame.py`, eski ve güncel Richard dosyalarında kesitin 16'şar talimatını byte olarak yeniden denetledi: 32 kayıt. Pending yazısı → GetTickCount → yüksek stamp DWORD'unu sıfırlama → helper → phase artışı sırası ve iki sürümde aynı `KERNEL32.DLL!GetTickCount` import kimliği doğrulandı. Kayıt üst çıktı dizininde `FarmexBot_alis_acma_caller_kod_kaniti.json` dosyasıdır. Ghidra byte denetimi REA Evidence veya canlı çağrı izi değildir.

On yeni test dahil1719 birim testi geçti (6.506 s). Genişletilmiş gizli UI; iki saniyelik helper boşluğunda ilk tick'in korunmasını, phase3beklemesini ve sonunda iki kayıtla phase4geçişini doğruladı.1037kontrol/11form/18ana sekme regresyonu geçti. Son gösterge temizliği ayrıca `work/verify_buy_open_frame_ui.py` ile gizli kendi EnginePage'imizde sınandı: giriş tick61004korundu, doğrudan kendi phase2fixture'ı yeni phase3sonucunu temizledi ve eski iki kaydı koruyarak toplam dört benzersiz kuyruk ID'si üretti. Bu son kontrol tam native yeniden başlatma değildir. Native testler bu Python/UI adımında tekrar çalıştırılmadı.

Gerçek caller/pointer/heap/ABI ve oyun eşdeğerliği açık kalır. Bu çalışma oyun erişim hakkı engelini çözmüş sayılmaz.
