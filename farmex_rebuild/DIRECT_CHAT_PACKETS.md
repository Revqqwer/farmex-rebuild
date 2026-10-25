# Doğrudan TP ve Priest ortak kayıt üretimi

20 Ekim 2026. `direct_chat_packets.py`, Mage TP `0049e8c8`, Priest ortak `004d3568` ve Cure/Disease wrapper'ları `004d3674`/`004d3690` için normal-yol byte üretimini ve iki aşamalı **yerel kuyruk** frame'ini uygular. Eski/güncel kaynakta **446 talimat kaydı**, dört template kopyası ve `_memcpy` import kimlikleri doğrulandı. Bu Ghidra/PE kanıtıdır; yeni REA Evidence veya gerçek wire-format/delivery kanıtı değildir.

## Getter ve alan sırası

Class helper `0046256c` ham EAX'ından low32 `class*1000+relative` hesaplanır. Actor getter `00462650` ham DWORD'u ayrı gözlemdir. TP relative4, Cure525, Disease535kullanır; Priest ortak helper relative'ı argümandan alır. Context DWORD'u source argüman kimliği olarak korunur; kaynakta kullanılmayan context alanlarına anlam uydurulmaz.

| Yardımcı | İlk kayıt | İkinci kayıt | Hedef kopyası |
|---|---|---|---|
| Mage TP | 48bayt / delay0 | 34bayt / delay1500 | DWORD, offset10 |
| Priest ortak / Cure / Disease | 48bayt / delay0 | 26bayt / delay1500 | WORD, offset10 |

Her iki kayıtta actionDWORD offset2, actorDWORD offset6'ya kopyalanır. TP ikinci kaydında X/Y/Z getter EAX DWORD'ları offset14/18/22'ye konur. Bunlar ham helper sonuçlarıdır; float veya başka koordinat türüne çevrilmez. Kullanılmayan template baytları, ilk kayıttaki sabit `0f` dahil, aynen korunur. Oyun protokolüne ilişkin dış varsayımlarla field width/offset düzeltilmez.

Priest ortak helper, class ve actor getter'larından **sonra** target'ın düşük WORD'unu kontrol eder. Sıfırsa kuyruk kayıtları oluşturulmadan normal return bölgesine geçer. Üst16bit nonzero olsa da bu guard değişmez. TP'de aynı zero-target guard'ı yoktur. Cure/Disease wrapper'ları partial EAX push etse de ortak helper yalnız target WORD'unu okur/kopyalar; bu aşama o üst register bitlerini packet alanına taşımaz.

## Kendi kuyruğumuzdaki devam

`DirectChatPacketFrame`, source argümanlarını sabit tutar; getter normal dönüşlerini ve ham EAX değerlerini ulaşılan sırada tüketir. Son getter eksikken önceki class/actor/koordinatlar değişmez. Her iki byte dizisi ilk enqueue öncesinde hazırdır.

İki enqueue'nun gate ve tick örnekleri ayrı, konumsal `QueueAttempt` gözlemleridir. Bilinen nonzero gate, tick eksikken korunur. Gate0o kayıt için bilinen copy-atlamasıdır; sonraki source enqueue yine yürüyebilir. İlk copy gerçekleşip ikinci gate/tick veya normal dönüş eksikse ilk yerel kayıt korunur.

Copy sonucu, enqueue helper'ının ayrı `normal_returned` gözleminden önce own queue'ya eklenebilir. Aynı helper dönüşünü beklerken yeniden adımlama kaydı çoğaltmaz. İki enqueue tamamlandıktan sonra ayrı `return_span` normal gözlemi gerekir. Tamamlanan aynı frame yeni kayıt eklemez. Bu frame gerçek queue'yu boşaltmaz; sender çağırmaz, server ACK üretmez.

Zero-WORD Priest skip'inde mevcut own queue korunur. Kaynak return EAX'ı anlamlı bir başarı bool'u olarak çözümlenmediğinden sonuç bunu doğrulanmış göstermez. Bu özellikle source tüketicinin üstte kendi AL sonucunu oluşturmasıyla karıştırılmaz.

## Doğrulama

**12 yeni testle toplam2881 test geçti (7.076 saniye).** Exact uzunluk/delay/field width, korunmuş template alanları, class taşması, fixed relative'lar, getter-before-zero guard, her getter boşluğu, ilk kaydın korunması, helper dönüşünden önce tek copy, bağımsız gate'ler, geç coordinate/tick ve return-span devamı sınandı.

UI/native C değişmedi; UI yeniden test edilmedi. Str/Rogue SW/Wolf doğrudan builder'ları ve tüketici alt-model bağları bu aşamada eklenmedi. Native allocation/code/protection işlemi, gerçek network gönderimi veya skill/server sonucu yoktur.

## Canlı oturum kontrolü

20 Ekim **16:52:46 UTC** host süreç metadata sorgusu274süreç listeledi; Knight/Farmex/Loader adıyla eşleşme0dı. Gözlemci Windows token'ı admin değildi. Bellek okuma/yazma ve oyun eylemi0olarak kaydedildi; bu kontrolde canlı teste geçilmedi. Bu sonuç yalnız belirtilen anda/isim kapsamındaki envanterdir; kalıcı oyun durumu iddiası değildir.

Kaynak: `outputs/FarmexBot_dogrudan_chat_paket_kaniti.json`; üretici `work/audit_direct_chat_packets.py`. Oturum kaydı `outputs/FarmexBot_canli_oturum_20261020.json`; uygulama kaydı `DIRECT_CHAT_PACKETS_VALIDATION.json`.
