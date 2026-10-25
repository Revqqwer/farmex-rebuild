# Oyun yükleme yolu için erişim metadata'sı

16 Ekim 2026 16:11 UTC: güncel oyun PID19216ve tam `C:\NTTGame\KnightOnlineEn\KnightOnLine.exe` yolu yeniden doğrulandı. Disk7008392bayt, SHA256 `ca69cecebdefd82b409ca8cf041655da53cb97113b068a086c5f7a6ef7e952a9` ile eşleşti. Gözlemci yönetici değildi. Bu kayıt önceki yönetici testinin yerine geçirilmez.

| İstek | Maske | Mevcut yetkide oyun sonucu |
|---|---|---|
| Sınırlı bilgi | 1000 | Handle açıldı, verilen maske1000 |
| Bellek okuma | 10 | OpenProcess hata5 |
| Adres alanı işlemi | 8 | OpenProcess hata5 |
| Bellek yazma | 20 | OpenProcess hata5 |
| Thread oluşturma hakkı | 2 | OpenProcess hata5 |
| 2+8+20 alt kümesi | 2a | OpenProcess hata5 |
| Alt küme + query information | 42a | OpenProcess hata5 |
| Belgelenen remote-thread hak kümesi | 43a | OpenProcess hata5 |

Tablodaki maskeler hexadecimal'dir. Hata5ile handle açılmaması, açılan handle'da verilen maskenin0olması ve metadata'nın bilinmemesi ayrı durumlardır. Kendi süreç kontrolünde aynı sekiz istek açıldı; istenen bitler gözlendi ve üretim `query_granted_access` sonucu tanı yardımcısıyla aynıydı. Kontrol oyuna erişimin başarılı olduğu anlamına gelmez.

[Microsoft CreateRemoteThread belgesi](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createremotethread), CREATE_THREAD, QUERY_INFORMATION, VM_OPERATION, VM_WRITE ve VM_READ haklarını belirtir; bu beşli43aeder. [Erişim hakları tablosu](https://learn.microsoft.com/en-us/windows/win32/procthread/process-security-and-access-rights) bitlerin anlamını verir.2a/42aayrı tanı alt kümeleridir;43ayerine garantili bir yükleme yolu olarak sunulmaz. Bütün haklar verilse bile gerçek başlangıç adresi, yüklenen kod/ABI ve çağrı sonucu ayrıca doğrulanmalıdır.

## Yönetici ölçümünün sınırı

Önceden kullanıcı tarafından onaylanan salt metadata tanısının `--admin` biçimi ayrı bir defalık dosya kullanır. Yönetici token'ı, tek PID, tam yol ve disk kimliği kapıları geçilmeden oyun hakları sorgulanmaz.16:14 UTC kontrolünde Windows başlatıcısı henüz child PID/sonuç döndürmemişti. Sonraki terminal sonucu `launch_failed / İşlem kullanıcı tarafından iptal edildi` oldu; child PID dönmedi ve yönetici ölçümü tamamlanmadı. Başlatma artık bekleyen bir işlem değildir. Bu Windows başlatma iptalidir; otomatik araç onay incelemesi reddi veya oyun handle erişim sonucu değildir. Otomatik tekrar başlatılmadı.

Önceki14:48 UTC yönetici testinde VM_READ için açılan handle'ın verilen maskesi0ölçülmüştü. O test yazma/işlem/thread maskelerini istemedi; yeni tablonun yönetici sonuçları gibi kullanılamaz. İki zaman/bağlam ölçümü farkının bütün nedeni tespit edilmiş değildir. Belirli bir anti-cheat, driver veya DACL nedeni kanıtlanmış sayılmaz.

## Yürütülen işlemler ve kanıt

`work/probe_loader_access_metadata_once.py`, yalnız süreç envanteri, kendi token metadata'sı, tam image path/disk hash'i, hedefin çıkış durumu ve açılan handle'ın verilen haklarını sorgular. Hak istekleri bunları kullanarak işlem yapmak için kullanılmadı. Oyun bellek değeri okuma/yazma, uzak allocation, uzak thread, modül yükleme, koruma ve privilege değiştirme sayıları0dır. UAC'yi kullanıcı onaylar; onay otomatik verilmez.

Ham normal-yetki kaydı üst çıktı dizinindeki `FarmexBot_yukleme_erisim_haklari_19216_once.json` dosyasıdır. Yönetici kaydı varsa ayrı `FarmexBot_yukleme_erisim_haklari_admin_19216_once.json` dosyasıdır. `work/finalize_loader_access_metadata.py`, yalnız tamamlanmış/gated kayıtları sınıflandırıp `FarmexBot_yukleme_haklari_karsilastirma.json` üretir; eksik yönetici kaydından ret veya başarı çıkarmaz.

Başlatma iptalinin ayrı kaydı `FarmexBot_yukleme_admin_baslatma_iptali.json` dosyasındadır. Bu kayıt bir erişim testi olarak tabloya eklenmez.16 Ekim normal-yetki ölçümü tarihseldir; daha sonra açılmış olabilecek yeni bir oyun oturumunun hakları gibi sunulmaz.

Kendi DLL'imizin kendi hostumuzda PE başlangıcının çalışması, bu oyun handle haklarını sağlamaz. Orijinal Loader'ın askıda süreç yaratma/aktarma/attach zinciri ile sonradan çalışan oyuna OpenProcess denemesi de aynı çalışma anı değildir. Mevcut oyun kapatılmadı veya yeniden başlatılmadı; bu iki başlangıç durumunun güncel oyun üzerinde eşdeğerliği denenmedi. Gerçek oyun bağlantısı ve canlı uyumluluk açık kalır.
