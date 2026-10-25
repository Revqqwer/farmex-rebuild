# Sınıf döngülerine typed chat tüketicisi bağı

20 Ekim 2026. Mevcut normal/legal sınıf başlığı modelleri `HelperReply.chat_consumer` alanında typed `ChatConsumerPlan` kabul eder. Yeni bağ, kaynakta doğrulanan altı çağrı slot'unun context ve dönüş kullanımı ayrımlarını korur. Eski/güncel kaynakta call-window/timer/direct zero-store kapsamında **172 talimat kaydı** doğrulandı; bütün başlıkların semantiği sertifikalanmadı.

| Başlık | Aile | Tüketici | Kaynak dönüş kullanımı |
|---|---|---|---|
| `0049bad0` | Mage normal | `004994bc` | lowAL nonzero destek dalını bitirir; yerel aralık650. |
| `0049b928` | Mage legal | `004994bc` | lowAL nonzero destek dalını bitirir; yerel aralık650. |
| `004d1be4` | Priest normal | `004cee18` | AL kullanılmadan sonraki `004d0eb0` yardımcısına devam. |
| `004d1d88` | Priest legal | `004cee18` | lowAL nonzero destek dalını bitirir; yerel aralık650. |
| `004de490` | Rogue normal | `004da568` | AL kullanılmaz; çağrı sonrası `561f7e` yeniden okunur. |
| `004dc544` | Rogue legal | `004da568` | lowAL nonzero destek dalını bitirir; yerel aralık500. |

“Legal” mevcut kaynak/UI aile adıdır; gerçek game-client uyumluluğu veya güvenlik kanıtı anlamına gelmez.

## Argüman ve dönüş sınırı

Altı çağrı da başlığın orijinal `[EBP+8]` argümanını push eder. `JobSnapshot.class_context_dword`, bu ham actor context DWORD'unun own gözlemidir; karakter/target ID'si değildir. Eksikse bağlı model `needs_observation` döner. Child context'i farklıysa hata verir; başka aile tüketicisi aynı adrese bağlanamaz.

Child eksikse olumlu legacy `returned_nonzero` onu aşamaz. Tamamlanan child da ayrı `HelperReply.normal_returned=True` gerektirir. Kaynak AL'ı kontrol ediyorsa child lowAL sonucu kullanılır; ayrıca verilen legacy bool bununla çelişemez. Kaynak AL'ı kullanmıyorsa ilgisiz bool'a anlam yüklenmez.

Normal Priest, başarılı child sonucundan sonra da sıradaki source yardımcısını çağrı planına ekler. Normal Rogue, child store listesindeki lock1projeksiyonundan otomatik post-lock üretmez; ayrı `locked_after` gözlemi gerekir. Böylece farklı caller sıraları tek bir “chat başarılıysa dur” kuralına çevrilmez.

Sonuçtaki `chat_consumers` tuple'ı source adresi ve child planını taşır. Child'ın varsa bağlı generic planı ve source hash/profil metadata'sı burada korunur. `class_family` yönlendirmesi bu bilgiyi kaybetmez. Legacy raw helper-reply denemesi ayrıca kullanılabilir; bu bağ UI'de henüz etkin değildir.

## Kilidin sıfırlanması

Mevcut `attack_lock.py`, `0046f991` timer bölümünü ayrı bir bounded model olarak kullanır. Source GetTickCount DWORD farkı32bit sarılır; elapsed unsigned olarak duration'a eşit veya büyük olduğunda `561f7e=0` yazılır.

Keşfedilmiş yordamların doğrudan literal zero-store taramasında timer `0046f9ad` yanında Rogue combo gövdesindeki `004e0811` de doğrulandı. Bu nedenle lock için yalnız timer sonucundan bütün kaynak yazımlarını bildiğimiz iddia edilmez. Alias/register üzerinden, generated veya keşfedilmemiş yazımlar ve başlangıç zero-initialization bu taramanın dışındadır. Yeni bağ, çağıranın istediği taze lock gözlemini bu nedenle korur.

## Doğrulama ve sınır

**12 yeni entegrasyon testiyle toplam2869 test geçti (7.089 saniye).** Altı source slot'u, support interval sonuçları, normal Priest devamı, normal Rogue taze lock gereği, incomplete-child/parent-normal ayrımı, context/family uyuşmazlığı, yalnız kullanılan AL'da tutarlılık, family-router metadata devamı ve legacy yol sınandı.

Mevcut head modellerinin finite-float, monotonic-time ve stable named-observation sınırları korunur. Yeni172kayıtlık kaynak kanıtı, yalnız bu yeni call-slot bağı ve belirtilen timer/store gözlemlerine aittir; bütün head gate/FPU/timer davranışının canlı eşdeğerliğini kanıtlamaz.

UI/native C değişmedi; UI yeniden test edilmedi. Gerçek callback kurulumu, producer→consumer ortak pending ömrü, helper/native skill/server sonuçları ve canlı uyumluluk açıktır. Hiçbir süreç, native target veya oyun eylemi yürütülmedi.

Kaynak: `outputs/FarmexBot_sinif_chat_cagiran_kaniti.json`; üretici `work/audit_class_chat_callers.py`. Uygulama kaydı `CLASS_CHAT_BINDING_VALIDATION.json`.
