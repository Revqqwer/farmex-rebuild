# DC kontrol modellerinin dört katmanlı bağlantısı

`dc_full_chain.py` mevcut dört kontrol modelini açıkça birleştirir: sınırlı periyodik parent → seçili scan/list tüketicisi → ulaşılan her sender için ayrı00464834 yardımcısı →004647b8 iç yardımcısı. Dosyadaki “full chain” adı yalnız bu model bağlantısıdır; bütün bot, bütün441instruction caller veya native çalışma tamamlandı anlamına gelmez.

Parent raw context6e/enable/unsigned300000ms kapısından çıkarsa action child oluşturulmaz. Kaynak tüketici çağrısına ulaşıldığında doğru list/scan ve context5690f8 ile `DCSenderConsumerFrame` kurulur. Parent'ın erken normal receipt'i eksik alt modelleri atlatamaz. Her düzeyin kaynak girişinin türetilmesi, o düzeyin prologue/helper/normal dönüş gözlemlerini otomatik doldurmaz.

İç thread helper tamamlanması ayrı sender outer dönüşünü üretmez. Sender tamamlanması consumer'ın `rowN.send` dönüşünü üretmez. Consumer tamamlanması periodic parent'ın `consumer` dönüşünü üretmez. Bunların ardından ayrı `post_tick` normal dönüşü ve ham EAX gözlemi alınmadan553ce4 stamp store intent'i oluşmaz. Son `post_tick` beklerken tamamlanmış alt modelin payload/write/şablon izi sonuçta korunur.

Parent kaynakta gönderim başarısı aramaz. Örneğin payload allocation EAX0 ile sender normal erken dönebilir: write intent'i yoktur fakat tüm normal dönüşler sağlanırsa parent yeni timestamp yoluna gider. Bu, gerçekten paket gönderildiği veya oyunda işlem olduğu anlamına gelmez. `payload_intents` planlanan byte'ları, `write_intents` katman/label/pointer/byte kayıtlarını, `stubs` ise oluşmuş şablon byte projeksiyonlarını sunar; hiçbiri bir Windows API çağrısı çalıştırmaz.

7 yeni test olumlu dört katman zinciri, üç erken parent çıkışı, eksik sender'ın atlatılamaması, wait boşluğunda korunmuş write öneki, üç ayrı outer dönüş ve fresh post tick, allocation failure sonrası kaynak timestamp yolu ve boş snapshot'lı scan seçimini denetler. Kod, parent beklerken bitmiş child izini kaybetmez; aynı final frame ikinci kez ilerletilince yeni kayıt üretmez.

Kaynak denetimi eski/güncel Richard'da1940instruction union'ını ve her sürümde ek üç callback callsite instruction'ını, toplam1946kaydı yeniden doğrular. Örtüşen önceki model raporları toplanıp sahte yeni kapsama dönüştürülmedi. Sekiz mevcut REA çıktısı yeniden eşleştirildi. Kanıt: `outputs/FarmexBot_DC_dort_katman_bagi_kaniti.json`.

API kapsamıdır; actual checkbox arayüzü/periyodik callback runtime scheduling bu birleşik modeli otomatik çalıştırmaz. Gözlemler captured fixture verisidir; runtime process/allocator/string/RTL/SEH, sender ABI ve canlı oyun eşdeğerliği açık kalır. Önceki own-native26byte RET8 testleri gerçek remote akışı yürütmüş sayılmaz. Son normal-context name/PID kontrolü0 eşleşme verdi; bu bütün masaüstü oturumlarının görünürlüğünü kanıtlamaz. Gerçek bellek, thread, süreç veya oyun işlemi yapılmadı.
