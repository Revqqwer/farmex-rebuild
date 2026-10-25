# Parti kabul/ret kaydının üst akışa bağı — 19 Ekim 2026

004ca770 ve 004ca7b4 yardımcılarının kaydı kaynakta sabittir: kabul `2f0201`, ret `2f0200`. Her biri WORD ve BYTE literal yükleyip toplam3baytı delay0 ile004c7710'a verir. Davetçi kimliği veya isim bu kayda eklenmez.

`PartyReplyFrame` kayıt üretimini yalnız own kuyruk üzerinde uygular. Gate/tick eksikse sonuç bilinmeyen kalır. Gate0 bilinen skip'tir ve daha sonra farklı gate verilince tekrar enqueue yapılmaz. Tam plan exact action/payload ve bilinen own enqueue sonucu ister. Bu tamamlanma, native helper'ın döndüğü anlamına gelmez.

Parti daveti karar modeli typed `reply_execution` kabul eder. Sadece ulaşılan kabul/ret dalında kind eşleşmesi ve alt plan tamamlanması denetlenir. Üstteki accept/reject normal dönüşü ve isim cleanup dönüşü ayrıca gerekir; bu işaretler eksik alt planı atlayamaz. Eski raw-helper gözlem yolu ayrı kalır.

`PartyInvitationFrame`, tek captured çağrı için config ve bytes'ı sabitler. O anda gerçekten tüketilen scalar/filter/normal-return önekleri saklanır. Reply çerçevesi yalnız kaynak action dalına ulaşıldığında oluşturulur. Queue kaydı hazır olup üst dönüş veya cleanup gözlemi eksik kaldığında tekrar enqueue edilmez. Sonraki packet için ayrı çağrı çerçevesi gerekir.

11 yeni test dahil **2630 yerel test, 6.496 saniye** geçti. Üç bayt içerikleri, gate/tick boşlukları, gate0 skip, action-kind uyuşmazlığı, bağımsız üst dönüşler, erken bloke yollarının enqueue yapmaması ve önekten devam/tekrar kayıt engeli sınandı.

İki korunmuş ikilide yardımcıların84talimat kaydı ile altı literal bayt doğrulandı. Frame setup ve gerçek queue/native yan etkileri bu kanıtla tamamlanmış sayılmaz. Kapsamlar önceki denetimlerle örtüşebilir; Ghidra/disk kanıtıdır, REA Evidence değildir.

Yeni bağ API kapsamındadır. Mevcut UI raw-helper denemesi değişmedi; bu tur UI testi tekrarlanmadı. Gönderici, gerçek kabul/ret, dış hook davranışı ve parti üyeliği doğrulanmadı. Ağ yanıtı gönderilmedi.
