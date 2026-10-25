# Sıralı mesaj kanal yardımcısı

23 Ekim 2026. `message_channels.py`, Richard0045c1f8 normal branch/call
akışını ve mevcut kaynak döngüsüne tipli çocuk bağını modeller. Yeni
REA213-talimat gövdeyle eşleşir. İki sürümde bu gövde ve84-talimat caller
toplam594 disk kaydı olarak doğrulanır. Gerçek native string/serializer
veya gönderim yürütülmez.

| Karşılaştırma sırası | Kaynak literal | 004c9b74 mode argümanı |
|---:|---|---:|
| 1 | All Chat | 0 |
| 2 | Party | 2 |
| 3 | Clan | 3 |
| 4 | Shout | 1 |
| 5 | Merchant | 4 |
| 6 | Noah Knight | 34 |

Bunlar çağrılan yardımcının mode değerleridir; gönderilen paket üzerinde
aynı enum/byte anlamına geldikleri henüz doğrulanmadı. İlk true karşılaştırma
kazanır. Helper EAX'ının yalnız AL baytı test edilir; yalnız1 koşulu yoktur.
Hiçbiri eşleşmezse004c9b74 atlanır, iki argüman yine temizlenir.

Önce stack parameter+10, sonra+c managed-copy normal dönüşü gerekir.
Her literal için ayrı oluşturma, karşılaştırma ham EAX ve literal cleanup
normal dönüşü tüketilir. Karar cleanup'tan önce yakalanmış EAX üzerinden,
cleanup tamamlandıktan sonra verilir. Model text->eşitlik algoritmasını
uydurmaz; karşılaştırma AL gözlemi native eşitlik kanıtı değildir.

0045cce8 caller'ının fiziksel PUSH sırası field4,field0,context'tir. Bu
yardımcı+c parametresini kanal literaline karşılaştırır, +10 parametresini
serializer'a taşır. Böylece field0 kanal argümanı, field4 mesaj argümanı
olarak tipli bağlanır. Helper kendi sender context'ini561ef8 sabitiyle
geçirir; caller'ın context argümanı bu sabit yerine kullanılmaz.

Managed işlemlerden sonraki taze+10 DWORD'u ayrıca gözlenir; giriş mesaj
handle'ına eşit varsayılmaz. Fiziksel serializer PUSH sırası taze_mesaj,
mode,561ef8 olur. Serializer normal dönüşü ile kanal ve mesaj argümanı
temizlik dönüşleri ayrıdır. Normal sınır sonu45c479; native SEH/ABI yoktur.

`ChannelMessageCycleFrame` ulaşılmış mesaj-helper noktasında alan argümanlarını
bağlar; dışarıdan raw helper-return override'ı kabul etmez. Tamamlanmış
kanal çocuğundan sonra ayrıca caller normal dönüşü gerekir. Ancak sonra
ikinci tick/zaman/index planları açılır. Eşleşmeyen kanal da normal dönerse
zaman/index ilerleyebilir; bu gerçek mesaj veya teslim başarısı değildir.

11 yeni test; toplam3973 test geçti. UI378 bağlı/145 bağlanmamış olarak
değişmedi; önceki tam UI kaynakları aynıdır. Liste derleyicisi, UI toggle,
512-talimat serializer, gerçek queue/sender, sunucu kabulü ve canlı bağlantı
bu aşamada tamamlanmış sayılmaz. Gerçek mesaj gönderilmedi.
