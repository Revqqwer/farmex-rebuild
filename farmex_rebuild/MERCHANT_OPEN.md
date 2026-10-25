# Alış pazarını açma planı

Sonraki caller bağlantısı: `merchant_open_frame.py`, pending BYTE→tek giriş tick'i→QWORD stamp→açma yardımcısı→ayrı normal dönüş→phase artışı sırasını ve eksikte devamı ekler. UI bekleme başlangıcını artık helper'ın bitiş saatine taşımaz. Tamamlanmış tampon/kuyruk kopyaları korunur. Ayrıntı: [MERCHANT_OPEN_FRAME.md](MERCHANT_OPEN_FRAME.md). Aşağıdaki ilk aşamadaki “native caller prefix uygulanmadı” sınırı bu dar yerel kesit açısından daraltılmıştır; gerçek oyun etkileri hâlâ açık.

`merchant_open.py`, `0042086c` normal yolunu; hazırlanmış kayıtlar, taze çanta/coin sonuçları ve açık yardımcı dönüşlerinden hesaplar. `plan_buy_open` tampon ve yan etki planlarını üretir. `compose_buy_open` bunları kendi değişmez kuyruğumuza bağlar. İkisi de oyun belleğine erişmez, koruma değiştirmez veya ağ gönderimi yapmaz.

## Sıra, seçim ve alan genişlikleri

Kaynak önce `value(global553f4c)` değerini yerel hedef cursor'una alır. Sonra **taze** `0042070c` boş-yuva sayısını ve `0046258c` coin EAX değerini alır. Önceki hazırlık hesabının değerleri kendiliğinden tekrar kullanılmaz. Çanta için 28 ayrı getter gözlemine bağlanabilen önceki model kullanılabilir.

Başlangıç tamponu `68 22 00` olur. Her döngü koşulunda önce unsigned vector-count sonucu gerekir; sonra boş yuva ve en fazla 12 seçili satır sınırı gelir. `stable_records=True` açık sabit snapshot varsayımıdır; aksi halde her koşul için ayrı count gerekir. Son boş yuva veya on ikinci seçimden sonra da bir sonraki count sorgusu kaynaktaki sıranın parçasıdır.

Item DWORD, adet DWORD ve **fiyatın düşük DWORD'u** alınır. Bütçe maliyeti `(adet DWORD × fiyat DWORD) & 0xffffffff` olur; IMUL yüksek kısmı kaynakta atılır. Karşılanamayan satır atlanır, sonraki daha ucuz satır hâlâ seçilebilir. Seçilen her satır tamponda şu 10 baytı üretir:

| Alan | Boyut | Düzen |
|---|---|---|
| Item ID | 4 | Little-endian DWORD |
| Adet | 2 | Adet DWORD'unun düşük WORD'u |
| Fiyat | 4 | Hazırlık QWORD'unun düşük DWORD'u |

Bütçe hesabı tam adet DWORD'unu kullanırken tampon düşük WORD'u kullanır; bu ayrım düzeltilmeden korundu. Hazırlık kaydındaki 64 bit fiyat da değiştirilmez. Kaynak aktarımı 32 bit olduğundan yüksek fiyat DWORD'u bu tampona girmez.

Maliyet bütçeden düşülür; boş yuva azalır, seçilen sayısı artar. Object `+98/+9c` QWORD toplamına maliyet eklenir; 64 bit taşma korunur. Bu toplam, satın alma veya coin ödendiği kanıtı değildir.

## Yürütülmeyen bellek yan etkileri

Seçilen her satırda global pointer yeniden okunur. `0045ddf4(fresh_global_base-0x28, 0)` planı dört baytlık korumalı sıfır yazma yardımcısıdır. Bu yardımcı `VirtualProtect(...,4,0x40,...)` olumluysa memcpy yapar; **normal dönmesi yazmanın başarılı olduğu anlamına gelmez**. Testler bu yardımcıyı veya VirtualProtect'i çalıştırmaz.

Sonra ilk alınan pointer'dan başlayan yerel cursor için 35 bayt sıfır memset planı vardır. Cursor her seçili satırda 40 bayt ilerler; atlanan liste satırları cursor'u ilerletmez. Her blokta kalan beş baytın da sıfırlandığı varsayılmaz. Korumalı yardımcı ve memset ayrı normal-return gözlemleri gerektirir; eksikte sonraki count veya kuyruk aşamasına geçilmez. `write_plans` gerçek bellek yazısı değildir.

## İki kuyruk çağrısı

Hiç satır seçilmemişse tampon gönderim planı ve kuyruk kaydı yoktur. En az bir seçimde:

1. Kaynaktaki `0050dab8` literalinden `68 21`, 0 ms gecikme.
2. Liste tamponunun üçüncü baytı seçilen sayısıyla güncellenir; `68 22 count` ve satırlar, 1000 ms gecikme.

Liste boyutu `3 + 10 × count`, en fazla 123 bayttır. İki `004c7710` planının bağlantı kapısı ve tick gözlemi ayrıdır. Kapı 0 kayıt eklemeyen normal yoldur; o çağrı için tick gerekmez. Nonzero kapı ayrı tick gerektirir. Bir çağrı eklenirken diğeri eklenmeyebilir.

Eksikte giriş kuyruğu ve durum kabul edilmiş sonuç olarak korunur; bilinen prefix `prospective_queue`, `prospective_state` ve source planında görünür. Tam yerel bileşimde yeni kuyruk/durum döner. Saf planı yeniden hesaplamak gerçek native kısmi etkilerin geri alınması veya tekrar yürütülmesi değildir. Kuyruk drain edilmez; sunucu ACK'si üretilmez.

## Arayüz ve kaynak sınırı

“Buy Merchant” phase3 denemesi artık hazırlanmış satırları bu açma bileşimine verir. Açık örnekte fake global-base `0x7000`, sabit vektör, normal yardımcı dönüşleri ve iki nonzero kuyruk kapısı kullanılır. Saatler ayrı olarak deneme zamanı+1 ve +2'dir. Bunlar oyun adresleri veya oyun gözlemleri değildir. Yeni denemede kendi kuyruk/sayaç durumu sıfırlanır; kendi pazar döngüsü tekrar hazırlanırken toplam sıfırlanır, eski kuyruk korunur.

UI yalnız tam yerel bileşimden sonra önceki runner'ın açma geçişini uygular. Native caller ise `+48` pending byte'ını ve `+50/+54` timestamp'ini **yardımcıdan önce** yazar, phase'i yardımcının normal dönüşünden sonra artırır. Bu native kısmi caller alanları ve exception/concurrency davranışı bütünüyle uygulanmış sayılmaz. UI'deki sonraki producer/pending bayrakları önceki sentetik örneklerdir; gerçek pazar kabulü değildir.

`work/audit_merchant_open.py`, eski ve güncel dosyalarda beş gövde ve caller kesitindeki 506 talimat kaydını, literal iki baytı, BYTE/WORD/DWORD kopya genişliklerini, miktar/sınır/stride/gecikme anchor'larını ve import kimliklerini doğrular. Kayıt üst çıktı dizinindeki `FarmexBot_alis_pazari_acma_kod_kaniti.json` dosyasıdır. Bunlar Ghidra exact-byte denetimleridir; REA Evidence veya canlı çağrı izi değildir.

On yeni test dahil 1709 birim testi geçti (6.208 s). Genişletilmiş gizli UI testi, hazırlanmış panel kaydı→düşük fiyat DWORD'u→13 bayt liste→iki yerel kuyruk kaydı bağını, 0/1000ms gecikmeleri ve toplam maliyet2sonucunu doğruladı.1037kontrol/11form/18ana sekme regresyonu da geçti. Native testler bu Python/UI adımında tekrar çalıştırılmadı.

Gerçek prepared vector, coin, çanta, hedef pointer, bellek yan etkileri, açma/producer cevabı, kuyruk drain, oyun ABI ve sunucu sonucu hâlâ doğrulanmadı.
