# Upgrade paneli ve yerel motor bağlantısı

Güncel kaynak ayrımı: aşağıdaki panel snapshot köprüsü legacy deneme yoludur.
Gerçek başlatma yardımcısı combo Text'ini doğrudan okumaz; önce parametre
üreticisinin object+0'a atadığı cached ANSI scroll üyesini kullanır. Üç gerçek
parametre olayı artık own UI'da explicit gözlem sağlayıcısıyla bu üreticiye
bağlıdır; güncel kapsam UPGRADE_PARAMETER_UI.md ve ilgili validation dosyasıdır.
Start/stop/worker aktarımı hâlâ açık. Snapshot denemesinin geçmesi source
native eşliği veya canlı sertifika değildir.

Motor denemelerinde panel seçeneği açıldığında Upgrade artık `txtUpgradeWait`, `txtUpgradeAnvilID`, seçili scroll metni ve `LwUpgradeItems` işaretli satırlarını kullanır. Bekleme panelde milisaniyedir; ayrı sentetik denemenin saniye girdisi bu yolda kullanılmaz. Panel seçeneği kapalıyken önceki tek satırlı deneme korunur.

`upgrade_configuration.py` iki sayısal scalar için yerel signed64 decimal parser uygular ve kaynağın sakladığı düşük DWORD'u korur. Seçili liste satırlarının ana sütunu signed32 decimal olarak çözülüp DWORD kuyruğuna sırayla aktarılır. Yinelenen satırlar korunur; işaretsiz satırların metni sayıya çevrilmez. Ek sütunlar anahtar yerine kullanılmaz. Bu derleyici tek yerel snapshot'tan atomik bir sonuç üretir; orijinal start yordamının exception sırasında kısmen değiştirebileceği UI/vector state'ini taklit etmez.

Scroll `GetText` girdisi açık Unicode metnidir. Yerel UI, yalnız geçerli seçili combo indeksinin katalogdaki metnini çözebilir; `-1` durumunda bilinmeyen metin uydurmaz. Boş ama açıkça gözlenen metin ile bilinmeyen metin farklıdır. Bu combo indeksi gerçek envanter scroll indeksi değildir. ANSI dönüşüm baytları, lookup ve runtime scroll indeksi bu derleyiciyle doğrulanmaz.

İki scalar için kaynak yardımcı `StrToInt64` kullanır ve çağıran yalnız EAX'ı saklar. ListView anahtarı ayrı `StrToInt` yolundadır. Yerel parser decimal ASCII, isteğe bağlı işaret ve çevre boşluklarını destekler; Delphi'nin bütün biçimlerini veya exception/fallback davranışını uyguladığı iddia edilmez. Kaynakta anvil için 0, bekleme için 2000 ek argümanları görülür; bu argümanların bütün hata yollarındaki fallback etkisi tamamlanmış sayılmaz.

Panel köprüsü artık `UpgradeRunner(source_clock=True)` yolunu seçer. Eski doğrudan deneme varsayılan monotonic yolunu korur. Kaynak yolu giriş tick'ini DWORD, önceki stamp'i QWORD olarak alır; `signed64(tick - stamp)` değerini `signed32(interval)` ile karşılaştırır. Bu, DWORD farkını otomatik wrap ederek pozitif süre saymak değildir. Örneğin stamp `0xfffffff0`, tick `0x54`, interval100 iken kaynak farkı negatiftir ve bekler. Stamp `0xfffffffffffffff0` olduğunda aynı tick signed64 hesabında100 eder ve eşik sağlanır. Negatif signed aralık da artık kaynak yolunda desteklenir.

`start(..., initial_stamp_qword=...)` ve `start_armor` başlangıç stamp'ini açık gözlem olarak alır. Yeni bir nesnede verilmezse sıfır varsayılmaz; `needs_initial_stamp` döner. Tekrar start çağrısı mevcut stamp'i saat girdisinden yeniden kurmaz. Queue ve armor stamp'leri ayrı tutulur. Kaynak start yordamının tüm diğer producer/exception etkileri bununla uygulanmış sayılmaz.

İşlem kapısı geçildikten sonra helper normal dönüşü `source_helper_returned`, sonraki bağımsız GetTickCount ise `source_stamp_tick_dword` ile gelir. Eksik dönüşte `needs_helper_return`, normal dönüş biliniyor ama tick eksikse `needs_stamp_tick` oluşur. `source_pending.queue_after` kaynakta helper öncesinde çıkarılacak kuyruğun taslağıdır; kabul edilmiş `queue` bu eksik geçişte değişmez. Aynı pending işlem tamamlanırken önceki kapılar/tick yeniden örneklenmez, ikinci satır tüketilmez. Bu yerel kabul/taslak ayrımı gerçek native işlemdeki kısmi yan etkilerin geri alındığı anlamına gelmez. Normal dönüş False ise stamp güncellenmez. Tamamlanınca yüksek DWORD'u sıfır olan yeni stamp yazım planı kabul edilir. Armor sayacı düşük32bit ile artırılır ve signed32 olarak42 ile karşılaştırılır.

Gizli UI denemesi açıkça sentetik başlangıç stamp0, normal helper dönüşü ve deneme saatiyle aynı değerde ayrı post-helper tick verir. Bu eşit değerler gerçek iki saat okumasının eşit olduğuna ilişkin kanıt değildir. Gerçek clock/stamp producer, helper/transport/exception etkileri, concurrent değişiklikler ve `__ftol` sınır davranışı hâlâ canlı doğrulama ister.

Kaynak denetimi eski/güncel dosyada beş yordam çiftinin toplam 1554 talimat kaydını dosya baytlarıyla eşleştirdi. Üç taşınmış gövde, CALL dışı talimatların benzersiz eşleşmesiyle bulundu: `004f7604→004f7620`, `004f7adc→004f7af8`, `004f82cc→004f82e8`. İki string/sayı yardımcısı aynı adreste kaldı. İlgili import kimlikleri karşılaştırıldı; iç helper etkileri sırf adres/gövde eşleşmesiyle doğrulanmış sayılmaz. Dört published kontrol kaydı iki dosyada doğrulandı. Önceden alınmış REA Evidence içindeki 15 resource payloadı güncel dosya baytlarıyla yeniden eşleştirildi. Yeni Ghidra denetimi ayrı kaynak kanıtıdır; yeni bir REA çalıştırması olarak sunulmaz.

Kanıt: `FarmexBot_upgrade_panel_kod_kaniti.json`. Gerçek inventory/scroll seçimi, canlı çalışma gate'i, native çağrı, gönderim, item dönüşümü ve sunucu sonucu doğrulanmadı. Deneme ekranındaki kapı ve scroll envanter indeksi açık sentetik girdiler olarak kalır.

## Kaynak scroll ad taraması

`upgrade_scroll.py`, eski `004f7040` / güncel `004f705c` yordamının 14..41 yuva taramasını modeller. Her yuvada seçili Unicode metnin dönüşüm yardımcısı yeniden çağrılır, sonra taze çanta adı alınır ve ANSI eşitliği karşılaştırılır. İlk eşleşme `slot-14` döndürür; tam 28 karşılaştırmada eşleşme yoksa `-1` döner. Sabit scroll ID tablosu veya otomatik eşya sınıflandırması yoktur.

`UpgradeScrollObservation.samples` her ulaşılan yuva için ayrı `converted_key_bytes` ve `slot_name_bytes` gözlemlerini içerir. Alternatif olarak `slot_name_inputs` mevcut `SlotNameObservation` modeline bağlanabilir; yakalanmış DWORD/name girdilerinden çanta adı hesaplanır. Bu yol süreç belleği okumaz. İki ad girdisi aynı ulaşılan yuvada birlikte verilirse hata olur. Bir önceki eşleşmeden sonraki örnekler değerlendirilmez. Eksik key dönüşümü/ad gözlemi yokluk sayılmaz. Boş ama açık iki ANSI içerik eşleşebilir. Harf büyüklüğü, gömülü NUL ve string uzunluğu korunur; casefold/strip/decode uygulanmaz. Bu byte-equality adapter'ı oyun içinde çalışan RTL'nin ölçümü değildir.

`UpgradeRunner` kaynak-saat yolunda, süre kapısı geçilmiş ve `queue_action_ready=False` ise isteğe bağlı `UpgradeSnapshot.scroll_lookup` sonucunu kullanır. Tam sonuç `source_scroll_index` gözlemini günceller; `-1` durdurur, bulunan indeks bu çağrıda kuyruktan satır çıkarmaz. Eksik gözlem `needs_scroll_lookup` üretir; state/queue/stamp değişmez. Ham `scroll_index` ile bağlı lookup aynı ulaşılan dalda birlikte verilemez. Hazır gate dalında tarama yapılmaz. İlk başlatma taraması ayrı `upgrade_start.py` modeliyle aşağıda bağlandı; gerçek vector/UI yan etkileri tamamlanmış sayılmaz.

Upgrade denemesinde varsayılan kapalı “örnek çanta adlarını tara” seçeneği, açık ASCII katalog metni ve kendimize ait 28 örnek adla bu yolu çalıştırır. 0..27 seçimi yalnız örnek scroll yuvasıdır; `-1` tüm örnek adların farklı olmasını sağlar. Bu, gerçek çanta snapshot'ı veya canlı envanter indeksi değildir. Kapı hâlâ açık sentetik girdidir.

Kaynak kanıtı `FarmexBot_upgrade_scroll_kod_kaniti.json`: tarayıcı, çanta adı yardımcısı ve eşitlik wrapper'ının iki dosyadaki toplam 428 talimat kaydı doğrulandı. API çağrı etiketlerinde tarihsel helper adresleri korunur; güncel tarayıcı `004f705c`, eşitlik wrapper'ı `00505134`, ad yardımcısı `00463670` olarak eşlendi. Key dönüşümünün gerçek codepage/RTL baytları, korunmuş oyun okumaları, concurrency ve native sonuçlar hâlâ doğrulanmadı.

## İlk başlatma ve durdurma sırası

`upgrade_start.py`, source `004f7adc` / current `004f7af8` yordamının yerel kontrol sırasını modeller. Nonzero start BYTE için önce form+a5c/a60 üzerindeki virtual+94 çağrılarına0/1 planlanır; kontroller published kayıtlarda `btnUpgradeAll` ve `btnUpgradeStop` olarak eşlendi. “SetEnabled” etiketleri bu çağrıların yorumudur; gerçek native VCL widget etkisi ölçülmedi. Sonra end/begin/range-erase yardımcılarının normal dönüşü, ilk scroll ad taraması, scroll index yazımı ve geçici string temizliğinin normal dönüşü gerekir. Ardından her döngü testinde ayrı signed32 GetCount gözlemi alınır. Count<=index döngüyü bitirir; checked BYTE nonzero ise ana sütunun StrToInt sonucu sırayla eklenir. En sonda mode1 olur.

İlk scroll taraması-1 döndüğünde start yordamı hemen durmaz: sonraki çağrılar normal dönerse mode1'e ulaşır. “Scroll yok” durması sonraki çalışma tüketicisinin uygun dalındadır. Stop BYTE0 ise önce mode0 yazımı, sonra UI çağrılarına1/0 planlanır; bu stop yordamı kuyruğu temizlemez. Başlatma/durdurma burada clock stamp'i yazmaz.

`UpgradeStartPlan.state` yalnız bütün yerel yol biliniyorsa değişir; eksikte giriş state'i korunur, bilinen prefix `prospective_state` içinde görünür. Bu ayrım gerçek orijinal programdaki kısmi UI/heap yan etkilerinin geri alındığı iddiası değildir. `apply_upgrade_start` yalnız tam planı ve hâlâ aynı mode/queue/scroll snapshot'ını kabul eder, source clock'u değiştirmez ve gerçek UI'ye işlem göndermez. Normal-return alanları gerçek helper/allocator uygulaması yerine açık gözlemlerdir. Heap/iterator bozulması, exception handler'larının bütün etkileri, satır temizliği/append capacity branch'lerinin native ayrıntıları ve eşzamanlı callback'ler uygulanmadı.

Panel yolu `defer_rows=True` ile satır anahtarlarını önceden parse etmez. İlk tarama eksikse veya önceki normal dönüş bilinmiyorsa daha sonraki yanlış caption sahte erken hata üretmez. Yerel caption parser yalnız `local_decimal=True` ile kullanılır; alternatif `key_dword` gerçek StrToInt dönüşünün açık gözlemidir. Hazır dönüş ile yerel caption aynı ulaşılan checked satırda birlikte verilemez. GetChecked false olan satırın caption'ı değerlendirilmez. UI kendi profilinin sabit count/checked/caption örneklerini ve açık normal-return fixture'larını sağlar; bunlar orijinal oyundan okunmuş veriler değildir. Örnek başlangıç/çanta seçeneği kapalıyken panel denemesi ilk taramada gözlem bekler ve çalışma state'ine geçmez. Açıkken geçerli örneklerle source-start planı uygulanır; stamp0 ayrı sentetik saat gözlemidir.

Kaynak denetimi, start ve üç iterator/range helper'ının iki dosyadaki508talimat kaydını doğruladı. Başlatma gövdesinde queue/armor clock alanına doğrudan yazım bulunmadı; bu yalnız incelenen gövde kapsamıdır. Kanıt: `FarmexBot_upgrade_baslangic_kod_kaniti.json`. Gerçek VCL/allocator/çanta/oyun başlangıcı veya native çağrı eşdeğerliği hâlâ açık.

## 57 bayt Upgrade tamponu

`upgrade_packets.py`, eski `004f714c` / güncel `004f7168` yordamının sabit57bayt şablonunu ve beş alan yazımını üretir. Şablon iki dosyada aynıdır. İleri REP kopyası için DF=0 yerel ABI varsayımı kullanılır; native register durumu ölçülmedi. Alanlar:

| Offset | Boyut | İçerik |
|---|---|---|
| 3 | 4 | Anvil DWORD, little endian |
| 7 | 4 | Hedef eşyanın taze helper ID'si |
| 11 | 1 | Hedef göreli yuva parametresinin düşük BYTE'ı |
| 12 | 4 | Scroll'un taze helper ID'si |
| 16 | 1 | Scroll göreli yuva parametresinin düşük BYTE'ı |

Kaynak önce `(scroll_relative+14) mod2^32`, sonra `(target_relative+14) mod2^32` argümanıyla `004634a4` çağırır. İki dönüş ayrı gözlemdir; ortak ID varsayılmaz. Tam DWORD getter argümanında kullanılırken yalnız düşük BYTE tampona kopyalanır. Native gövdede görülmeyen0..27 clamp'i serializer'a eklenmedi. Geri kalan şablon baytları aynen korunur. Anvil gözlemi eksikse iki getter'dan sonra bekler; getter eksikse daha sonraki alan/gönderim planına ilerlemez.

`UpgradeItemObservation` ile getter'ın yedi `0045dc44` sonucuna bağlanılabilir. Root→inventory→slot record→base/variant pointer→iki DWORD akışı, sıfır gözlenen record'da erken0 dönüşü ve `(base + unsigned_variant%1000) mod2^32` uygulanır. Record0 gözlemi fiziksel çantanın boş olduğunun bağımsız kanıtı değildir. Bu API yalnız verilen değerleri ve planlanan adresleri işler; koruma değiştiren native okuyucuyu çağırmaz, oyun belleğine erişmez. Yakalanmış helper EAX ile bağlı getter aynı ulaşılan çağrıda birlikte verilemez.

Sonuçta `004c7710(context00561ef8,buffer,57,0)` çağrı planı olarak görünür. Serializer aşağıdaki `UpgradeExecution` ile yerel kuyruğa ve panel denemesine bağlandı; gerçek oyun kuyruğu/transport/upgrade sonucu yoktur. İlk API aşamasının kanıtı `FarmexBot_upgrade_tampon_kod_kaniti.json`: iki gövdenin eski/güncel256talimat kaydı, caller kesitinin18kaydı,57şablon baytı ve beş memcpy import kimliği doğrulandı. Bu ilk aşamada dokuz yeni test dahil1639birim testi geçmişti; sonraki bileşim doğrulaması ayrı kayıttadır. Canlı inventory/gate/ABI/sonuç bağları açık.

## Çalışma döngüsü, tampon ve yerel kuyruk bileşimi

`UpgradeExecution` bir source-clock `UpgradeRunner` ile sahip olduğu `QueueState`'i bağlar. Helper henüz başlamadan kurulmalıdır. Caller kapıları normal olarak değerlendirilir; helper'a ulaşıldığında dışarıdan verilmiş `source_helper_returned=True` tampon/kuyruk aşamalarını atlatamaz. Helper parametreleri yakalanır, iki item getter gözleminden57bayt üretilir, sonra bağımsız `QueueSample.connection_gate/tick` gerekir. Tamamlanmış ilk getter dönüşü sonraki eksikte tutulur; değişen hazır dönüş reddedilir. Kısmi getter snapshot'ları aynı çağrıya ait tutarlı gözlemler olmalıdır; gerçek belleği yeniden örnekleme yapılmaz.

İşlem kapısı ile kuyruk bağlantı kapısı farklıdır. `004c7710` için sıfır kayıt eklemeyen normal yoldur; her nonzero DWORD copy/tick dalına girer. Yalnız dış callback'in başka bir yerindeki exact1 koşulu buraya taşınmaz. Gate açık ama queue tick eksikse gate'in değişmesine izin verilmez. Gate sıfır olduğunda queue tick gerekmez. Sonrasında helper normal dönüşü ve caller'ın ayrı stamp tick'i gerekir. Böylece kayıt eklenmeyen bir normal helper yolu da source satırını tüketebilir; bu başarı/ACK sayılmaz.

Tampon ve queue kararı bir kez bilindikten sonra sonraki stamp eksiklerinde yeniden üretilmez. Yerel queue kopyası `prospective_queue` içinde görünür; kabul edilmiş queue ve source item kuyruğu tam yerel frame sonuna kadar korunur. Sonra tek source satır ve en çok tek queue kaydı commit edilir. Bu bir yerel plan kabul politikasıdır; orijinal programdaki kısmi heap/queue yan etkilerini geri almaz. Tamamlanmış kopyadan sonra verilen yeni örnekler eski kaydı değiştirmez. Bileşim sırasında source pending nesnesi veya kabul edilmiş yerel queue dışarıdan değiştirilirse hata verilir; eşzamanlı üretici/native queue birleşimi uygulanmadı.

Panel denemesi bu bileşimi kullanır. Katalogdan seçilen scroll adı, ilk tarama ve sentetik helper-return fixture'ları önceki gibidir. Scroll ID `0x10203040`, hedef ID ayrı deneme ID girdisi, kuyruk gate'i ayrı kontrol, üç saat ise gate=t, enqueue=t+1, post-helper=t+2 olarak açık yerel örneklerdir. Bunlar oyundan okunmuş değerler değildir.57bayt hex ve kuyruk kayıt sayısı görüntülenir. Kuyruk drain edilmez, native gönderim yapılmaz. Armor helper'ı sonraki aşağıdaki adımda ayrı gözlemlerle bu bileşime eklendi.

Kaynak bileşim kanıtı `FarmexBot_upgrade_kuyruk_bilesim_kod_kaniti.json`: üç gövdenin eski/güncel1180talimat kaydı, caller→serializer→enqueue→connection helper bağları ve13import çağrı kimliği doğrulandı. Bu bağlar dosya düzeyindedir; çalışan oyundaki çağrı izi veya allocator/native ABI kanıtı değildir.

## Armor alım helper'ının iki tamponu

`upgrade_armor.py`, eski `004f7210` / güncel `004f722c` helper'ını modeller; `UpgradeExecution` bağlantısı sonraki bölümde açıklanır. Helper önce `00463a8c` ile14..41 yuvalarını tarar; her yuvada taze `004634a4` dönüşünü kullanır. İlk sıfır sonuç `slot-14` WORD değerini,28nonzero sonuç255değerini üretir. Eksik sonuç sıfır veya doluluk sayılmaz. Yakalanmış `UpgradeItemObservation` ile bu ID getter'ına bağlanabilir. Sıfır helper sonucu gerçek boş çantanın bağımsız kanıtı değildir.

Sonra altı vendor karşılaştırması ayrı ayrı yapılır: Sundries, Armor, Weapon, Potion, DC Sundries, Amore. Her True kendi kodunu yazar; son eşleşme kazanır. Önceki eşleşme olsa da sonraki bilinmeyen karşılaştırma atlanmaz. İncelenen helper gövdesinde vendor stack local'ine yalnız bu altı koşullu yazım var, açık sıfır başlangıcı yok. Hiçbiri eşleşmezse model `initial_vendor_dword` gözlemi ister; bunu sıfır varsaymaz. Bu, dış runtime/prologue veya bütün native stack durumunun çözüldüğü anlamına gelmez.

20bayt şablon `00550fc5` adresinden alınır; source ileri REP kopyası için DF=0 varsayılır. Alanlar:

| Offset | Boyut | İçerik |
|---|---|---|
| 2 | 4 | Vendor kodu |
| 6 | 4 | NPC DWORD parametresi |
| 11 | 4 | Eşya DWORD parametresi |
| 15 | 1 | Boş-yuva helper AX sonucunun düşük BYTE'ı |
| 16 | 2 | Miktar parametresinin düşük WORD'ü |
| 18 | 1 | Selector A düşük BYTE |
| 19 | 1 | Selector B düşük BYTE |

Offset10'daki1ve diğer dokunulmayan şablon baytları korunur. Yardımcının kendisinde free-slot255için erken dönüş eklenmedi; caller'ın daha önceki çanta gate'i ayrı gözlemdir ve arada değişiklik olamayacağı varsayılmaz. Normal mode2 caller kesiti vendor literalArmor, miktar1, selectorA0ve obje+4c/+58/+5c alanlarını aktarır; tam Armor başlatıcı/NPC/panel üreticileri bu encoder'la uygulanmış sayılmaz.

İlk enqueue planı20bayt/0ms'dir. Ardından `004c911c` wrapper'ı `00547786` adresindeki `6a02` iki baytını100ms gecikmeyle ayrı `004c7710` çağrısına verir. Bunlar tek bir paket veya tek bir bağlantı/tick gözlemi değildir. Encoder API'si yalnız `(payload,delay)` çiftlerini üretir; tek başına kuyruk ekleme, drain, helper normal dönüşü veya sunucu ACK'si yapmaz. Bileşim her enqueue için bağımsız gate/tick ister.

Kanıt `FarmexBot_upgrade_armor_tampon_kod_kaniti.json`: üç gövdenin eski/güncel564talimat kaydı, caller kesitinin52kaydı, iki sabit şablon, altı vendor literal/kodu ve yedi memcpy import kimliği doğrulandı. On yeni test dahil1659birim testi geçti. UI/native kodu değişmedi; bu adımda UI/native testleri tekrarlanmadı. Canlı Armor NPC/çanta/satın alma sonucu doğrulanmadı.

## Armor döngüsü ve iki enqueue bağlantısı

`UpgradeExecution.step(..., armor_inputs=ArmorExecutionInputs(...), armor_queue_samples={0:...,1:...})`, Armor encoder'ını source-clock runner'a bağlar. Buradaki state2, Upgrade nesnesinin+0x10alanıdır. Caller'ın NPC(+4c), item(+58), selectorB(+5c) girdileri açık gözlemdir; miktar1ve selectorA0caller sabitleridir. Bu alanlar aşağıdaki `armor_start.py` planından da üretilebilir; gerçek native NPC arama/başlatma yürütülmez. Tamamlanmış first-zero WORD ve vendor karşılaştırmaları sonraki eksikte tutulur; değişen bilinen sonuçlar reddedilir. Tampon tamamlandıktan sonra yeni encoder verisiyle aynı kayıt yeniden kurulmaz.

Her enqueue ayrı gate ve tick ister. Birinci kayıt kopyalanıp ikinci sample eksik kaldığında ilk kopya yalnız `prospective_queue` içinde kalır. Sonraki adım sadece ikinci kaydı sürdürür; ilk kaydın saati/ID'si değişmez. İlk gate0, ikinci nonzero ise yalnız `6a02` kaydı oluşabilir; tersi durumda yalnız20baytlık kayıt oluşabilir. Her iki gate0iken de normal helper/cleanup/stamp yolu bir yerel deneme sayabilir. Bu sayı satın alma başarısı değildir.

İki enqueue bilindikten sonra ayrı helper normal dönüşü, caller'ın `00505c48` geçici string temizliği ve sonraki stamp tick'i gerekir. Cleanup gözlemi `ArmorExecutionInputs.caller_cleanup_returned` alanıdır. Eksikte sayaç/stamp/kabul edilmiş queue korunur. Önceden bilinen helper/cleanup dönüşleri yeniden istenmez. Stamp bilindikten sonra DWORD sayaç artırılır; signed43sınırı mevcut yerel runner politikasını uygular. Native durdurma mesajlarının ve exception/concurrency yollarının bütün etkileri bu sonuçla doğrulanmış değildir.

“Armor Alımı” arayüz denemesi örnek gözlemler açılınca aşağıdaki başlangıç modelinden state2üretir; stamp0ayrı bir gözlemdir. İşletim sistemi/oyun içinde NPC arama yapılmaz. Kendi çanta ID dizisi, Armor vendor-match fixture'ı, helper/cleanup dönüşleri ve gate=t, enqueue0=t+1, enqueue1=t+2, stamp=t+3saatleri sentetiktir. İki kuyruk bağlantısı ayrı kontrol edilir.43yerel denemede86yerel kayıt görülmesi43satın alma veya ağ gönderimi anlamına gelmez. Kuyruk drain edilmez.

Kaynak: `FarmexBot_armor_kuyruk_bilesim_kod_kaniti.json`, dört gövdenin eski/güncel1554talimat kaydı ve dört çağrı bağı. Caller helper dönüşü → geçici temizliği → GetTickCount → stamp → sayaç sırası assembly'den ayrıca doğrulandı. Canlı NPC/çanta/clock/VCL/allocator/native ABI ve sonuç açık kalır.

## Armor başlangıcı ve panel eşlemesi

`armor_start.py`, source `004f7f74` / current `004f7f90` başlangıç kontrolünü modeller. Filtre hazırlığının normal dönüşünden sonra `Armor Merchant` filtresiyle NPC helper sonucu gerekir. Mevcut `select_npc` modeli isteğe bağlı bağdır: gözlenen iterator sırası, signed distance, ID/name ve açık traversal completion gerekir. Kısmi seçim son ID sayılmaz. Son ID sıfırsa hata mesajı yolu, nonzero ise pointer helper'ı gelir. Pointer sıfırsa kaynak sessizce döner; sonraki koordinat veya mesaj gözlemi istenmez.

Pointer'dan ayrı x/y ofsetleriyle korumalı float okuma ve `__ftol` EAX sonuçları gözlem olarak alınır; +50/+54'e rawDWORD saklanır. Model native float okumaz, FPU/int→float dönüşümlerini yürütmez veya geometrik mesafe hesaplamaz. Sonraki distance helper'ının ayrı `__ftol` sonucu signed32 yorumlanır. Assembly `CMP result,9; JLE` kullanır;9geçer,10hata yoludur. X/y ve lookup sırasında kullanılan önceki uzaklık, bu taze distance sonucu yerine kullanılmaz.

Yakınlık geçilince combo+0xd98ilk kez okunur; `004f74d8` / current `004f74f4` eşlemesi23indeksi dönüştürür.5/11/17boş satırları ve tanınmayan bütün DWORD değerleri0üretir. Item0hata yoluna gider; ikinci combo ve bag flag henüz okunmaz. Nonzero item+58'e yazıldıktan sonra combo yeniden okunup+5c'ye yazılır. İki gözlem otomatik eşitlenmez. Bag helper ALnonzero ise hata, sıfır ise counter+60=0ve state+10=2yazılır. Bu gövdede clock alanına doğrudan yazım bulunmadı.

Hata mesajları ve bunların geçici string temizliği ayrı normal-return gözlemleridir. Erken hata, daha önce yazılmış NPC/pointer/koordinat/item alanlarını otomatik sıfırlamaz; önceki state/counter korunabilir. `complete=True` erken dönüş için de mümkündür; `armed=True` yalnız son state2yazımı yolundadır. Eksik gözlemde giriş state'i kabul edilmiş halde tutulur, bilinen prefix `prospective_state` içinde görünür. Bu politika gerçek native kısmi etkilerin geri alındığı iddiası değildir. `apply_armor_start` yalnız tam ve değişmemiş giriş snapshot'ına uygular; mevcut kuyruk ve iki clock stamp'ini korur.

UI başlangıçta sabit7uzaklıklı bir NPC ad/ID iterator örneği, sahte pointer0x7000/ofsetler4/8ve x/y/distance dönüş girdileri sağlar. Bunlar oyun verisi değildir. Panel seçeneği açıkken `cmbUpgArmorList` değeri iki okuma için sabit yerel profil örneğidir; kapalıyken ilk/ikinci combo ayrı girişlerdir. Scalar alanlar başlangıç planından alınır, her denemede UI'den yeni NPC/item tahmin edilmez. Boş panel5seçimi, NPC0ve full başlangıçları yerel denemeyi arm etmez; sonraki taze bag gate'i çalışma aşamasında ayrı değerlendirilir. Native mesaj gösterimi veya gerçek NPC taraması yapılmaz.

Kanıt: `FarmexBot_armor_baslangic_kod_kaniti.json`. Başlatıcı245, combo helper120ve NPC seçici268talimatlık gövdelerinin iki dosyadaki toplam1266kaydı eşleşti.23CMP/JNZ/return bloğu doğrudan source instruction'lardan çıkarılıp API eşlemesiyle karşılaştırıldı; +0xd98published kontrol kaydı iki dosyada doğrulandı. İki combo read site'i ayrı kaydedildi. Native iterator/STL/exception/FPU/VCL etkileri ve canlı uyumluluk hâlâ açık.
