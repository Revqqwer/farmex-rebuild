# Rota katalog sonlanması ve tarama hatası

18 Ekim2026. Önceki own adapter OS hatasında eski rota seçeneklerini
koruyordu. Bu, doğrulanmış kaynak normal-akışıyla farklıydı; açma/okuma
sonlanmaları artık ayrı modellenir.

Richard4e93d8, vector reset span'ından sonra opendir çağırır. Null pointer
doğrudan cleanup'a gider; readdir ve closedir çağrılmaz. Nonzero pointer
yolunda readdir-null döngüyü bitirir ve closedir çağrılır; sonucun EOF mu
okuma hatası mı olduğu errno ile sorgulanmaz. 4e96d4 devamında combo Clear
ve eldeki vector'e göre öğeler/boş-count placeholder gelir. Full native
reset/insert/RTL/helper etkilerinin tamamlandığı iddia edilmez.

`work/audit_route_dropdown.py`, reset-before-open, null-open jump'ın
readdir/closedir span'ını atlaması ve read pointer loop jump'ını iki sürümde
yeniden denetler.1196instruction kaydı aynı kapsamda doğrulandı; eklenen
anchor denetimleri yeni/benzersiz instruction sayısı olarak eklenmedi.

`plan_route_catalog` artık yalnız display projection'ın bitişini ve sağlıklı
entry enumeration bilgisini ayırır:

| Gözlem | complete | enumeration_verified | Gösterilen |
|---|---|---|---|
| Sağlıklı own iterator sonu |True|True|Eşleşen adlar veya placeholder|
| Bilinen open_failed |True|False|Placeholder|
| Bilinen read_stopped, hata |True|False|Okunmuş eşleşmeler veya placeholder|
| Yalnız prefix, sonlanma bilinmiyor |False|False|Prospective prefix, commit yok|
| Conversion receipt/metni eksik |False|Ayrı supplied bilgi|Commit yok|

`complete=True` burada bilinen sonlanmaya göre katalog görünümünün
oluşturulabildiğini söyler; dizinin eksiksiz veya oyun uyumluluğunun
doğrulandığı anlamına gelmez. open_failed ile entry veya healthy enumeration
verilmesi çelişki olarak reddedilir. read_stopped tek başına healthy EOF
kanıtı değildir. Mevcut enumeration_complete fixture interface'i korunur.

Yerel adapter yalnız `os.scandir` açma ve `next` OS hatalarını karşılık gelen
sonlanma politikasına eşler. Python exception'ları gerçek CRT pointer
gözlemleri gibi sunulmaz; native handle veya pointer üretilmez. Hata metni ve
scandir_open/scandir_next aşaması result'ta korunur. Mid-scan hata önceki
katalog yerine yalnız bu geçişteki eşleşen adları gösterir. Iterator hem
normal dönüşte hem budget/codec hatasında context manager ile kapatılır.

Kendi paneli başarısız açmada placeholder'a geçip seçimi-1yapar; mid-scan
kesilmeyi ayrı metinle gösterir. Son deneme hata öncesi başarılı bir tanıyla
karışmaz: route_catalog_last her denemede yenilenir, çözülmemiş conversion/
budget exception'ında None kalır. Bunlar native window/helper etkisi değildir.

Altı yeni test normal EOF,open failure,read failure/empty prefix,unknown
prefix,çelişik input,budget/codec ve iterator cleanup ayrımlarını sınar.
Gizli UI testi eksik klasörde eski katalog temizliği/placeholder/seçim reset'i,
read-error prefix gösterimini ve unresolved dönüşümde stale-result temizliğini denetler. Codec/bütçe/RTL
istisna etkileri, CRT vs Python file enumeration eşdeğerliği ve native/live
uyumluluk hâlâ açıktır. Oyun belleği/native eylem yapılmadı.
