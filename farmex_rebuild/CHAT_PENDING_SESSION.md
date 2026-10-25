# Mesajlar arası yerel pending ve süre kilidi

20 Ekim 2026. `ChatPendingSession` bağımsız sürümde pending BYTE, kind/sender DWORD, süre kilidi ve yerel kayıt kuyruğunu mesajlar arasında korur. `begin_message/advance_message` mevcut üreticiyi, `begin_consumer/advance_consumer` mevcut sınıf tüketicisini kullanır. Bunlar açıkça başlatılan seri yerel işlemlerdir; native callback planlaması değildir.

Bekleyen istek doluyken ikinci mesaj üreticinin kendi guard'ından geçmez ve önceki kind/sender korunur. Attack lock üreticide kontrol edilmediğinden, pending boşken kilit açık olsa da yeni istek kabul edilebilir. Tüketici kilit açıkken isteği koruyup AL0 döndürür. Süre dolduktan sonra yeni tüketici çağrısı aynı isteği işleyebilir. Pending temizlendiğinde kind/sender alanları kendiliğinden sıfırlanmaz.

Tam tüketici sonucu pending ve üç kilit alanının store planlarını yerel state'e uygular. Bağlı doğrudan çocuk kuyruğu önceki session kayıtlarını aynı sırayla korumalıdır; aksi halde commit reddedilir. Yeni kayıtlar önceki kayıtların ardından gelir. Kuyruk boşaltılmaz, ağ çağrısı veya ACK oluşmaz. Diğer store planları tüketici sonucunda korunur; session bunları native etki olarak uygulamaz.

Eksik işlem sürerken başka mesaj, tüketici veya timer olayı başlatılamaz. Bu **bizim seri ve transactional yerel sözleşmemizdir**. Priest'in kaynakta helper'dan önceki pending temizliği eksik sonuçtaki `stores` içinde görünür; tamamlanmadan session state'e uygulanmaz. Kaynak programın bunu atomik yaptığı veya thread'leri böyle sıraladığı iddia edilmez. Bu aşama kaynak eşzamanlılık davranışını tamamlamaz.

`apply_reached_unlock_timer` yalnız açıkça ulaşıldığı verilen timer bölgesini yürütür; callback reachability'sini kanıtlamaz. Mevcut `plan_attack_unlock` modeli `(clock-started)&FFFFFFFF >= duration` koşuluyla BYTE kilidi temizler. Eşikte açılır, DWORD saat taşmasını korur; clock eksikse state değişmez. Modelin iz metnindeki GetTickCount adresi tarihsel sürüm adresidir; gerçek çağrı çalıştırılmaz. Güncel import rolü `FarmexBot_sinif_chat_cagiran_kaniti.json` kaynağında ayrıca doğrulanmıştır.

Sekiz yeni test iki mesajın kilit-bekleme-açılma-kuyruğa eklenme akışını, mevcut pending'in ezilmemesini, eksik Priest pre-clear commit sınırını, önceki kuyruğun kaybolmasını reddetmeyi, generic başarısızlıkta korumayı, Mage/Rogue clear farkını ve timer taşma/eşitlik sınırını kapsar. Son tam koşu `CHAT_PENDING_SESSION_VALIDATION.json` dosyasındadır.

Yeni ikili analiz iddiası yoktur. Kaynak bağları önceki298-talimat pending kimlik raporu ve172-talimat sınıf caller/timer raporundan alınır. UI/native C değiştirilmedi; UI yeniden test edilmedi. Native shared-memory, başka lock yazıcıları, queue drain, callback/timer otomatik erişimi, oyundaki etkiler ve canlı uyumluluk açık kalır.
