# Görev arama -> Al/Ver -> ortak yerel kuyruk

`QuestActionObservation.lookup` typed `QuestLookupObservation` kabul eder.
Gerçek Al/Ver düğmelerinin mevcut sağlayıcısı bunu doğrudan taşıyabilir;
panel için ayrı bir sahte başarı veya sabit ID bağlantısı eklenmedi.

İlk ulaşılan lookup girişinde iki açık kaynak ayrılır. Typed iç gözlem varsa
composed tarama seçilir; yalnız ham `lookup_eax` varsa dış dönüş yakalaması
seçilir. İkisi de yoksa `lookup_input` beklenir. Seçilen yol o invocation için
kilitlenir. İç tarama beklerken ham EAX vererek atlamak mümkün değildir.
Eski ham-EAX fixture'ları dış gözlem aktarımını sınamaya devam eder; pinned
004d642c kodunun başka normal dönüşü olduğu iddiası değildir.

Composed yol, gerçek kayıt caption'ından türetilen display-name snapshot'ı,
Al mod4 / Ver mod3, source-index eksi4 ve source-index sınırlarını child'a verir.
Child'ın normal devamı bitmeden EAX ve ilk kuyruk kaydı oluşmaz. Tamamlanan
child'ın FFFFFFFF sonucu bile caller'ın ayrı `lookup_eax` normal dönüş
receipt'ini atlamaz. İlk istek böylece düşük WORD olarak FFFF içerir.

Parent plan `lookup_plan` ile iç çağrı/read/compare önekini taşır. Eksik iç
gözlem provider context'ine `(lookup, phase, indexDWORD, ordinal, needed)`
olarak ulaşır. Retry, child frame'i veya source çağrı token'larını yeniden
üretmez. İki stage de bitince mevcut script/gate/tick/append önekleri ve ortak
kuyruk yayıncısı devam eder. Gönderim veya oyun başarısı üretilmez.

10 yeni test; toplam4933 test. Gerçek Al/Ver düğmeleri, iç argument-cleanup
boşluğu, kuyruk öncesi bekleme, context, timer devamı ve FFFF alanı tam yerel
GUI'de yeniden kontrol edilir. Güncel sonuç `QUEST_LOOKUP_COMPOSITION_VALIDATION.json`
içindedir. Mevcut üç native fonksiyon için1578 komut kaydı iki PE'ye sabitlendi.

Bu normal-flow birleşimidir. Native helper/read/string/equality/FPU/refcount/
SEH/istisna ve çalışma zamanı patch davranışları, otomatik canlı gözlem ve
oyun gönderimi hâlâ doğrulanmış değildir. Önceki lookup-API belgelerindeki
"henüz caller'a bağlı değil" notları tarihsel aşamayı anlatır.
