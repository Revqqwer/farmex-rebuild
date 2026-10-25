# Gerçek Yenile düğmesine yerel bağlantı

`frmMain/MainTab/sheetQuest/btnRefreshQuests`, `ConfigurationPanel` üzerinden
`QuestRefreshFrame` akışını çalıştırır. Sağlayıcı
`set_source_quest_refresh_provider` ile açıkça bağlanır. Varsayılan sağlayıcı
yoktur; oyundan veri toplandığı veya native yardımcılara erişildiği varsayılmaz.
Sağlayıcı yokken düğme devre dışıdır.

Sağlayıcı ticket, profil nesli, ulaşılan faz, tarama indeksi ve eksik bilgiyi
taşıyan `QuestRefreshContext` alır; `QuestRefreshObservation` veya None döner.
Eksik bilgi mevcut kayıt/satır/NPC önekini korur. Kendi 100ms timer'ımız
devamı yürütür; bu süre native VCL zamanlamasının kanıtı değildir.

Gerçek panel listesi ve NPC seçenekleri ara sonuçlarla güncellenir. Sıralamada
görünen başlıklar koleksiyon indeksidir; tarama indeksleri değildir. Seviye
sütunu sayısal artan sıraya alınır. Eşit seviyelerde kararlı giriş sırası
bağımsız sürüm politikasıdır; native eşit anahtar sırası kanıtlanmamıştır.
Programatik NPC seçimi burada kaynak OnChange olayını taklit etmez;
NPC filtresi ayrı, henüz tamamlanmamış bir olaydır.

Yenile beklerken diğer üç metadata düğmesi bu görünüm üzerinde çalışmaz.
Metadata işlemi sürüyorsa yeni Yenile başlatılmaz. Form değişimi işlemi
iptal etmez; kayıtlar ve seçenekler tekrar çizimde korunur. Profil/sağlayıcı
değişimi veya panelin kapanması eski ticket'ı ve timer'ı geçersiz kılar.
Sağlayıcının profil değiştirdikten sonra döndürdüğü gözlem uygulanmaz.
Bekleyen liste/seçim dışarıdan düzenlenmişse otomatik üstüne yazılmaz.

GUI kontrolü gerçek düğmeyi çağırır; 30001 tarama içinde iki kabul edilmiş
kaydı koleksiyon başlıkları 1/0 ve seviyeler 5/80 olarak görüntüler. HEPSI/NPC
seçenekleri, seçim0, son temizlikte bekleme, başka forma geçiş ve geri dönüş,
aynı profil içinde dış düzenleme, eski profil yanıtı ve değişmeyen ortak
eylem kuyruğu denetlenir. Bu gözlemler yalnız kendi gizli Tk arayüzümüzdedir.
Orijinal bot veya oyun penceresi çalıştırılmaz.

Tam yerel test ve GUI kaydı `QUEST_REFRESH_UI_VALIDATION.json` içindedir.
API ayrıntıları `QUEST_REFRESH.md`, `QUEST_COLLECTION.md`,
`QUEST_LIST_EMIT.md`, `QUEST_COMPARE.md` belgelerindedir. Bu önceki API
belgelerindeki “UI henüz bağlı değil” notları kendi önceki aşamalarını anlatır;
bu belge ve güncel doğrulama kaydı Yenile'nin sonraki durumudur.

NPC filtreleme, görev ayrıntıları, seçili Al/Ver, otomatik oyun verisi,
native string/heap/SEH/VCL/concurrency ve gerçek oyun uyumluluğu açık kalır.
Yerel Yenile tamamlanması oyun tarafında görev alma/iptal etme onayı değildir.
