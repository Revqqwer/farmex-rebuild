# Bulunan runtime: başlangıç ve RNG kapsamı

Özgün loader kaynak akışında RTL arşivi için C:\Windows hedefi vardı. Bu konumda cc32260mt.dll bulundu; yalnız System32/SysWOW64 ve oyun/bot klasörlerine bakan önceki arama bu dosyayı kapsamıyordu.1057144baytlık dosya çalıştırılmadan ayrı analiz kopyasına alındı. SHA256:45b21b5cb5d13af35bdc3a5c5ca058a8df679e579bed95c19aad0ac2dd423b8e.

3377adlandırılmış export içinde __startupd, _srand ve _rand var. REA PE kaynak envanteri2payloadı çıkardı;payloadlar doğrudan dosya baytlarıyla doğrulandı. Bu REA statik kaynak kanıtıdır. Ayrı Ghidra kayıtlarında8odaklı yordamın328benzersiz talimatı dosyayla eşleşti. Genel autoanalysis180s sınırına ulaştı ve tam DLL analizi tamamlanmadı;sonraki odaklı exportlar3+3+2tamamlandı/missing0/failed0. Bu sekiz gövde bütün DLL veya bütün TLS alt yordamlarının doğrulaması değildir.

## Başlangıç sırası

Bu diskteki __startupd, reason1 process-attach yolunda önce322392b8 başlangıç tablosu yürütücüsünü, sonra32239a00callback sarmalayıcısını çağırır. Normal dönüşlerin gerçekleştiği kaynak yolunun sırası budur;oyunda yeni bir canlı çağrı izi değildir.

Başlangıç kaydı6bayttır:byte1öncelik,byte2'den itibarenDWORD işleyici. Yürütücü init için öncelikleri0..255artan sırada;eşit öncelikte tablo adresini artan sırada dolaşır. Descriptor'daki exit tabloları detach tarafında ters kayıt/azalan öncelik sırasıyla kullanılır. Record byte0bu yürütücüde kontrol edilmez.

Güncel modüldeki00508048descriptor init aralığı00401000..00401ab6içinde457kayıt içerir. Profil/global kurucusu0049f061,00401006kaydındaöncelik32ile yer alır;öncelik sıralamasında sıfır tabanlı453indekse, yani454.çağrı planına gelir. Bunun dosyada ikinci kayıt olması ikinci çalışacağı anlamına gelmez. Descriptor callback'i004a111c'dir. Bütün initializer çağrıları normal döner ve bu runtime akışı kullanılırsa profil kurucusu callback'ten önce yürütülür.

32239a00gövdesi dört stack girdisi alır:işleyici,module,reason,reserved;üç DLL callback argümanını açık push eder ve sonundaRET10hex kullanır. Pseudocode'un iki argümanlı görünümü tam ABI değildir. Kaynak modülün __startupd çağrısı descriptor'u mevcut DLL giriş stack'inin üstüne koyar;assembly, descriptor/orijinal dönüş adresi/module/reason/reserved düzenini kullanır. Bunlar doğrudan genel bir C imzası olarak kopyalanmamalıdır. Exception sarmalayıcısının bütün hata davranışları ayrıca çözülmedi.

## Random gövdesi

Bu dosyanın _rand yordamı thread-data+48DWORD'unda aşağıdaki adımı uygular:

```text
next = (seed * 0x015a4e35 + 1) mod 2^32
eax  = (next >> 16) & 0x7fff
```

_srand,seed'i+48'e ve0'ı+4c'ye yazar;ardından_rand'ıbir kez çağırır. Bu ilk sonuç atılır.00467cc4yardımcısının_srandsonrasındaki_randçağrısı,aynı/değişmeyen thread-data sözleşmesinde ikinci adımdır. Her yardımcı çağrısı yeniden seed eder;yerel model global bir RNG akışını taşımıyor.

Thread-data yardımcısı thread kayıt tabanı+2178içindeki pointer'ı kullanır;boşsa allocation yardımcısı üzerinden oluşturur. Allocation/memory failure ve bütün TLS alt yordamları modelde yürütülmez. Bu nedenle replay için açık same_thread_context=True sözleşmesi gerekir;bu bayrak gerçek TLS pointer'larının ölçüldüğü iddiası değildir. Araya RNG state'ini değiştiren bir etki girmemesi de bu yerel sözleşmenin kapsamındadır.

Bu dosyanın15bit çıkışı0..32767ile sınırlıdır. Böylece60000..300000argümanlı yardımcının bu dosya varyantındaki aritmetik sonucu60000..92767içinde kalır. 16 Ekim 10:39 UTC ölçümünde oyun PID 19216 içinde C:\Windows\cc32260mt.dll yoluna ait MEM_IMAGE eşlemesi 0x321a0000 tabanında gözlendi. Aynı ölçümde diskteki dosyanın SHA256 değeri analiz kopyasıyla eşleşti. Bellekteki kod baytları, çağrıların yürütülmesi ve RNG sonuçları okunmadı; canlı davranış eşdeğerliği henüz doğrulanmadı. Başka/ölçülen CRT dönüşleri için ham EAX gözlem yolu ayrı kalır;aralık testlerinde kullanılan sentetik büyük EAX değerleri bu dosyanın üretebildiği değerler sayılmaz.

## Yerel JSON seçimi

`crt_rng.py`yalnız bu dosyanın matematik replay'ini yapar. Gerçek DLL yüklenmez. Mevcut initial_random_inputs,final_random_inputs veya predicate_inputs.random_inputs içine aşağıdaki seçim konabilir:

```json
{"tick":0,"srand_returned":true,"disk_crt_replay":true,"same_thread_context":true}
```

Bu örnekte warmup0atılır;ikinci_rand346olur;60000..300000yardımcı sonucu60346'dır. srand_returnedgözlemi ve ayrı helper tick'i hâlâ gerekir. Disk replay ile rand_eaxaynı ulaşılan çağrıda birlikte verilemez. Thread sözleşmesi bilinmiyorsa sonuç bekler. Plan rand_source=local_disk_crt_replayetiketini taşır;loaded_game_runtime_verifiedve native_execution_verifiedFalsekalır. Sonraki taze stamp,flag,kilit/mod gözlemleri kaldırılmadı.

Kaynak/sonuç kayıtları:FarmexBot_CRT_runtime_envanteri.json,FarmexBot_CRT_baslangic_random_kod_kaniti.json,REA_CRT_runtime_kaynak_kaniti.json. Orijinal DLL kaynak paketine eklenmez.

## Canlı eşleme gözleminin sınırı

Kullanıcı bot panelinin açık, kullanım süresinin bitmiş olduğunu bildirdi. Metadata tanısı yalnız QUERY_LIMITED_INFORMATION ve QUERY_INFORMATION istedi; oyun değerlerini okumadı, yazmadı veya koruma değiştirmedi. 6450 bölge ve 149 image allocation sorgusu içinde seçilen oyun ve CRT yolları gözlendi. Tarama atomik değildir. Önceki panel kapalı kaydı PID 20832'ye aittir; sonraki kayıt PID 19216'ya ait olduğundan fark yalnız panelin açılmasına bağlanamaz. Kaynak: FarmexBot_canli_CRT_eslenen_dosya_bot_panel_once.json. Modeldeki loaded_game_runtime_verified=False korunur: yol eşlemesi, bellekteki analiz edilen kodun ve gerçek çağrı davranışının doğrulaması değildir.

## Bağımsız başlangıç sırası modeli

`crt_startup.py` içindeki `decode_startup_records`, açık bir byte snapshot'ını altı baytlık kayıtlara çözer. `replay_startup_dispatch`, 322392b8 yordamının öncelik → descriptor → kayıt döngüsünü uygular. Init modunda öncelikler artar; sıfır dışındaki bütün mode DWORD değerlerinde exit öncelikleri ve descriptor içindeki kayıtlar tersine gider. Descriptor dizisinin sırası exit sırasında da ileri kalır. Prefix byte ve sıfır handler kaynakta filtrelenmez; model bunları sessizce atlamaz.

Bu API handler adreslerini çalıştırmaz. `stable_tables=True`, çağrıların tablo veya count'u değiştirmediğine ilişkin açık yerel varsayımdır. `normal_returns` içindeki her True bir normal dönüş gözlemidir; eksik/False dönüşte yalnız ulaşılan çağrı ve tamamlanan önceki çağrılar gösterilir. Bu model count'u açık nonnegative descriptor tuple olarak alır; bozuk, parçalı veya taşan tabloların native hata davranışını modellemez. Handler içi etkiler, exception sarmalayıcısı ve DLL callback yürütmesi kapsam dışıdır.

Güncel modülün gerçek tablolarıyla ayrı denetim 457 init ve 458 exit kaydını işledi. Profil kurucusu sıfır tabanlı 453. indekste kaldı; önceki 453 dönüş verilip kendi dönüşü verilmediğinde sonraki kayıtlara geçilmedi. Dispatcher'ın 79 talimatı CRT dosya baytlarıyla yeniden eşleştirildi. Kanıt: `FarmexBot_CRT_baslangic_plan_dogrulama.json`. Yedi yeni sınama dahil 1591 birim testi geçti. API değişikliği UI kullanmadığı için bu adımda UI ve native fixture testleri tekrarlanmadı.
