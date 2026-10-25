# Ana işleyici, Genie alt modeli ve ortak kendi kuyruğu

`MainWorkerObservation.children['genie_worker']`, typed `MainGenieObservation` kabul eder. Bunun `prefix` alanı mevcut Genie worker gözlemlerini, `notice` alanı yalnız ulaşılan Notice devamını taşır. Kaynak0046ee14, fresh mod DWORD0 ve active BYTE nonzero yolunda0045a05c'ye562194 context'i verir. Model child'ı ancak bu çağrıya ulaşılırsa oluşturur.

Eksik Genie child dış helper dönüşüyle geçilemez. Prefix erken dönerse Notice gözlemi gerekmez. Prefix Notice girişine ulaşırsa kendi general-stop local'i Notice'a bağlanır; çelişkili dış local reddedilir. Child tamamlandıktan sonra ana yordamın ayrı `genie_worker` normal dönüşü hâlâ gerekir. Ortak sonraki00458df8 çağrısı bu child ile birleştirilmez.

`MainWorkerFrame`, `GenieWorkerFrame` ve `GeniePrefixFrame` artık isteğe bağlı başlangıç `QueueState` alır. Kaynak Genie yenileme yardımcısı004ca588 ve MS eşya yardımcısı004ca900 aynı561ef8 enqueue context'ini kullanır. `MainWorkerFrame` bu iki generated yol için aynı kendi kuyruğunu taşır. Saf/ayrı planner çağrılarının kendiliğinden bir global oturum kuyruğu oluşturduğu iddia edilmez; ortak kuyruk bu frame bağıdır.

Genie envanter taraması alt modelde tamamlanıp7 baytlık kayıt oluştuğunda own queue, dönüş receipt'i beklenirken de üst frame'e taşınır. Tekrar advance aynı kaydı eklemez. İç enqueue, recovery helper, prefix post-tick ve main outer dönüş boşlukları ayrı kalır. Gate0 skip önceki kuyruğu korur. Farklı ana-worker turlarında caller açıkça önceki kendi kuyruğunu yeni frame'e verebilir. Bu, kaynak scheduler'ın veya diğer opaque kuyruk üreticilerinin bütün etkilerini kapsamaz.

Opaque recovery çağrısının normal dönüşü tüketilmişse daha sonra bu geçmiş çağrıya generated child eklenip yeni kayıt üretilemez. Önceden bağlanan child'ın tüketilmiş ID/gate/tick prefix'i ise korunur. Kendi kuyruk kimlikleri sıralıdır; bellekteki gerçek queue adresi veya server ACK değildir.

Sekiz yeni test; eksik child, reached-only Notice, önceki MS kaydı üstüne Genie kaydı, iç/main dönüş boşluklarında tek enqueue, gate0, ulaşılamayan child, geç binding reddi ve direct optional child yolunu kapsar. Eski/güncel ikililerde1618 mevcut talimat kaydı ve beş gerçek REA raporu eşleşti. Mode/active/caller context ve ortak enqueue context byte düzeyinde doğrulandı. Bu yeni binary keşif kapsamı veya tam worker sertifikası değildir.

UI değişmedi ve bu aşamada yeniden UI testi yapılmadı. Notice'a yalnız açık captured durum verilir; challenge algılama/çözme veya yanıt otomasyonu eklenmez. Oyun getter kimliklerini bütün çağrılar arasında birleştirme, gerçek envanter, native başlangıç/durdurma, scheduler, kuyruk drain/gönderim ve canlı uyumluluk açık kalır.
