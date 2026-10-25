# Normal chat bölümlerinin sıralı bağı

21 Ekim 2026. `ChatHandlerSegmentsFrame` tek, sabit ve sınırlı ayrıştırılmış chat mesajında giriş/log → sekiz komut → parti daveti → skill isteği → ortak temizleme modellerini sırayla tüketir. Her bölümün kendi frame'i korunur. Önceki bölüm tamamlanmadan sonraki constructor, gözlem veya enqueue seçenekleri değerlendirilmez. Tamamlanmış önceki bölümün daha sonra gönderilen geçersiz verisi yeniden tüketilmez.

`work/audit_chat_segment_joins.py`, kaynak normal CFG üzerinde komutların bütün çıkışlarının456804'e, parti dalının çıkışlarının4569d9'a gittiğini doğrular. Skill producer iki çıkışa sahiptir:457014bildirim dalı veya45730eortak temizleme. Temizlemenin normal grafiği457384RET'te sonlanır. Eski/güncel toplam1426 talimat kaydı dosya baytlarıyla kontrol edildi; bu önceki bölgelerin tekrar kapsanmasıdır. Yeni sonuç, normal akışların birleşme özelliğidir. Helper'ların normal döndüğü varsayımı, exception ve çağrı etkilerinin doğrulanması değildir.

Skill planı457014'e giderse parent `unmodeled_notice_tail` ile durur; cleanup snapshot'ı veya olumlu normal dönüşler bu boşluğu atlatamaz. Bu kapsamda bildirim dalının oyun/süreç eylemleri otomatikleştirilmez. Eksik/başka opcode prefix'i sonraki bölümleri başlatmaz.

Komut action'ı oluştuysa parti dalından önce bağımsız, açık bir `after_commands_queue` yerel snapshot'ı gerekir. Helper'ın normal dönüşünden yeni kuyruk içeriği türetilmez. Snapshot ilk kuyruk kayıtlarını aynı sırayla korumalıdır; bu bizim provenance sınırımızdır. Sonraki parti davetinin iki enqueue adımı bu kuyrukla başlar. Skill veya temizleme eksik kaldığında parti kayıtları korunur ve devamda çoğalmaz. Bu yerel queue snapshot'ı gerçek native queue sahipliği veya ağ teslimi değildir.

Temizleme için orijinal EBP/yerel DWORD snapshot'ı ayrıca gerekir; başka helper'ın caller frame'i veya yerel kayıt buffer'ı yerine geçirilmez. Eksik temizleme normal dönüşünde önceki log/komut/davet/istek tekrar yürütülmez.

Sekiz yeni test PM normal zincirini, eksik önceki bölümde sonraki bozuk girdinin tüketilmemesini, runtime gate kapalıyken temizliğe ilerlemeyi, bildirim dalında durmayı, post-command queue prefix'ini, geç skill boşluğunda davet kayıtlarını ve kısmi cleanup devamını sınar. Tam koşu `CHAT_HANDLER_SEGMENTS_VALIDATION.json` dosyasında kayıtlıdır.

Kaynak `outputs/FarmexBot_chat_bolum_gecis_kaniti.json`; korunmuş Ghidra/PE normal-CFG kanıtıdır, yeni REA Evidence değildir. Sonuç `complete`, yalnız seçilmiş normal bölümlerin açık gözlemlerle tamamlandığını gösterir. Full handler, EAX, native string/heap/FS etkisi veya canlı eşdeğerlik doğrulanmış sayılmaz. UI/native C değişmedi; UI yeniden test edilmedi. Gelen-paket işleyicisinin ayrı whole-handler normal dönüşü bu sonuçla otomatik değiştirilmez.
