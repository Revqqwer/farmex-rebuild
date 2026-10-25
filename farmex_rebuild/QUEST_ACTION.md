# Seçili Al/Ver — yerel devam API'si

`QuestActionFrame`, `004d5a8c` Al ve `004d6040` Ver normal akışlarını aynı
çağrı sırasını koruyan ayrı dallarla modeller. Gerçek düğmelere veya ortak
eylem kuyruğu yayımlayıcısına henüz bağlı değildir. Kendi bağımsız QueueState'i
vardır; oyun çağrısı, gönderim veya sunucu onayı yapmaz.

Görünür satır caption'ından koleksiyon indeksi alınır. NPC adı C++ string
hazırlama span'inden geçer; ID ve pointer ayrı sorgulanır. İki koordinat
offset'i ve float32 helper sonuçları, mesafe sonucu ve iki FPU dalı ayrı
gözlemlerdir. Sıralı0..10 aralığı dışında akış hedef/kuyruk bölümüne girmez.
Hedef farklıysa retarget yardımcısına NPC pointer'ı verilir; ID verilmez.
Hazırlama helper'ı, record data+20 okuması ve durum çağrısı takip eder.

| Özellik | Al | Ver |
|---|---|---|
| Durum AL | Çağrı/dönüş beklenir; değer dallanmakta kullanılmaz | Yalnız AL3 ilerler |
| Lookup modu | 4 | 3 |
| İlk6 byte isteği | 6407 + ID düşük WORD + iki sıfır | Aynı |
| İlk kuyruk gecikmesi | 500 | 1000 |
| Script istekleri | 55/00/lenLow + tam script, sonra FF eklenmiş hali | 55/00/lenLow + tam script +02 |
| Script gecikmeleri | 1000,1500 | 2000 |

Lookup'a görünen ad, iki ayrı source-index okumasından üst sınır ve DWORD
sarmalı sourceIndex-4 alt sınırı verilir. İç arama çözülmüş sayılmaz; EAX
gözlemi gerekir. Sonuç0 için kaynak caller erken çıkmaz. Data+1c yardımcısının
dönüşü beklenir fakat kullanılmayan sayısal değeri uydurulmaz.

C++ char_traits<char>::length importu kaynakta doğrulandı. Varsayılan API
hazırlanmış C++ string byte'larını açık gözlem olarak ister. Açık own-Cstring
modunda record ANSI girişinin ilk NUL'a kadar olan kısmı kullanılır. Bu mod
native allocator/alias/exception semantiğini kanıtlamaz. Paket başlığında
uzunluğun yalnız düşük byte'ı, gövdede tam C++ string kopyası kullanılır;
record script-storage DWORD'u uzunluk olarak kullanılmaz.

Her004c7710 çağrısı ayrı gate ve DWORD tick ister. Gate0 ise o çağrının saati
tüketilmez. Pozitif gate'te tick'ten sonraki append span'i ayrıca gözlemlenmeden
yerel kuyruk kaydı oluşmaz. Bilinen append öneki outer-helper dönüşü beklerken
korunur; devamda yeniden eklenmez. Önce okunmuş gate/tick yeniden örneklenmez.
Bu yerel projection'dır; native heap/vector ve sender eşliği değildir.

512 byte kaynak tamponu dışına taşabilecek yol normal başarıya çevrilmez.
Örneğin509 byte script Al yolunda ilk iki kuyruk önekini bırakır, FF ekleme
çözülmemiş taşma olarak durur. Ver yolunda02 ekleme öncesi aynı sınır ayrıdır.
Önekler geri alınmaz; script veya uzunluk sessizce kesilmez.

24 yeni testle4897 Python testi geçti. Yeni GUI çalıştırılmadı; önceki4873
detay UI aşamasının904 kod kaynağı ve GUI import kapanımı değişmedi. Gerçek
Al/Ver düğmeleri ve ortak kuyruk yayıncısı sonraki entegrasyondur.
İki PE'de2002 instruction kaydı ve paket/float/import sabitleri yeniden
doğrulandı. Bu sayı bitmiş fonksiyon veya proje yüzdesi değildir.
Tam kanıt `QUEST_ACTION_VALIDATION.json`; byte raporu proje kökünde
`outputs/FarmexBot_gorev_Al_Ver_kaniti.json` dosyasıdır.
