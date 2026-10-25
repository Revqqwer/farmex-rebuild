# Normal tarama zamanlayıcısı — kaynak düzeltmeleri

`merchant_scan_step`, kaynak `004bf9dc` için tek çağrılık normal değer projeksiyonudur. Aynı modüldeki `MerchantScanFrame`, bunun üzerine ayrı bir kendi invocation gözlem katmanı ekler; kapsam MERCHANT_SCAN_FRAME.md içindedir. Gerçek timer, queue/helper yürütümü veya native child frame değildir. `ScanState.active` kendi çağrı korumasıdır; kaynak yordamın içinde böyle bir guard bulunmaz. Kaynak active byte'ının tüm kısmi child etkileri burada modellenmez.

İki tüketim dalında ilk GetTickCount yalnız50ms karşılaştırması içindir. `004bf5d0` normal döndükten sonra ikinci, bağımsız GetTickCount alınır ve56fb2c/30 QWORD'una sıfır genişletilmiş DWORD olarak yazılır. Eski model ilk saati kullanıyordu; artık `consume_returned` ve `post_consume_now_ms` ayrı gereklidir. İkisi yoksa eski damga korunur. Kullanılmayan dallar saat gözlemi istemez. Elapsed karşılaştırması source signed64 SUB/SBB davranışını korur; DWORD wrap adına yeni bir düzeltme eklenmez.

Rotalı koleksiyonda helper normal dönüşü ve EAX0 ayrı girdilerdir. EAX0 sonrasında rota indeksi artırılır, sonra rota boyutu yeniden okunur. `route_count_after_collect` için eski route_count fallback'i yoktur. Sonraki count eksikse tamamlanan indeks artışı korunur. Fresh count büyür veya küçülürse bitiş kararı buna göre verilir.

Actor durumunun offset globali554020'dir. Önceki `actor_raw_byte_55402c` alanı yanlıştı ve kaldırıldı; yeni alan `actor_raw_byte_554020` explicit BYTE ister. Bu API düzeltmesinde eski keyword için alias yoktur; sağlayıcı doğru alanı kullanmalıdır.

Distance yardımcısının normal dönüşü ayrıdır. `distance_status_word` verilirse kaynak `FNSTSW AX; TEST AH,45` maskesi kullanılır: maskeli bitler0 ise hareket, eşit/küçük/unordered ise arrival yolu. Sonlu nonnegative `selected_point_distance` eski normal scalar kullanım kolaylığı olarak durur; raw FNSTSW gözlemi önceliklidir. NaN için Python tahmini yapılması yerine explicit unordered status kullanılabilir.

Movement, collection, consume, export ve stop normal dönüşleri bağımsızdır. Çağrı intentinin listede olması helper'ın döndüğünü kanıtlamaz. Export normal dönmeden stop intentine geçilmez. Stop normal dönmeden kendi lifecycle `completed` yapılmaz. Eksik child dönüşünde kaynak child'ın daha önce yaptığı bellek/UI etkileri bilinmez; own caller/shadow state'in tutulması native rollback kanıtı değildir. Incomplete sonucu yeni bir native continuation gibi tekrar dispatch etmek güvenli olduğu iddiası yoktur; gerçek resumable composition ayrı açık iştir.

12 yeni regression testiyle toplam4384 Python testi geçti. İki Richard sürümünün202-instruction gövdesi dahil404 kayıt byte olarak doğrulandı; iki pre/post saat çifti, fresh count,554020 ve x87 maskesi ayrıca sabitlendi. Bu tüm native helper yollarının eşliği sertifikası değildir.

Yeni GUI çalıştırılmadı: değişen `merchant_scan.py` ve testi, app/smoke_ui köklerinden bulunan300 modüllük AST import closure'ının dışındadır. Closure'daki bütün kaynak hash'leri önceki4372 tam GUI kaydıyla aynıdır; tanınan nonliteral dynamic import bulunmadı. Bu statik dependency kontrolü ayrıca `MERCHANT_SCAN_SCHEDULER_VALIDATION.json` içinde tutulur. Scheduler API'si UI/timer/data provider'a hâlâ bağlı değildir.
