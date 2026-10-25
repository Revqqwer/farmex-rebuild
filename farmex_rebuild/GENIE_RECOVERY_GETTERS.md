# Yenileme taramasında envanter okuyucuları

`RecoverySlotSample.name_inputs` ve `item_inputs` isteğe bağlı typed gözlemlerdir. İsim için mevcut 00463670→00467908→0045dca8 operand modeli, kimlik için ayrı ve taze 004634a4 modeli çağrılır. İki çağrıya da taramanın gerçek mutlak slotu14..41 verilir. İsim hesaplanırken üretilen itemID daha sonraki taze kimlik okumasının yerine geçmez.

Alt gözlem varsa sonucun eksikliği, ayrıca sunulan ham isim/kimlik ile kapatılamaz. Tamamlanan alt sonuç ham sonuçla çelişirse reddedilir. Eksiksiz typed sonuç ham değer olmadan da kullanılabilir. Dış yardımcı dönüşleri ve kaynak eşitlik sonucu ayrı gözlemlerdir; varsayılan mod native RTL karşılaştırmasını taklit etmez.

`InventoryGetterFrame` mevcut saf modelleri yalnız ihtiyaç duyulan operandları sırayla alarak ilerletir. Slot/global/pointer/kimlik ve iç isim okumasında tüketilen alanlar korunur. Eksik byte yakalaması aynı prefix ile genişleyebilir; önceki byte'lar değiştirilemez. Henüz okunmamış alanlar otomatik tüketilmez. İlk eşleşmede ayrı kimlik0 dönmesi taramayı durdurur; isim kopyasının çözülemeyen taşma/sonlandırma yolu boş isim veya başarı sayılmaz.

Sekiz yeni test; ayrı isim/kimlik snapshot'ları, gerçek slot adresleri, eksik alt sonuçta ham fallback engeli, çelişkili sonuç reddi, tüketilmiş kimlik alanının korunması, isim byte prefix devamı, kaynak taşma boşluğu ve eşleşmeyen isimde kimlik okuyucusunun atlanmasını kapsar. Son tam koşu3012 testtir. Dört yardımcı gövdesinde eski/güncel toplam1106 talimat kaydı yeniden disk doğrulandı; bu yeni ikili envanter kapsamı veya tam fonksiyon sertifikası değildir.

Bu modeller oyun okumaz. İç guarded-read/RTL dönüşleri modellenmiş yerel snapshot varsayımıdır; gerçek koruma/bellek/RTL etkisi doğrulanmadı. Kaynak hash/profil kimliğinin bütün iç okuyuculara taşınması ve ortak worker-session kuyruğu hâlâ açıktır. UI değiştirilmedi ve yeniden sınanmadı; native gönderim, eşya tüketimi ve oyunda Genie etkisi doğrulanmadı. Kaynak korunmuş Ghidra/PE verisidir; yeni REA Evidence değildir.
