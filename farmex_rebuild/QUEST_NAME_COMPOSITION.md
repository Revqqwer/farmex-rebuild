# ANSI karşılaştırma -> görev arama -> Al/Ver

`QuestLookupObservation.name_compares`, iteration ordinal'ına göre typed
`QuestNameCompareObservation` kabul eder. Böylece mevcut Al/Ver sağlayıcısı
aynı nested lookup gözlemi içinde ANSI karşılaştırmanın iki ayrı LStrCmp
çağrısını, flag'lerini ve normal dönüşlerini de taşıyabilir.

Her ulaşılan satırın name_compare girişinde gözlem kaynağı ayrı seçilip
kilitlenir. Nested örnek varsa model kullanılır; yalnız ham EAX varsa açık
yakalanmış dönüş kullanılır. İkisi de yoksa name_compare_input beklenir.
İç karşılaştırma beklerken ham EAX vermek bu beklemeyi atlamaz. Null kayıt
veya metadata yolunda nested karşılaştırma hiç tüketilmez.

İç modelin clean0/1 sonucu hazır olsa bile lookup caller'ının ayrı
`(ordinal, name_compare)` normal dönüş receipt'i gerekir. Ancak bundan sonra
nation/class filtreleri, mode okuması, name cleanup ve kalan tarama ilerler.
Nested planlar lookup planında ordinal/plan çiftleriyle tutulur; parent context
eksik ANSI aşamasını da taşıyabilir. Retry iç çağrıları yeniden üretmez.

Gerçek Al/Ver düğmelerinde eşitlik dönüşü boşluğu sırasında filtre/kuyruk
ilerlememesi, timer ile devam ve sonraki iki akış test edilir. 10 yeni test;
toplam4960 test ve tam GUI sonucu `QUEST_NAME_COMPOSITION_VALIDATION.json`
içindedir. Kaynak kanıtı iki PE'de1862 komut ve ANSI LStrCmp importudur.

Unicode decode/case-fold fallback eklenmez. Captured flags varsayılan olarak
korunur; owned-byte yolu post-load ANSI snapshot'ları için açık bir yerel
politikadır. Ad okuma helper'ının IsBadReadPtr/memcpy/constructor/assignment/
cleanup alt üreticisi, native refcount/RTL/SEH/FPU, otomatik oyun gözlemleri
ve gerçek gönderim hâlâ açık. Eski belgelerdeki "API henüz bağlı değil"
notları önceki aşamayı anlatır.
