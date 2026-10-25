# Generic alt modelin sınıf tüketicilerine bağı

20 Ekim 2026. Mage/Rogue/Priest tüketicileri, `ChatConsumerObservation.generic_execution` alanında isteğe bağlı typed `GenericSkillPlan` kabul eder. Mevcut raw normal/EAX gözlem yolu korunur. Alt model verildiğinde source `004655e8` sınırı için eksik çocuğu üst normal dönüşle aşmak mümkün değildir.

## Bağ kuralları

Bağ yalnız kaynak generic dalına gerçekten ulaşıldığında değerlendirilir. Direct yol, pending0veya erken başarısızlık nedeniyle generic'e ulaşılmıyorsa o çocuğun argümanları kullanılmaz. Ulaşılan çağrıda relative skill ve **tam target actor DWORD** üst source argümanlarıyla aynı olmalıdır.

Alt model eksikse tüketici `bound generic: ...` boşluğunda durur; delay/lock/pending-clear adımlarına geçmez. Tamamlanan alt model yine ayrı üst `generic_skill` normal dönüşü ve `generic_skill_eax` gözlemini gerektirir. Bu üst ham EAX, alt modelin döndürdüğü ham EAX ile tam eşleşmelidir. `100` gibi düşük BYTE'ı0ama full DWORD'u nonzero sonuçlar bool'a erken daraltılmaz.

Bilinen child/parent EAX0durumunda source false yolu seçilir ve generic başarısızlığında pending korunur. Önceki hedef/hareket yardımcısının etkileri geri alınmış sayılmaz. Bu etkiler zaten gerçek yürütme kanıtı değildir.

Tam sonuç `ChatConsumerPlan.generic_execution` alanında korunur; bu alan actual helper kimliğini, lookup/dispatch operand planını, ham sonucu ve varsa source hash/profil metadata'sını taşır. Alt metadata, ham parent gözlemlerini otomatik olarak canlı veya sürüm eşleşmesi doğrulanmış native context'e dönüştürmez.

## Frame devamı

`ChatConsumerFrame`, generic sınıra ulaştığında alt snapshot'ı bağlar. Eksik alt model sonraki adımda daha fazla gözlemle tamamlanabilir. Önceden verilen class EAX, argümanlar, source/profil kimliği, map anahtar/değerleri ve bilinen ham dönüşler değişemez. Olumlu normal-dönüş makbuzu geriye alınamaz. Yeni map anahtarları veya daha önce eksik raw dönüşler eklenebilir.

Bu **kararlı own snapshot enrichment** sözleşmesidir; native talimatlar arasında değişen bütün gerçek global okumaların emülasyonu değildir. Önceden verilmiş ama kaynakta henüz kullanılmamış bir map alanı da bu own sözleşmede kararlı kabul edilir. Farklı snapshot veya profil için yeni frame gerekir.

Tamamlanmış child daha geç tick/helper boşluğunda tekrar değiştirilmez. Önceki consumed sonuç ve metadata korunur; tamamlanan aynı parent frame tekrar çağrı veya store uygulamaz. Bütün planlar inerttir; native çağrı/store uygulanmaz.

## Doğrulama

**12 yeni entegrasyon testiyle toplam2857 test geçti (7.015 saniye).** Mage1/Rogue2/Priest6 olmak üzere dokuz generic çağrı noktası; eksik child'ın üst dönüşle aşılamaması, ayrı parent normal, exact EAX0/nonzero, yanlış relative/actor, geç child tamamlama, değişen class/map reddi, sonraki tick boşluğunda child koruma ve current source metadata devamı sınandı.

Mevcut üç kaynak audit'i tüketilir: generic wrapper96kayıt, Mage/Rogue482kayıt, Priest1336kayıt. Bu aşamada yeni ikili talimat analizi eklenmedi. UI/native C değişmedi; UI yeniden test edilmedi. UI/compiler271 ve envanter dışında251yol aynı; bunlar özellik tamamlanma yüzdesi değildir.

Callback önceliği, gerçek producer→consumer pending ömrü, native/callee ABI ve skill/server sonucu hâlâ açık. Bu entegrasyon deneme UI'sine henüz bağlı değildir. Başarılı birim testleri canlı uyumluluk veya gerçek skill başarısı sayılmaz.

Makine kaydı: `GENERIC_CONSUMER_BINDING_VALIDATION.json`. Alt kaynak kapsamları: [generic wrapper](GENERIC_CHAT_SKILL.md), [Mage/Rogue](CHAT_SKILL_CONSUMERS.md), [Priest](PRIEST_CHAT_CONSUMER.md).
