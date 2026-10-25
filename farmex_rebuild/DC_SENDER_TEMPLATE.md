# DC gönderici yardımcısının normal kontrol ve byte modeli

`dc_sender_template.py`,00464834 dış yardımcısı76instruction ve004647b8 iç yardımcısı43instruction için inert normal kontrol akışını modeller. `patched_sender_template` dört raw DWORD'dan26byte şablon üretir. `DCTransferFrame` bu byte üretimini kaynak yardımcı/normal dönüş sırasıyla ilerletir. Windows API çağrıları yalnız tuple kaydıdır; Python modülü ctypes/remote-memory/thread çağrısı yapmaz.

## Dış yardımcı

Giriş, prologue ve yerel şablon kopyalama normal dönüşleri ayrıdır. Şablonun diskteki26byte'ı iki Richard görüntüsünde doğrulandı. İlk VirtualAllocEx payload uzunluğuyla istenir; EAX0ise payload write, patch, inner sender ve payload free yollarına girilmez. Bu erken dönüşte yerel template kopyası vardır fakat tamamlanmış bir sender stub'ı olarak değerlendirilmez.

Allocation nonzero olduğunda payload write intent'i kaydedilir ve WriteProcessMemory normal dönüşü beklenir. Kaynak BOOL/bytes-written sonucunu kapı olarak kullanmadığından model başarı EAX alanı üretmez. Normal dönüş de başarılı yazma kanıtı değildir.

Dört `_memcpy` sınırı sırasıyla3/8/13/18offset'lerini doldurur:553e84 globalinden **kopyada kullanılan** captured DWORD, kaynak uzunluk argümanı, önceki allocation pointer'ı ve553e90 globalinden kopyada kullanılan captured DWORD. Global değerler helper dönüşünden sonra yeniden okunmuş sayılmaz. Her normal receipt ve gerektiği yerde captured input ayrı alınır; eksik geç capture önceki patch'leri geri almaz. Tamamlanan aynı frame ikinci kez patch/write intent'i üretmez.

## İç yardımcı ve temizleme

Kaynak004647b8 çağrısı iç girişini türetir; inner prologue normal sınırı ayrıca gerekir. İkinci allocation26byte şablon içindir. Bu allocation0ise write/thread/wait/close/free stub yolu atlanır. Child epilogue ve ayrı outer normal dönüşünden sonra **ilk payload alanı yine bırakılır**.

İkinci allocation nonzero ise şablon write intent'i, CreateRemoteThread normal dönüşü ve ham thread EAX sonucu alınır. Thread nonzero için sonsuz timeout WaitForSingleObject normal dönüşü gerekir. Thread0ise wait atlanır fakat kaynak CloseHandle(0) çağrısına ulaşır. Ardından stub alanı bırakılır. İç epilogue tamamlanması dış helper normal dönüşü değildir; `stub_outer` ayrıca gerekir. Bundan sonra payload free ve outer FS/stack/return normal sınırı tamamlanır.

Bu sıra kaynak normal kontrolüdür; Win32 error/exception/SEH davranışını veya gerçekten yazılmış byte/thread durumu/free başarısını sertifikalandırmaz. CloseHandle0/handle0/length0 gözlemleri kaynakta olmayan otomatik başarı/başarısızlık varsayımına çevrilmez.

## DC tüketicisine bağlantı

`DCSenderConsumerFrame` list/scan tüketicisinin ulaştığı her `rowN.send` için ayrı `DCTransferFrame` oluşturur. Handle ve immutable payload, parent'ın kendi intent'inden alınır; kaynak uzunluğu/payload/handle eşleşmesi denetlenir. Sender entry gerçek kaynak çağrısından türetilir. Erken consumer normal receipt'i eksik sender child'ını atlatamaz. Child complete olsa bile consumer'ın ayrı normal dönüşü gerekir. Sonraki satırdaki sender için önceki child state'i kullanılmaz. Guard'ın atladığı sender hiç oluşturulmaz.

Bu isteğe bağlı API'dir; mevcut periyodik cascade varsayılan olarak opak tüketici çağrısını korur. Native oyunda otomatik gönderim veya arayüzden remote operasyon başlatma eklenmedi.

## Doğrulama

15 test ilk/ikinci allocation0 ayrımı, thread0 wait-skip/CloseHandle/free sırası, write normal receipt ile BOOL başarısının ayrımı, dört patch ve partial prefix, kopya input capture'ı, inner/outer normal dönüşleri, bekleme kesintisi, sender binding ve iki satırın bağımsız child state'ini denetler. İki sabit Richard sürümünde iki tüketici ile iki sender gövdesi toplam964instruction kaydı ve dört mevcut REA çıktısıyla doğrulandı.

Önceki altı own-native vaka, aynı26byte biçimi kendi RET8 alıcılarımız altında sınamıştı. Bu kanıt hash/log/source üzerinden yeniden bağlandı; native test bu aşamada tekrar çalıştırılmadı. O test yeni remote allocation/write/thread modelini çalıştırmış sayılmaz. Kaynak kanıtı: `outputs/FarmexBot_DC_gonderici_model_kaniti.json`.

Tam fonksiyon semantiği, actual runtime globals/target/context/ABI, remote write/thread/wait/free etkileri, VCL/SEH ve canlı uyumluluk açık kalır. Bütün oyun/native yürütme bayraklarıFalse kalır; hiçbir gerçek remote operasyon yapılmadı.
