# Al/Ver yerel kuyruk yayın katmanı

`quest_action_worker.py`, mevcut `QuestActionFrame` tarafından gözlemle üretilen
append öneklerini verilen ortak `QueueState` okuyucu/yazıcısına aktarır. Bu API
gerçek panelin Al/Ver düğmelerine bağlandı; gözlemler açık sağlayıcıdan alınır. Oyun veri sağlayıcısı,
native çağrı, gönderim veya sunucu onayı içermez.

Kaynak davranışının çözümü `QUEST_ACTION.md` ve önceki ikili kanıt raporlarıdır.
Yeni worker'ın hata/tekrar deneme/iptal politikası kendi uygulamamızdır;
orijinal botun native yarış veya istisna davranışı olarak sunulmaz.

- Append öneki, dış enqueue yardımcısının normal dönüşü eksik olsa da yayımlanır.
- Tamamlanma, hem action dönüşü hem yerel yayın doğrulanınca bildirilir.
- Yazıcı hata verdiğinde bekleyen aday korunur; yeni gözlem tüketilmeden çözülür.
- Önceki aday zaten tutulmuşsa tekrar yazılmaz. Sonradan eklenen kayıtlar korunur.
- Belirsiz yazım sırasında silme veya farklı değişiklik olursa kuyruk ezilmez;
  `queue_conflict` sonucu açık uzlaştırma ister. Drain ile yarış güvenliği
  kanıtlanmış değildir; okuyucu/yazıcı senkron ve aynı yerel sahipte olmalıdır.
- İptal, gerçekleşmiş öneki geri almaz; belirsiz yayın tekrarını durdurur.
- Tekrar giriş, frame'i veya yazıcıyı yeniden çalıştırmaz.

`test_quest_action_worker.py` içindeki 11 test, bu sözleşmenin başarılı akış,
önek, yazma öncesi/sonrası hata, araya ekleme, çakışma, noop yazıcı, iptal,
mevcut kayıt kimlikleri ve tekrar giriş senaryolarını doğrular.

Bu çalışma kaynak ağacındadır. Önceki yayımlanmış ZIP ve onun 4897 testlik
manifesti bu yeni worker'ı içermez; yeni sürüm paketlenmiş sayılmaz.

Tam yerel regresyon: 4908 test, başarılı süreç çıkışı 0. Log ve kaynak hashleri
`QUEST_ACTION_WORKER_VALIDATION.json` içindedir. Yeni GUI çalıştırılmadı.

Güncel UI: QUEST_ACTION_UI_VALIDATION.json. Tam yerel GUI yenilendi; gerçek
Al/Ver, ortak kuyruk, timer ve stale yanıt kontrolleri geçti. Önceki API
aşamasının GUI çalıştırılmadı notu tarihsel kayıttır.
