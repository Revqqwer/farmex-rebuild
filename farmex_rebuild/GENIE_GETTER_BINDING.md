# Genie okuyucularının worker çağrılarına bağı

Sonraki aşama:3chat ve1bot-stop getter çağrısı da optional typed child ile bağlandı. Güncel kapsam [CHAT_BOT_GETTER_BINDING.md](CHAT_BOT_GETTER_BINDING.md); aşağıdaki önceki aşama notları tarihsel sınırları korur.

21 Ekim 2026. `GenieWorkerObservation.getter_executions` ve `NoticeGenieObservation.getter_executions`, etiket bazında isteğe bağlı `GenieGetterPlan` taşır. Genel girişte initial_remaining/always_state/always_remaining/general_remaining, Notice bölümünde start_state/remaining/stop_state olmak üzere7çağrı noktası bağlanır.

Bağlı child, ulaşılan kaynak helper kimliğiyle eşleşmelidir. Generated input snapshot yeniden saf planner'dan geçirilerek complete/rawEAX/lowAL/steps/request ve native flags doğrulanır. Eksik child, üst helper'ın olumlu normal dönüşü veya ham EAX'iyle atlanamaz. Tam child olsa da üst helper normal dönüşü ve full raw EAX ayrıca gerekir; lowAL aynı diye farklı üst bitler kabul edilmez.

Ulaşılan bağlı getter'ların kaynak hash/profil kimliği aynı olmalıdır. `GenieWorkerFrame` bu kimliği genel prefix'ten Notice tail'ine de taşır. Bu doğrulama her çağrıda aynı canlı root/byte değerini zorlamaz: taze kaynak çağrıları farklı raw EAX döndürebilir. Ancak bir getter invocation'ı eksik sonuçtan zenginleştirilirken tüketilmiş global/root/read prefix'i değiştirilemez.

Tamamlanmış child, daha sonraki outer saat/return boşluğunda korunur. Geç gelen farklı child, tamamlanmış önceki gözlemi sessizce değiştirmez. Reached helper/profil kontrolü dal koşullarından sonra yapılır; ulaşılamayan başka getter planı tüketilmez. Kaynak/profile çelişkili child cache'e alınmadan plan doğrulaması reddedilir.

Child verilmeyen legacy opaque normal/raw gözlem yolu korunur. Bu yol bağlı root/byte okumasını kanıtlamaz. Source hash/profil metadata'sı da yüklü module/runtime kimliği olarak yorumlanmaz. Native execution ve protection flags hiçbir yolda başarı sertifikasına çevrilmez.

11yeni test yedi çağrı noktasını, eksik child/ayrı parent dönüşünü, üst-bit EAX uyuşmazlığını, yanlış helper'ı, consumed root değiştirmeyi, aynı worker ve prefix/tail arasında kaynak/profile uyuşmazlığını, geç clock boşluğunda tamamlanmış child korumasını, taze farklı byte'ları ve generated/native claim tutarsızlığını kapsar. Son tam koşu `GENIE_GETTER_BINDING_VALIDATION.json` dosyasındadır.

Yeni ikili audit yoktur. Bağ önceki184talimat getter/profile kanıtı ile594talimat worker kanıtını kullanır; bunlar korunmuş Ghidra/PE çıktılarıdır, yeni REA Evidence değildir. Chat komutları ve bot-switch'teki ayrı getter tüketicileri bu aşamada bağlanmadı. UI/native C değişmedi, UI yeniden test edilmedi. Gerçek read/VirtualProtect/Genie etkisi, callback ve canlı uyumluluk açık kalır.
