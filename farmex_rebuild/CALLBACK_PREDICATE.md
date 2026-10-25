# Callback koşul yordamı — 0046ebd0

Bu model açık kaynak gözlemlerinden koşul sonucunu hesaplar. Bellek okumaz, random üretmez, zaman almaz veya pointer değiştirmez. Adresler kaynak tanımlayıcılarıdır.

Güncel ve eski modülde74talimat dosya baytlarıyla doğrulandı. Farklı iki CALL aynı GetTickCount importuna gider. Ayrı kanıt: `FarmexBot_callback_kosul_kod_kaniti.json`. Bu kendi Ghidra/dosya kanıtıdır; REA runtime Evidence değildir.

`mode_byte` sıfırsa diğer kontrol alanları okunmaz. Ayrı DWORD `tick` ile taze QWORD `stamp_qword` farkı mod2^64 alınıp işaretli64 olarak yorumlanır. Fark300000 veya daha küçükse AL1; aksi halde AL0 planlanır. Negatif fark da bu kaynak dalında AL1 verir. Bu davranışa ürün anlamı atanmamıştır.

Mode nonzero olduğunda önce `enabled_byte` nonzero olmalıdır. Sonra sırayla `field_555dd8`, `field_555de4`, `field_555ddc`, `field_555de0` işaretli DWORD olarak negatif olmalıdır. İlk başarısız alan AL0 verir; sonraki bilinmeyen gözlemler istenmez. Bu dört alanın ürün anlamı henüz kanıtlanmadığından adres adları korunmuştur.

Kontroller geçerse `minutes_dword` okunur. Sıfırsa `00467cc4(3,20)` çağrı planı oluşturulur ve ayrı `random_return` gerekir. Bu helper'ın dağılımı veya üst sınır dahil olma davranışı burada varsayılmaz. Dönüş DWORD'u00553d30 alanına yazım planı olarak kaydedilir. Sonra yordamın kendi clock gözlemi ve taze stamp'i gerekir. Dakika çarpımı düşük32bitte yapılır; sonuç işaretli32 olarak64bite genişletilir. Zaman farkı bu eşikten küçük veya eşitse AL1 olur. Büyük minute değerleri taşabilir; Python sınırsız çarpım sonucu doğrudan eşik olarak kullanılmaz.

Her AL1 dalı00555e23 alanına BYTE1 yazımı planlar. AL0 bayrağı sıfırlamaz. Eksik random/clock/stamp durumunda AL bilinmeyen kalır; daha önce ulaşılan yazımlar yalnız planda görünür. Bu gerçek bellek etkisinin kanıtı değildir.

Mevcut callback ara bölüm JSON alanına örnek:

```json
{
  "initial_state": {"interval_dword": 1000, "last_attempt_qword": 0},
  "observation": {
    "tick": 3000,
    "session_stamp_qword": 0,
    "predicate_inputs": {"mode_byte": 0, "tick": 300000, "stamp_qword": 0},
    "flag_after_predicate": 1,
    "final_random_return": 70000
  }
}
```

`predicate_inputs` verildiğinde ayrıca `predicate_al` verilemez. Predicate kendi clock'unu kullanır; dış ara bölüm `tick` değeri onun yerine geçirilmez. AL1 ve bayrak yazım planı, çağıranın sonraki `flag_after_predicate` gözleminin yerine geçmez. AL0 veya taze bayrak0 dalında pointer helper hedefi ve normal dönüş gözlemi ayrıca gerekir. Sonraki kilit/mod/maden gözlemleri de bağımsız kalır.

Predicate snapshot'ı her çağrı için açık sağlanır. İçteki minutes yazımı otomatik olarak sonraki snapshot'a taşınmaz; bu model kaynak belleğinin sahibi değildir. Arayüzün kendi callback timer state'i ancak tam yerel zincir tamamlanınca kabul edilir. Kaynak snapshot'ının veya normal helper dönüşünün verilmesi canlı doğrulama değildir.

## Kaynak random hesabı bağı

Hazır helper dönüşü yerine ayrı gözlenen clock/srand dönüşü/rand EAX değerleriyle hesap seçilebilir. Şema, üç çağrı noktasındaki alan adları ve sınırlar [SOURCE_RANDOM.md](SOURCE_RANDOM.md) içindedir. Bu bağlantı gerçek RNG çalıştırmaz veya canlı doğrulama üretmez.
