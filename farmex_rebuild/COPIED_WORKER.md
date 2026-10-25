# Kopyalanan bağımsız worker kontrolü

23 Ekim ek kanıtı: [özgün431-byte işçi](SOURCE_LOADER_WORKER_NATIVE.md) de yalnız
kendi sentetik görüntümüzde15 native senaryoyu geçti. Bu ayrı yerel deney,
aşağıdaki kendi-child aktarım testiyle birlikte gerçek oyun yüklemesini kanıtlamaz.

17 Ekim 2026. Kendi askıda child'ımıza yalnız DLL görüntüsü değil, bağımsız worker kodu ve bağlamı da aktarıldı. Başlangıç, test child'ındaki resident hazırlama export'una gitmek yerine ayrılan worker-code alanından çalıştı. Hedef hâlâ yalnız parent'ın oluşturduğu hash-pinned kendi child'ıdır; mevcut oyun/PID hedefi veya genel DLL girdisi yoktur.

## Statik kod kapısı

`native/copied_worker.c`, global/string-literal/CRT doğrudan çağrısı kullanmadan yazılmış tek x86 yordamdır. Gerekli Windows API ve DLL fonksiyonları bağlamdaki işaretçiler üzerinden çağrılır. `native/prepare_copied_worker.py`, kendi derlenen şablonumuzdaki iki export sınırından3772baytı çıkarır; bu aralıkta mutlak PE relocation girdisi varsa durur.

Ghidra ile kendi şablonumuz statik çözümlendi. `work/audit_copied_worker.py` şablon ve kod hash'lerini,1117talimat kaydının byte'larını ve13dolaylı `CALL EAX` noktasını doğruladı. Dış hedefe doğrudan çağrı veya mutlak bellek operandı gözlenmedi. Ghidra function-body aralığında kalan beş baytlık tek boşluk ayrıca iç hedefe giden relative JMP olarak doğrulandı; kopyalanan aralık sınıflandırılmamış byte bırakmadı.

Şablon SHA256 `0b96361f582118f1274273669aaa70103bde9cfd4bb736479365e8140b8a9b8a`, worker byte SHA256 `49560598eb4b371134f7f00edd64545699606c97512cc64f437fa71c237ec194`. Ghidra dosyası `Ghidra_Own_CopiedWorker_0b96361f.json`, kapı sonucu `FarmexBot_kopyalanan_worker_statik_kanit.json` dosyalarıdır. Bu kendi kodumuzun Ghidra denetimidir; REA Evidence veya orijinal uygulamadan canlı iz değildir.

## Başlangıç ve kapanış

Parent'ın normal akışı:

1. Kendi sabit child dosyasının SHA256/size kapısını geçer ve onu askıda oluşturur; job sınırı/handle kimliği önceki kontrolde olduğu gibi korunur.
2. Kendi DLL'inin10752bayt headers/3section verisini dört kopyayla child'daki `0x20000000` allocation'ına aktarır.
3.25336bayt bağlamı `0x22000000`,3772bayt worker kodunu `0x21000000` alanına kopyalar. Kod sayfası RW'den RX'e alınır ve instruction cache flush sonucu denetlenir. Bağlam RW kalır.
4. İlk remote thread bu kopyalanan worker adresinden başlar. Worker tam mapped-image karşılaştırmasını,116HIGHLOW relocation'ı,43import çözümlemesini ve section korumalarını denetler; DLL_PROCESS_ATTACH çağrısından sonra kendi fixture export'unu bulup sentetik HP/MP çerçevesini yayınlar.
5. Parent yalnız kendi bağlam allocation'ını okuyarak worker phase/status/sayaçlarını doğrular. Ana main gövdesinin işaretinden önce84bayt fixture çerçevesini salt okunur alır. HP250/500, MP100/300, profile1, PID/ABI/boyut/sequence ve hata alanları denetlenir.
6. Ana thread devam eder; önceki suspend sayısı1ve main hazır işareti görülür.
7. Parent okuyucusu kapandıktan sonra yalnız bağlamın command DWORD'una detach komutu yazar. İkinci own-child thread'i aynı kopyalanan worker'dan DLL_PROCESS_DETACH, import referanslarını bırakma ve image allocation'ını serbest bırakma yolunu çalıştırır.
8. Worker exit0ve bağlam phase2denetlenir; image MEM_FREE ölçülür. Worker/context allocation'ları thread bittikten sonra bırakılır. Child serbest bırakılır, child/parent exit0ve mapping'in yokluğu doğrulanır.

Normal yolda dört image-write, iki code/context-write ve bir detach-command-write vardır. İki remote thread ve bağlam okumaları **kendi child'ımızdadır**; oyun üzerinde bunların sayısı0dır. Fixture verisi mevcut oyundan alınmaz, bağımsız gerçek oyun doğrulaması değildir.

Windows API işaretçileri x86 parent'tan bağlama verilir. Bu testte kendi x86 child'ımızda gerçekten çalıştılar; farklı bir hedefin module base, bitness veya hook koşullarında aynı adreslerin doğru olacağı varsayılmaz. Import yolları bu örneğin sistem dizinindeki kernel32/msvcrt bağımlılıklarıyla sınırlıdır. TLS/delay-import/CLR veya başka PE'ler desteklenmiş sayılmaz.

## Başarılı ve reddedilen durum

İlk başarılı build52cd342cayrı kayıtta korundu. Cleanup ölçümünü açıkça ekleyen son olumlu parent SHA256 `378a9f7048a648e088c24612f544522168e0e20333c881a4d9e812e65018662a`; child SHA256 `33ad6531afdda501c6395c7811745e776524cde9b2dba61fa3c548fe50fda635`. Kanıt `FarmexBot_kopyalanan_worker_378a9f70_testi.json`: stage8, giriş/kapanış worker exit0, ResumeThread önceki1, child exit0, cleanup/exit gözlemleri1.

Negatif kontrolde yürütülecek DLL baytları değiştirilmedi; bağlamdaki karşılaştırma referansının yalnız ilk byte'ı bozuldu. Aynı worker tam-image karşılaştırmasında **kendi durum kodu7** döndürdü. Bu Windows hata7değildir. Parent normal akışı başarısız saydı; ana thread'i devam ettirmedi ve yalnız kendi child'ını exit90ile kapatarak terminal durumunu doğruladı. Beklenen ret testi geçti; DLL başlangıcı başarılıymış gibi raporlanmadı.

Negatif parent SHA256 `5ea1a4d34d5979bf80fd7a164fe1287cd5dc4d683a5f85956de83030cc981a73`; kanıt `FarmexBot_worker_ret_5ea1a4d3_testi.json`. Parent exit1, stage5, worker exit7, resume_previous0, child exit90ve cleanup_confirmed1beklenen sonuçlardır. Dosyada `expected_rejection=true`, `fixture_operation_succeeded=false` ayrımı bulunur.

## Kaynak yöntemiyle bağ ve kalanlar

Önceki orijinal Loader `0041e710` ve `0041e558` denetimleri; image/worker context/code kopyalama → relocation/import → üç argümanlı DLL entry çağrısı zincirini gösteriyordu. Kendi testimiz artık image, context ve bağımsız kodun taşınmasını ve kopyalanan entry'den çalışmayı içerir; önceki resident-helper bağımlılığı bu örnekte kaldırıldı.

Bu, orijinal Richard/VCL/CRT modülünü veya oyunu yüklediğimiz anlamına gelmez. Bağlam düzenimiz, kod boyutumuz, katı kendi-payload kapımız, section korumaları, fixture yayın ve kontrollü teardown orijinal worker'ın birebir kopyası değildir. Orijinal DLL worker'ının bütün thread'leri dolaşması yerine burada parent yalnız kendi ana thread'ini devam ettirir. Gerçek oyun thread/ABI, modül/TLS başlangıcı, hakları, güncel HP/MP ve bütün bot eylemleri açık kalır. Önceki yönetici başlatma iptali yeniden denenmedi.

Derleme: `build_suspended_bootstrap_fixture.ps1 -CopiedWorker`, ayrı OutputDirectory ve önceki sabit kendi DLL SHA256kapısıyla yapılır. `-RejectImage` yalnız bu worker biçiminde sabit negatif referans kontrolünü ekler. Çıkarılan kod başlığı ve EXE/DLL'ler kaynak ZIP'ine girmez. Ghidra kapısı runtime verifier'dan önce geçmelidir; şablon/hash değişirse eski kanıt kullanılamaz.

`work/verify_suspended_bootstrap.py --copied-worker-v2` ve `--copied-worker-rejection` son iki build'i denetler. Bütün beklenen alanlar kanıt dosyasına başarılı yazılmadan önce doğrulanır; beklenmedik sonuçta başarısız kayıt korunur. Native kontroller Python birim sayısına eklenmez; önceki1719Python/UI sonucu bu native-only adımda tekrar çalıştırılmadı.
