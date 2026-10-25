# Banka eşya okuyucusu — 19 Ekim 2026

`source_bank_item.py`, 0046fed8 yordamının normal işlem sırasını verilen gözlemlerle yeniden üretir. Oyun belleği okumaz ve koruma değiştirmez.

553e80 kökü, 5540bc ara ofseti ve 5540c0 slot ofseti sırasıyla alınır. Slot dörtle çarpılır; adres hesapları DWORD taşmasını korur. Yalnız kayıt pointer'ının sıfır olması erken sıfır dönüşüdür. Kayıt+60 ve kayıt+64 pointer'ları, değerleri okunmadan önce alınır. Sonuç temel değer ile unsigned varyantın 1000'e bölümünden kalanın toplamıdır; toplam DWORD'a sarılır.

Null adres ve koruma çağrısının açık başarısız sonucu bilinen sıfır olabilir. Eksik gözlem sıfır sayılmaz. Her ulaşılan adres ve örnek sırası denetlenir. API planının tamamlanması, özgün yordamın normal döndüğü anlamına gelmez.

`BankCountObservation.item_inputs`, bağımsız slot gözlemlerini 192 slotluk sayaca bağlar. Her slotun normal dönüşü ile dış sayacın normal dönüşü ayrıca istenir. Raw EAX ve bağlı gözlemin aynı ulaşılan slotta birlikte verilmesi reddedilir. BUY failure bu bağlı sayacı kullanabilir; arayüzdeki mevcut ham sayaç girdisi ayrı kalır.

On yeni test null/başarısız/bilinmeyen ayrımını, pointer sırasını, unsigned bölümü, adres taşmasını, eksik örnekleri ve BUY zincirindeki ayrı dönüş kapılarını kapsar. Tam test sonucu ve dosya hash'leri BANK_ITEM_READER_VALIDATION.json dosyasındadır. İki korunmuş sürümdeki 960 talimatlık mevcut kapsam yeni adres sabitlemeleriyle yeniden doğrulandı; bu sayı ek benzersiz talimat sayısı değildir. Kanıt Ghidra/disk denetimidir, REA Evidence çıktısı değildir.

Native koruma/okuma, fault ve eşzamanlılık etkileri, gerçek helper dönüşü ve canlı oyun uyumluluğu doğrulanmadı. Bu kapsam tüm botun tamamlandığı anlamına gelmez.
