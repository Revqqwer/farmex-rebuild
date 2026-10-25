# Gerçek Flood listesinden byte kayıtları

`flood_compilation.py` gerçek `lwFlooding` satırlarını immutable bir snapshot'a alıp kendi `MessageListRow` kayıtlarına derler. Kaynak üretici `0045c488` ve iki Text helper'ının dosya baytlarıyla eşlenen değer akışı uygulanır: caption→kanal, subitem0→mesaj, subitem1→gecikme. Checked alanı filtre değildir; sıra korunur. Ekstra sütunlar kullanılmaz.

Gecikme scalar RTL modeli ve bağımsız default10 politikasından alınır, düşük DWORD1000ile çarpılıp32bite sarılır. Ekleme düğmesinin minimum5 kuralı derleyiciye taşınmadı: profilden gelen0/negatif/4gibi satırlar da bu üreticinin değer akışına girer. Code hatalıysa kısmi parser sonucu kullanılmaz. Hex ve embeddedNUL sayı davranışları önceki scalar kanıtın sınırları içindedir.

Kanal/mesaj dönüşümü bu Windows host'unda ölçülen açık GetACP kod sayfasıyla `WindowsNameCodec` flags0 kullanır. Her sonuç byte dizisi ve used-default bilgisiyle tutulur. UTF8'de used-default bilgisi None'dır. Unicode mesajların native RTL cached/default codepage'i, best-fit/error politikası ve oyundaki encoding nesnesiyle eşlik **doğrulanmadı**. Dönüşüm gerçek Windows API çağrısıdır; orijinal bot helper'ı çalıştı veya normal döndü diye sahte receipt oluşturulmaz.

Bağımsız konteyner O(n) çalışır; yerel64satır sınırı yoktur. Source vector pointer/capacity/heap/SEH taklidi yapmaz. Eksik mesaj/gecikme sütunu veya conversion hatasında tamamlanmış prefix ve gerçekleşen conversion metadata'sı kalır; uydurma boş satır/ANSI eklenmez. `complete` yalnız bu kendi snapshot derlemesini tanımlar. Eksik native subitem/exception yolu çözülmüş sayılmaz.

Panel Ekle başarılıysa, Sil/Temizle çağrısından sonra (liste zaten boş/seçim yok olsa da), genel liste editörünün Uygula eyleminde ve profil bağlamasında yeniden derler. Aktif/timestamp/index state'i eklenmedi veya sıfırlanmadı. `current_flood_compilation()` yalnız hem mevcut satırlar hem kod sayfası snapshot ile eşleştiğinde sonucu verir. Harici liste değişikliği, profil yükleme veya kod sayfası değişimi eski sonucu güncel diye sunmaz. Eksik derleme açık completeFalse olarak kalır.

Bu aşamada yalnız gerçek liste path'i compiler inventory'ye eklendi:379girdi,144envanter dışı editable path. Ekleme formunun3alanı hâlâ dolaylı editor girdileridir; sayıyı artırmak için ayrıca eklenmedi.1yeni doğrudan liste bağlantısı, tüm Flood özelliğinin veya gerçek gönderimin tamamlanması değildir.

10 yeni Python testi: byte/sıra/Checked,default10 ve ms wrap,producer'da min5 olmaması,NUL/UTF8 metadata,eksik hücre/codec prefix'leri,stale/type sözleşmeleri,1000satır ve bağımsız captured `MessageListFrame` sonucuyla değer karşılaştırması. Gizli gerçek widget testi CP1254/Türkçe bytes, stale liste/kod sayfası reddi, malformed profile prefix ve profil yeniden derlemeyi kapsar. Native VCL/vector/codec eşliği, zaman worker'ı, toggle/seçileni yaz ve oyun sender bağlantısı hâlâ açıktır.
