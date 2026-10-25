# Kendi askıda sürecimizde başlangıç kontrolü

Sonraki transfer kontrolü: `-TransferImage` biçimi own-parent'ın başlık+üç section'ı own-child'a dört başarılı kopyayla aktarmasını ekler. Child gelen tam bellek görüntüsünü doğrular ve onu başlatır. Aynı zamanda gömülü biçimin regresyonu ve dosya-kimliği ret kontrolü geçti. Ayrıntı: [TRANSFERRED_BOOTSTRAP.md](TRANSFERRED_BOOTSTRAP.md). Aşağıdaki ilk deneyin “parent image kopyalamaz” kapsamı varsayılan gömülü biçime aittir.

17 Ekim 2026 00:17 İstanbul / 16 Ekim21:17UTC: kendi x86 parent/child programlarımızda başlangıç zinciri başarıyla tamamlandı. Bu, oyun üzerinde bir yükleme değildir; var olan oyun kapatılmadı veya yeniden başlatılmadı.

## Çalıştırılan zincir

`native/suspended_bootstrap_parent.c`, yalnız kendi dizinindeki `farmex_probe_host.exe` programını oluşturabilir. Mevcut PID veya başka program yolu kabul etmez. Child derlenince SHA256, boyut, image base ve tek bootstrap export RVA'sı parent'ın oluşturulan başlığına sabitlenir. Parent yürütmede child dosyasını yazmaya kapalı bir read handle ile tutar, CNG SHA256 eşleşmesini denetler ve sonra `CREATE_SUSPENDED | CREATE_NO_WINDOW` ile kendi child'ını yaratır.

Başarılı çalışma sırası:

1. Child kendi Job Object'ine alındı; parent kapanırsa yalnız bu child'ın kapanmasını sağlayan kill-on-close sınırı kullanıldı.
2. CreateProcess'ten dönen handle'ın verilen maskesi `0x1fffff`, aynı kendi child'ı için sonradan açılan `0x43a` isteğinin verilen maskesi `0x143a` gözlendi. İstenen bitler iki handle'da da vardı.
3. Sabit own-child image base `0x400000`, MEM_IMAGE/allocation-base metadata'sıyla doğrulandı. Bootstrap entry'si bu sabitlenmiş kendi EXE'mizin export adresidir.
4. Bir remote thread **yalnız kendi yeni child'ımızda** bu export'u çalıştırdı. Child içine gömülü, SHA256 ile sabitlenmiş kendi DLL'imiz child'ın özel belleğinde önceki PE hazırlayıcıyla başlatıldı. Arbitrary DLL veya uzak görüntü baytı girişi yoktur.
5. Remote helper exit0döndü. Child'ın kendi `main` gövdesinin işareti hâlâ gelmemişken 84 baytlık sentetik HP/MP çerçevesi FILE_MAP_READ ile alındı: HP250/500, MP100/300, sequence2, kaynak FIXTURE ve producer PID child ile eşleşti.
6. Ana thread `ResumeThread` ile devam ettirildi; önceki suspend sayısı1olarak döndü. Child'ın main gövdesi hazır işaretini gönderdi.
7. Parent okuyucusu kapandıktan sonra bırakma event'i verildi. Child kendi DLL'ini kapattı, exit0ile bitti; paylaşımlı harita artık bulunamadı. Parent da exit0ile bitti.

Bu test çocuk `main` gövdesinin henüz çalışmadığını gösterir. Windows loader/TLS/DLL initialization'ın hiç çalışmadığını veya bir oyun korumasının henüz başlamadığını göstermez. İşletim sistemi başlangıç kodu ve child main ayrı aşamalardır.

## Kapsam ve sınırlar

`local_bootstrap_fixture.c`, `FARMEX_SUSPENDED_CHILD` derleme seçeneğinde bu export/child-main yolunu sağlar. Önceki varsayılan yerel-host yolu kaynakta korunur. Child yalnız kendi DLL'inin fixture API'sini çağırır; gerçek HP/MP veya oyun process API'si çağrılmaz.

Parent kendi child'ına PE görüntüsü kopyalamaz; remote WriteProcessMemory/VirtualAllocEx yolunu bu testte yeniden uygulamadık. DLL child'a derlemede gömülüdür ve kendi allocation/import/entry hazırlığı child içinde yapılır. Dolayısıyla orijinal Loader'ın bütün aktarma mekanizması, import adreslerinin güncel oyundaki uyumu veya oyun ABI'si bu sonuçla doğrulanmış değildir. Orijinal modülün kendi thread envanterini devam ettirmesi yerine bu kontrolde parent yalnız kendi ana thread'ini devam ettirir.

Parent hedef olarak yalnız CreateProcess'ten aldığı kendi handle'ı kullanır. Başarısızlıkta terminate/cleanup yolu da bu handle ve yalnız ona bağlı job içindir. Mevcut uygulama PID'si seçilmez. Test UAC kullanmadı; token/privilege ayarı değiştirmedi. Kendi child belleğinde allocation/koruma/yayın işlemleri ve bir remote thread vardır; oyun üzerinde bu işlemlerin sayısı0dır.

Kendi child'ımızdaki hakların verilmesi, çalışan oyuna aynı hakların verileceğini göstermez.16Ekim16:11UTC oyun ölçümünde yönetici olmayan gözlemci aynı temel hakları alamamıştı. Yönetici tanısı ise Windows başlatma iptaliyle sonuçlandı; bu yeni test iptali aşmaya veya yönetici oyun sonucunun yerine geçmeye çalışmaz. Ayrıntı: [LOADER_ACCESS.md](LOADER_ACCESS.md).

## Yeniden üretme ve kanıt

`native/build_suspended_bootstrap_fixture.ps1`, CompilerPath, BridgePath, PythonPath ve OutputDirectory parametreleriyle ayrı bir build üretir. BridgePath yalnız kendi DLL'imizin `4510845e33931b26da0381adfa12e414c4ef72d9c0206728952f6ecfe1903c3a` kimliğini kabul eder. `native/prepare_bootstrap_child.py` yeni child'dan parent pin'ini üretir; program çalıştırmaz. Generated header'lar ve EXE/DLL dosyaları kaynak ZIP'ine eklenmez.

`work/verify_suspended_bootstrap.py` tek parent çalışmasını 25saniye dış süre sınırıyla denetler. Parent aşamalarında ayrı 5saniye bekleme sınırları vardır. Her parent build hash'i ayrı kanıt dosyası alır; aynı build sonucu üzerine yazılmaz.

Başarılı parent SHA256 `4f8b69cd95a8257c5d88b1899f00943ac8612f10270d519baea660e09d80d44a`, child SHA256 `0416991e96cdf73ea68d77c8db8291cf68fce59490baba3c2ab41d4078dd5e48`. Çalışma kaydı üst çıktı dizinindeki `FarmexBot_askida_baslangic_4f8b69cd_testi.json` dosyasıdır. Child PID6820, sekizinci aşama, bootstrap/child/parent exit0, önceki suspend sayısı1doğrulandı. Bu tek native zincir, Python birim testi sayısına eklenmez; son1719Python ve UI doğrulaması önceki kendi kapsamıdır ve native-only adımında tekrar çalıştırılmadı.

Gerçek oyun bağlantısı ve bütün özelliklerin canlı uyumluluğu açık kalır.
