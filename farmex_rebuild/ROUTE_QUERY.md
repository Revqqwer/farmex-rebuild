# Rota aday sorgusu

Güncelleme: İsim helper'larının normal liste tarama caller'ı artık
[SOURCE_NAME_FILTER.md](SOURCE_NAME_FILTER.md) içinde modellenmiştir.
Query optional typed primary/secondary planları kabul eder; ayrı normal
dönüş gereksinimi sürer. Aşağıdaki ilk aşama sonuçları tarihseldir; helper
boşluğu liste üretimi, gerçek conversion/RTL ve native etkilerle daralmıştır.

18 Ekim 2026. `route_query.py`, 0046cfcc normal çağrı akışının yerel modelidir.
İki sabitlenmiş modülde sorgunun 265, referans yardımcılarının 11 ve 17
talimatı disk baytlarıyla doğrulandı: toplam 586 kayıt. Kaynak rapor
`outputs/FarmexBot_rota_aday_sorgu_kod_kaniti.json`; üretici
`work/audit_route_query.py`. Bu, saklanan Ghidra çıktısı ve disk doğrulamasıdır;
REA Evidence kaydı veya canlı yürütme kanıtı değildir.

Her çağrı üç çıktı baytını sıfırlar. Önbelleğe alınan 00462650 tam DWORD
sonucu ve string başlangıcı ayrı gözlemlerdir. Tarama 0..3000 dahil sırayla
gider. Null aday atlanır; hiçbir eksik gözlem null aday sayılmaz. Üç çıktı
1 olsa bile tarama ve son Unicode cleanup normal dönüşü gerekir.

Null olmayan adayda üç guarded DWORD okuması WORD'e kesilir. X/Y float
getter dönüşleri, metric/__ftol sonucu ve karşılaştırma AH baytları ayrıca
verilir. Model sayıdan FPU sonucunu uydurmaz. Context39 etkinse durum
alanı iki ayrı taze okumayla 4 ve 5 için sınanır; metric önce çalışmıştır.
İsim uzunluğu 16'dan küçükse inline, aksi halde guarded dolaylı pointer
kullanılır. Her iki yol tam WORD uzunluğunu kopyalar; 255 varsayılmaz.
İsteğe bağlı `QueryNameCapture` açık codec ve yakalanmış baytlarla mevcut
yerel kopyalama modelini kullanır. Codepage/taşma boşlukları durdurulur.

İsim span'ı tamamlandıktan sonra aday WORD4040 ile önbellekteki **tam DWORD**
karşılaştırılır. Eşitse atlanır. 004626b0 sonucu da tam DWORD'dur. Opsiyonel
00462690 sonuç dizisi ilk okuma 1 ise 2 üretir; aksi halde ikinci **taze**
okuma 2 ise 1, değilse 0 üretir. Bunlara ulus anlamı atanmış değildir.

WORD3fdc farklıysa anti yarıçap karşılaştırmasında TEST AH,5 sıfır olmalı;
birincil isim helper AL0 çıktı0, ikincil ALnonzero çıktı2 yapar. Eşitse
context8 yarıçapı anti/enemy arasından seçer. Birincil AL0 yolunda ayrı
anti karşılaştırması çıktı0'ı belirler; çıktı1 bu ikinci karşılaştırma
başarısız olsa da 1 olur. İkincil sonuç bağımsızdır. Çıktılar yalnız 0→1
olur; tekrar yazımlar izde korunur.

`RouteEntryObservation.query_execution` isteğe bağlı typed planı kabul eder.
Ulaşılan çağrıda ham output override ile karıştırılamaz. Bilinen yarıçaplar
çağıranın gerçek parametreleriyle eşleşmelidir. Kısmi plan, çıktıları111
olsa da giriş zincirini ilerletmez. Tam plan da ayrı `query_returned=True`
gereksinimini kaldırmaz. Ulaşılmayan plan çağrılmış sayılmaz.

23 yeni test dahil tam 2258 test geçti (7.980 saniye); sorgu/giriş/callback
odaklı 52 test de geçti. UI/native kod değişmedi, bu aşamada UI/native test
tekrarlanmadı. Mevcut ekran aracı Genel panelini başarıyla yakaladı; bu
orijinal panel gözlemidir, kendi modelimizin canlı uyumluluğunu kanıtlamaz.

0046c1a0 ve 0046c2ac isim süzgeçlerinin iç mantığı, gerçek FPU/helper
yürütmesi, string runtime/exception/concurrency ve canlı oyun bağlantısı
açıktır. Bu API yalnız sağlanan gözlemlerle yerel plan üretir; oyun belleği
okumaz/yazmaz, orijinal modül çalıştırmaz ve oyun eylemi gerçekleştirmez.
