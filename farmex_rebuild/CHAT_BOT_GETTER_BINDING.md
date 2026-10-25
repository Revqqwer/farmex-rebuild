# Chat ve bot durdurma getter bağları

21 Ekim 2026. `ChatCommandsObservation.getter_executions` içindeki genie_start_state/genie_remaining/genie_stop_state ve `BotSwitchObservation.getter_executions` içindeki stop_genie_state, isteğe bağlı generated `GenieGetterPlan` kabul eder. Genel/Notice worker'ındaki önceki7çağrıya ek4çağrı noktasıdır.

Getter helper kimliği ve generated snapshot/result tutarlılığı kontrol edilir. Eksik child, üst normal/raw EAX ile atlanamaz. Tam child olsa da üst helper normal dönüşü gerekir ve raw EAX birebir aynı olmalıdır. Kaynak kararında hâlâ yalnız gereken düşük AL kullanılır: start state için nonzero, stop için tam1. Aynı lowAL'ye sahip farklı full EAX gözlemleri tutarlı sayılmaz.

Chat frame'inde yalnız ulaşılan getter planları tüketilir. Örneğin start blocked bayrağı açıksa yanlış start-state child incelenmez; state nonzero ise remaining child tüketilmez. Aynı chat planında ulaşılan getter'lar kaynak hash/profil karıştıramaz. Bot-start yolunda stop-state child tüketilmez. Consumer helper argümanları ve wrapper/üst normal sınırları ayrı kalır.

Frame eksik child zenginleştirilirken tüketilmiş global/root/field gözlemlerini korur. Child tamamlandıktan sonraki movement veya action dönüş boşluğunda yeni child onu değiştirmez. Bot stop getter'ı eksikse sonraki stop context/global reset'leri ve stop movement henüz üretilmez; önceki source store projeksiyonları korunur.

Bot-switch kendi içinde bu getter'ı bağladıktan sonra chat action child'ı olarak kullanılabilir. Chat'in ayrı `action:bot_stop` normal dönüşü yine gerekir. Nested action/caller arasında bütün kaynak/profile kimliklerinin tek bir global invocation sertifikasıyla birleştiği iddia edilmez; bu ek kapsam açık kalır.

10yeni test dört çağrı noktasını, eksik child/ayrı üst dönüşünü, full EAX ve lowAL ayrımını, tüketilmemiş dalları, source/profile uyuşmazlığını, frame enrichment ve completed-child korumasını, chat→bot action sınırını kapsar. Son tam koşu ve geniş gizli UI sonucu `CHAT_BOT_GETTER_BINDING_VALIDATION.json` dosyasındadır.

Yeni ikili audit yoktur; mevcut184talimat getter/profile raporu ve önceki chat/bot kaynak aralıkları kullanılır. Çıktılar korunmuş Ghidra/PE kanıtıdır, yeni REA Evidence değildir. UI kontrolleri/JSON adaptörü değiştirilmedi; mevcut ham gözlem modu korunur ve typed getter seçeneği henüz UI'den toplanmaz. Regresyon için gizli UI tekrar çalıştırılır. Native C, gerçek read/protection/Genie eylemi ve canlı uyumluluk doğrulanmadı.
