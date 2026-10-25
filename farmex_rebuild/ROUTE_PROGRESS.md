# Rota ilerleme, varış ve bekleme üreticisi

18 Ekim 2026. `route_progress.py`, güncel004eb2c4 içinde004eb3ef adresine
ulaşılmasından başlayıp mevcut hareket/çıkış modellerine bağlanır. Daha önceki
entry, Enemy geçişi ve local-31 sorgu üreticisi dış sözleşmedir. Native
004f276c satır yürütücüsünün tamamı bu modelle çözülmüş sayılmaz.

## Okuma ve yazı sırası

Girdiler `(object/global, offset/address, bit width, value)` biçiminde sıralı
ve taze örneklerdir. Tek snapshot sözlüğünden aynı alanın bütün okumaları
doldurulmaz. 566/567 flag'leri kısa devreyle okunur. İlk pass'te5ec önce signed
negatiflik guard'ı için, sonra544 ile signed karşılaştırma için yeniden
okunur. İkinci okumanın ilk değerle aynı olması varsayılmaz.

Şartlar uygunsa6d9=1 yazısı clock'tan önce gelir. GetTickCount DWORD sıfırla
genişletilip tam QWORD56ff94/56ff98 damgasından çıkarılır. Signed64 fark5000'e
ulaşmışsa004eaf94 çağrısının normal dönüşü gerekir. Damga, önceki karşılaştırma
saatinden değil **ayrı bir GetTickCount** örneğinden güncellenir. Bu yardımcı
gövdesinin yan etkileri henüz modellenmez.

Ardından004f276c normal-return EAX DWORD'u ayrı gözlemdir. Taze5f0 sayısından
düşük32bitte1 çıkarılır; dönüş bu değere eşit değilse hareket/çıkışa gidilmez.
Count0için son değerffffffff olur; kendi positive-count guard'ı eklenmez.
Eşitlik sonrası ayrıca taze BYTE5e8 sıfır olmalıdır. Bu iki koşul native
satırın veya gerçek hareketin başarılı olduğuna dair ACK değildir.

Taze global561f58 nonzero ise önceki `route_motion` modeline geçilir. Sıfır
ise AntiCR flag/durum ve daha önce üretilmiş local-31 BYTE ayrı okunur.
Şartlar uygunsa004eb4dc..004eb513 AntiCR rota yükleme/temizleme span'ının normal
dönüşü istenir; bundan sonra doğrudan dönülür. Diğer rota türlerinin dosya
yükleyicisi bu span yerine kendiliğinden geçirilmez.

Sonraki pass566/567 ve6d9/6da alanlarını yeniden okur. Hiç flag yoksa
56ff9c/56ffa0/56ffa4 sıfırlanır, sonra hareket modeline geçilir. Done6da
nonzero yolu da hareket modeline gider. Bekleyen request dalı6d9=1 yazar,
5000ms kontrolünü yapar ve gerekirse ayrı yardımcı/saatle damga günceller;
bu dal hareket/çıkışa uğramadan döner.

6d9 nonzero/6da0yolunda metric yardımcısının karşılaştırma sonucu AH gözlemidir.
Girdiler signed DWORD562004/562000, disk float eşiği50,0'dır. Model metric
formülünü, float argüman dönüşümünü veya FPU exception'larını hesaplamaz;
kaynağın `AH & 45hex` testini uygular. Greater yolunda5000ms request kontrolü
sonrası dönülür. Less/equal/unordered yolunda sırasıyla6d9=0,6da=1,
56ff9c=ayrıclock,56ffa0=0 yazılır;00467cc4(2000,7000) dönüşü56ffa4'e yazılır.
Saat ve RNG seed saati birbirinin yerine kullanılmaz.

## Mevcut RNG modeliyle bağ

Ham helper EAX yerine `SourceRandomObservation` verilebilir. Daha önce
modellenmiş `replay_source_random(2000,7000,...)` kullanılır; kendi clock,
srand normal dönüşü ve rand EAX veya açık pinned disk CRT replay sözleşmesi
gerekir. Ham EAX ve bound helper birlikte yalnız bu dal erişildiğinde çatışır.
Eksik veya arithmetic-fault planı geldiğinde limit yazılmaz ve deneme
tamamlanmaz. Bekleme damgasına kadar bilinen ön yazılar ayrı korunur.
RNG algoritmasının yüklü oyun CRT'siyle aynı olduğu varsayılmaz.

Bu API saf denemedir. `writes` bilinen kaynak yazılarını sıralar; eksik alt
modelde kabul edilen active/enable girişte kalır, alt modelin prospective
değerleri ayrıca sunulur. Opaque yardımcıların yazabileceği diğer alanlar
emüle edilmez; normal dönüş gözlemi bu yan etkilerin çözüldüğü anlamına gelmez.
Alt hareket modelinin saatleri/koordinatları/global örnekleri taze ve ayrıdır.
Gerçek process, bellek, FPU, RNG veya oyun eylemi yürütülmez.

## Doğrulama

`work/audit_route_progress.py` iki hash'li dosyada caller ve20talimatlık RNG
helper'ından **374 talimat kaydını** baytlarıyla doğrular. Dal/store anchor'ları,
5000ms eşiği,50,0float baytları `00004842`, `AntiCR` literali, alt/üst limit
push sırası ve GetTickCount/_srand/_rand import kimlikleri kontrol edildi.
Rapor `outputs/FarmexBot_rota_ilerleme_bekleme_kod_kaniti.json`.
Bu statik Ghidra/disk kanıtıdır; REA Evidence değildir. Önceki auditlerle
örtüşen kayıtlar benzersiz talimat veya tam fonksiyon sayısı değildir.

19 yeni test dahil ilerleme/hareket/çıkış için60 ilgili test geçti. Tam Python
kontrolünde **2084 test geçti (6.958 saniye)**. Count
sarılması, iki taze indeks, tekrarlanan flag'ler, tam QWORD saat, ayrı damga
saati, helper dönüşü, AH greater/equal/less/unordered, RNG gap/çatışması ve
alt hareket modelindeki eksikler sınandı. UI ve native kaynak değişmedi;
bu aşamada UI smoke/native fixture tekrarlanmadı. API henüz rota ekranına
bağlı değildir. Entry, satır yürütücüsü ve yardımcı etkileri ile canlı
uyumluluk açık kalır.
