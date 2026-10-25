# TP koruma ayarı ve gelen27 olayı

`teleport_protection.py`, Koruma bölümündeki üç TP kontrolünün kaynak üretimini ve004d82a4 içindeki sınırlı27 olay dalını modeller. Bellek yazımı, oyun durdurma, bağlantı kesme veya başka oyun süreçlerini kapatma yürütülmez. Planlardaki çağrı ve adresler yalnız kanıt tanımlayıcısıdır.

## Ayarın üretimi

Üç panel callback'i561f55 gate'i üzerinden5690f8 context'iyle0046b928'e gider.607 instruction'lık bu üreticinin yalnız0046c0e1..0046c134 arasındaki19 instruction'ı burada modellenir; öncesinin tamamlandığı açık giriş gözlemidir.

chtpkontrol, form alanıB0C getter AL'sini context+B0'a yazar. rdtpkontrolstop, form alanıB10 getter AL'si nonzero ise context+B4'e1, aksi halde2 yazar. DC radio'suB14 bu bölümde ayrıca okunmaz. İki radio daFalse olduğunda “işlem yok” sonucu uydurulmaz; kaynak yine2 yazar. İki radioTrue ise stop seçimi önceliklidir. Ham üretici AL2 gibi değerleri BYTE2 olarak korur; own bool panel derleyicisi bunun ayrı sınırlı politikasıdır.

##27 olayının koşulları

Olay modeli004d88e4 girişinden başlar. Önceki packet handler guard'ları veya nesne/pointer kimliği tamamlanmış sayılmaz. Own packet bayt0 değeri27 değilse sonraki kaynak bölümü004d8a98'e ilerlenir.27 ise bayt2 alanı ayrı oyun durumu okuyucularıyla karşılaştırılır. Bu kontrol yalnız herhangi bir koordinat farkına indirgenmez.

1. Bayt2 nonzero ise ilk0046209c EAX sonucu okunur. TamEAX bayt2'den farklı ve562251 bayrağı nonzero ise ayrı bir0040ae0c(561f34,0) durdurma çağrı yolu vardır. Bu, TP enable kutusundan önceki bağımsız koşuldur.
2. GetTickCount sonucu sıfır genişletilip561f74/561f78 zaman damgasından64 bit SUB/SBB ile çıkarılır. İşaretli fark10000 ms'den küçükse TP eylem bölümüne girilmez; olayın sonraki alt tür kontrolleri yine çalışır. Negatif farkDWORD sarma süresi gibi ele alınmaz.10000 eşitliği bölüme girer.
3. İkinci, taze0046209c tamEAX sonucu packet bayt2'ye eşitse ANSI bildirim kurma/gösterme/temizleme aralığına ulaşılır. Bu aralık ayrı normal dönüş gözlemidir; string/CRT etkileri emüle edilmez. Sonrasında56209c bayrağı1 yazılmış olarak planlanır.
4. Ancak bundan sonra5691a8 TP enable baytı okunur. Nonzero ise5691ac DWORD değeri1 olduğunda durdurma yardımcısı çağrılır. Ardından aynı DWORD yeniden okunur; bu taze değer2 olduğunda004c7e0c(561ef8) bağlantı kesme yardımcısı çağrılır. Bunlar `if/elif` değildir. Önceki yardımcı/global değişimleriyle bir olayda iki yol da ulaşılabilir olabilir; model bunu ayrı gözlemlerle korur.

56209c, ayrıca durum mesajı seçiminde okunan global alanla aynıdır ([SESSION_STATUS_SELECTION.md](SESSION_STATUS_SELECTION.md)). Aynı adresin iki kaynakta kullanılması statik bağdır; flag'in bütün oyun anlamını veya canlı eşzamanlılığını kanıtlamaz.

## Olayın sonraki alt türleri

Packet bayt1=3 olduğunda üçüncü taze0046209c sonucu okunur. TamEAX bayt2'ye eşit değilse561f6e ve561f70 baytları1 yazılmış olarak planlanır. Bayt2=5c ve5691b0 açıksa5691b2'ye göre0046d66c veya0046dc5c yardımcı çağrı yolu vardır. Bu yardımcıların çoklu oyun etkileri burada opak kalır; hiçbir süreç kapatılmaz. Bu alt bölüm10 saniyelik TP kapısının dışında da ulaşılabilir.

Bayt1=2 olduğunda561f70 sıfırlanır. Normal27 dalı004d8a84'teki EAX=1/SEH sonlandırma bölümüne ilerler. Model bütün1123 instruction'lık packet handler'ın dönüşünü veya exception teslimini sertifikalandırmaz. Own packet baytları sabit bir anlık görüntüdür; kısa tamponlar kaynakta güvenli reddediliyor sayılmaz, modelde desteklenmeyen aralık olarak durur.

004c7e0c'nin19 instruction'ı ayrıca incelendi: global5475a0 baytını yerel temporar­y'ye kopyalayıp4c7710'a uzunluk1/gecikme0 ile gider. Diskteki bayt00'dır; çalışma anında değişmediği veya gerçekten bağlantıyı kestiği kanıtlanmadı. Bu yardımcı modelde opak normal çağrı olarak kalır; disk baytı canlı gönderim sonucu sayılmaz.

## Doğrulama

Dört yeni REA çıktısı eski/güncel sabit Richard görüntüleriyle eşleştirildi. Üretici607, olay handler'ı1123, üç callback14'er ve DC yardımcı19 instruction içerir: iki sürümde3582 kayıt byte doğrulandı. Modellenen19+117 instruction bölümlerinin272 kaydı bu toplamın içindedir; yeni benzersiz kapsam diye ayrıca eklenmez. Fonksiyonların başka bölümleri önceden modellenmiş olduğundan bu aşama fonksiyon sayısını artırmaz.

12 yeni test;10000 sınırı, negatif zaman, ilk/ikinci/üçüncü EAX farkı, yeniden okunan işlem alanı, iki durdurma yolu, enable öncesi bildirim, alt tür bayrakları, jail yardımcı ayrımı, eksik normal dönüşte korunmuş önek ve kısa paket sınırını denetler. Arayüz değişmedi; bu API henüz Koruma paneli denemesine/gerçek incoming dispatcher'a bağlanmadı. Native ve canlı uyumlulukFalse kalır.

Kanıt: `outputs/FarmexBot_TP_koruma_kod_kaniti.json`; denetim: `work/audit_teleport_protection.py`.
