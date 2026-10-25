# 32 bit HP/MP okuma bileşeni

17 Ekim copied-worker biçimi: `build_suspended_bootstrap_fixture.ps1 -CopiedWorker`, kendi derlenen kodunu statik sınır/fixup denetimiyle çıkarır ve yalnız kendi oluşturduğu hash-pinned child'da kullanır. Normal attach/IPC/detach ve `-RejectImage` sabit negatif referans kontrolü geçti. Generic PID/DLL girişi veya Game yükleme değildir. Kapsam ve kanıt: [COPIED_WORKER.md](../COPIED_WORKER.md).

17 Ekim transfer biçimi: `build_suspended_bootstrap_fixture.ps1 -TransferImage` yalnız own-child'a pinned kendi DLL headers/section'larını taşır. Child'a gelen allocation tam mapped-image karşılaştırmasından sonra hazırlanır; genel DLL/PID yükleyicisi değildir. Olumlu aktarım, gömülü regresyon ve hedef dosya kimliği negatif kontrolü geçti. Ayrıntı: [TRANSFERRED_BOOTSTRAP.md](../TRANSFERRED_BOOTSTRAP.md).

17 Ekim askıda own-child kontrolü: `build_suspended_bootstrap_fixture.ps1` ayrı parent ve hash-pinned kendi child'ını üretir. Parent sadece kendi yarattığı child'a bootstrap thread'i açar; child kendi gömülü DLL'imizi başlatır. Sentetik frame, ana-thread resume ve cleanup zinciri geçti. Mevcut PID/Game hedefi veya genel remote-image yükleyicisi değildir. Kapsam ve kanıt: [SUSPENDED_BOOTSTRAP.md](../SUSPENDED_BOOTSTRAP.md).

## Windows yükleyicisi olmadan kendi DLL başlangıcı

`local_bootstrap_fixture.c` derlemede içine gömülen tek ve SHA256 ile sabitlenmiş kendi DLL'imizi, kendi sürecinin özel bellek alanında başlatır. 116 relocation/43 import ve 32 bit yayıncıdan 64 bit salt okunur okuyucuya sentetik veri aktarımı doğrulandı. Bu kaynak hedef PID veya çalışma anında DLL yolu kabul etmez. Oyun yükleme ve canlı uyumluluk kapsam dışıdır. Derleme sınırları, özgün işçiyle karşılaştırma ve gerçek çalışma kaydı için [NATIVE_BOOTSTRAP.md](../NATIVE_BOOTSTRAP.md).

## DLL yaşam döngüsü doğrulaması

16 Ekim 2026: `lifecycle_fixture_host.c` ile kendi x86 programımızda Windows `LoadLibrary`/`FreeLibrary` yaşam döngüsünün 12 kontrolü geçti. İlk yükleme kendiliğinden yayın başlatmıyor; açık yayın çağrıları sequence 2 ve 4 üretiyor. İki kez kapatma, kapattıktan sonra yeniden yayın, DLL ayrılırken paylaşım alanının temizlenmesi ve yeniden yüklemede kritik bölümün yeniden hazırlanması doğrulandı.

Salt okunur bir okuyucu tutamacı eski paylaşım alanını yaşatırken DLL yeniden yüklendiğinde yayıncı status 11 döndürüyor ve eski çerçeveyi koruyor. Son okuyucu tutamacı kapatıldıktan sonra aynı adla yayın yeniden başlayabiliyor. Dolayısıyla yeniden yükleme sırasında eski okuyucuların kapanması gerekiyor. Okuyucu bu testte aynı test programının tuttuğu tutamaçla temsil edildi; ayrı süreçler arasındaki aktarımın önceki testi aşağıda belirtiliyor.

`build_lifecycle_fixture.ps1` ayrı bir çıktı klasöründe derleme yapar. Çalışma kaydı `../FarmexBot_native_yasam_dongusu_testi.json` dosyasındadır. Bu doğrulama Windows yükleyicisini kullanır; orijinal botun elle PE yükleme yöntemini, oyuna yüklemeyi veya canlı oyun alanlarını doğrulamaz. Aşağıdaki önceki test sayıları kendi kapsamlarıyla korunmuştur.

16 Ekim güncel uyarlama: Üretim okuyucusu hem önceki7009936/adeccdc6…700a hem yeni7008392/ca69cece…952a9 disk kimliğini ayrı tabloyla destekler. Yeni US root0x11289c0,Steam0x11e9638;iki yeni profildeMP0xd60/max0xd5c. Kaynak initializer operandları doğrulandı;canlı alan/ABI doğrulanmadı. Yeni own-host19vaka geçti;FarmexObserveRefreshedFixture yalnız kendi farmex_probe_host.exe hostunda çalışır. ABI52bayt/sürüm1 kaldı. Aşağıdaki önceki test kayıtları tarihsel kapsamları belirtir.


16 Ekim2026 güncel disk kontrolünde oyun kimliği değişti:7008392 bayt/ca69cece…952a9. Bu native bileşenin7009936/adeccdc6…700a kimliğiyle eşleşmiyor. Python okuyucu da artık aynı kimlik kapısını uygular. Güncel offset/ABI doğrulaması yapılmadı; oyun kopyası yalnız statik analiz için korundu. Bu kaynakların önceki test sonuçları kendi fixture kapsamıdır.


vitals_bridge.c yalnız çalıştığı sürecin belleğini okur. FarmexObserve kendi süreç yolunu ve x86 PE özelliklerini denetler; US/Steam aday tablosuyla karakter kökü ve dört HP/MP DWORD alanını, ardından kökü tekrar okur. En fazla 24 veri baytı okunur. Sonuç 52 baytlık sürüm 1 C ABI kaydıdır. Başarılı okuma aday veri anlamına gelir; bağımsız canlı doğrulama değildir.

FarmexObserveFixture yalnız farmex_probe_host.exe adlı kendi test programımızda kullanılabilir. probe_host.c sentetik US/Steam verilerini ve hata durumlarını sınar. DLLMain gözlem başlatmaz. Kaynaklar oyun yükleyicisi içermez. shared_vitals.c ve ../native_ipc.py tek yönlü veri aktarımını kendi test programımızda sağlar. Uygulamanın bağlantı sayfası hazır yayıncıyı okuyabilir; gerçek oyun bağlantısı henüz kurulmadı.

Derleme TinyCC 0.9.27 Win32 ile yapıldı. Derleyici pakete dahil değildir. PowerShell örneği:

```powershell
.\build_native.ps1 -CompilerPath 'C:\tools\tcc\tcc.exe' -OutputDirectory 'C:\work\native-build'
```

Yerel doğrulamada sekiz vaka geçti: US, Steam, yanlış üretim süreci, geçersiz kök, okunamayan kök slotu, tutarsız HP, geçersiz profil ve kısa çıktı alanı. Kanıt üst klasördeki FarmexBot_native_salt_okuma_testi.json dosyasındadır. Test oyunu seçmedi; DLL oyuna yüklenmedi. Üretim PE kapıları, kökün eşzamanlı değişmesi ve gerçek oyun alanları bu testle doğrulanmadı.

HP/MP üretim bileşeni bellek alanlarından önce Game dosya boyutu 7009936 ve SHA256 adeccdc66814422e47ffc66b9a5659a2f9487aad6d4a5289a78261d94a3e700a kontrolünü uygular. image_identity.c Windows CNG ile diskten hashler; build_native.ps1 vitals_bridge.c, image_identity.c ve shared_vitals.c dosyalarını birlikte derler. Status 8 kimlik uyuşmazlığı, 9 hash/okuma hatasıdır; ABI 52 bayt/sürüm 1 değişmedi. Bu bileşende oyun alanlarına bellek yazımı, başka süreç açma, koruma değişimi, hook, oyun eylemi veya ayrıcalık değişimi uygulanmaz. Disk kimliği canlı alan/ABI doğrulaması değildir.

## Tek yönlü HP/MP aktarımı

shared_vitals.c açık çağrıyla 84 baytlık sürüm 1 çerçevesini kendi paylaşımlı belleğine yazar. Harita adı kendi PID'sini ve 32 küçük hex karakterlik oturum değerini içerir. Önceden var olan harita üzerine yazılmaz. Kritik bölüm yayıncıları sıraya koyar; tek/çift sequence ve InterlockedExchange tamamlanmamış çerçeveyi ayırır. DLLMain otomatik örnekleme veya oyun yükleme başlatmaz.

../native_ipc.py yalnız FILE_MAP_READ ile bu çerçeveyi okur. Boyut, sürüm, iki PID alanı, profil, kaynak türü, sequence, veri tutarlılığı ve zaman aşımını denetler. Sentetik kaynak fixture_candidate, oyun adayı candidate_unverified döner; independently_verified her durumda false kalır. PID ve harita adı tutarlılığı, haritayı oluşturan sürecin kimliğini doğrulamaz.

build_ipc_fixture.ps1 kendi 32 bit test yayıncısını derler. 64 bit Python okuyucusuyla 15 vaka geçti: US/Steam verisi, okuma hatası, yarım/bozuk/eski çerçeve, yanlış kimlik/profil/kaynak, eşzamanlı yayın, yanlış süreç, geçersiz ad ve mevcut haritanın korunması. Kanıt ../FarmexBot_native_IPC_dogrulama.json. Bu test gerçek oyuna DLL yükleme, oyun alanı doğrulaması veya oyun eylemi içermez.

NativeVitalsProvider açık PID, oturum değeri ve profil ile tek örnek alır; haritayı işlem sonunda kapatır. Bağlantı sayfasında “Hazır yayıncıdan HP/MP al” seçeneği ve sentetik kaynak seçimi vardır. İki gerçek test yayıncısıyla US/Steam HP/MP değerlerinin gizli arayüze ulaşması doğrulandı. fixture_candidate canlı oturum gözlemine dönüştürülmez; candidate_unverified bağımsız doğrulanmış sayılmaz ve canlı motoru başlatmaz. Yayıncı kaybolduğunda otomatik bellek okumasına veya süreç yüklemeye geçilmez.

FarmexIdentityFixture yalnızownhostta fixed sibling dosyalar veyaexactGame disk dosyasını denetler. Dokuzvaka geçti:empty,abc,wronghash,wrongsize,missing,multichunk,Gamefile,invalidkind,null digest. Bellegin bytes_read sayısı0'dır;dosya okuması ayrıca değerlendirilir. ÖncekiHP/MP sekizarena vakası yeniDLL iletekrar geçti. Kanıt ../FarmexBot_native_dosya_kimligi_testi.json. Oyunprogramı/süreci açılmadı;DLL oyuna yüklenmedi.

## Ayrı çağrı şekli fixture'ı

call_fixture.c kendi32bit hostunda ECX,iki stack argümanı,RET8 veInn PUSHAD/PUSHFD korumasını ölçer. Yalnız kendi callback allocation'ına çağrı yapar;oyun adresi/PID seçme veyaoyun belleğine erişim yoktur. Kendihost belleğinde callback/kayıt yazımı vardır. Dört vaka geçti; gerçek oyun ABI'si doğrulanmadı. Bunlar Python876 veyaHP/MP sekizfixture sayısına eklenmez.

build_call_fixture.ps1 -CompilerPath parametresiyle TinyCCWin32/GCC uyumlu x86 inlineassembler kaynağını derler. Üretilenfarmex_call_fixture.exe dörtJSONsatırı vegeçişte exit0 üretir. Derleyici veEXE kaynakpaketine dahil değildir. Üstklasörde ../FarmexBot_native_cagri_fixture_testi.json kendiortam çalışma kaydıdır.

16 Ekim callback bağlamı: 0046eca8 gövdesinin 12 talimatı eski ve güncel dosyada aynı. Güncel initializer çağrılarına bağlanan ayrı kök-slot adayları US01128a7c/Steam011eaab0 ve 3b0 alan ofseti doğrulandı; bunlar HP/MP kökü değildir. Yeni kendi x86 programımızda beş bağlam/register/stack vakası geçti. Kendi RET0 alıcımızla ECX aktarımı, EBX/EBP korunması ve stack dengesi ölçüldü. Gerçek oyun alıcısının ABI'si ve etkileri doğrulanmadı. Oyun süreci açılmadı, oyuna okuma/yazma veya modül yükleme yapılmadı. Önceki 1554 Python/UI ve 19 native HP/MP/disk-hash sonuçları ayrı test kapsamları olarak kalır.
