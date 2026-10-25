# Görev koleksiyonuna ekleme — yerel API kapsamı

`quest_collection.py`, hazırlanmış bir `QuestRecord` kaydının koleksiyona
eklenmesini gözlemlerle ilerleyen bir yerel model olarak uygular. Bu aşama
oyuna bağlanmaz ve gerçek Yenile düğmesine henüz bağlı değildir.

Referans noktaları: Richard `004d7104` boyut, `004d712c` kapasite,
`004d7154` yerinde kopyalama ve `004d71b0` yeniden ayırma çağrıları.
Kaynak adresleri önceki ikili incelemeden gelir; bu ekleme yeni bir
decompiler veya canlı çalışma kaydı değildir.

- Başlangıç adresi sıfırsa kullanılmayan son adres okunmaz. Adres farkı
  32 bit sarma, işaretli bölme ve sıfıra doğru yuvarlamayla hesaplanır.
- Boyut ve kapasite ayrı gözlemlerdir. Dal seçimi işaretsiz karşılaştırmadır.
- Yardımcının normal dönüşü ve dönen son adres ayrı kanıtlardır.
- Yerinde eklemenin bilinen kayıt/son adres öneki, sonraki başlık gözlemi
  eksik olsa da korunur; devam çağrısı kaydı tekrar eklemez.
- Yeniden ayırmada büyüme miktarı veya bellek adresi üretilmez; sonraki
  başlık açıkça verilmelidir. Yerel kayıt sayısıyla uyuşmazlık çözülmemiş kalır.
- Eşzamanlı yerel kayıt/sürüm değişikliği çatışma olarak bildirilir.

`test_quest_collection.py` bu dal ve devam davranışlarını denetler.
Test sonucu gerçek native ayırıcı, ANSI referans sayımı, hata çözülmesi,
oyun erişimi veya tüm Yenile davranışının eşliği anlamına gelmez.

Koleksiyondan görev satırı üretimi ve NPC listesine ekleme sonraki yerel
API aşamasında eklendi; kapsam `QUEST_LIST_EMIT.md`. Kaynak sıralaması ve
bunların gerçek Yenile akışına bağlanması hâlâ açık.
Dağıtım ZIP'i ayrıca yeniden paketlenip doğrulanana kadar önceki
4776 testlik kayıt üretimi sürümüdür.
