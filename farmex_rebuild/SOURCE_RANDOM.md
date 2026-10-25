# Kaynak aralık hesabı — 00467cc4

`source_random.py` açık saat/CRT gözlemlerinden yardımcının DWORD dönüş hesabını yapar. Gerçek saat veya random üreticisi çağırmaz; CRT state'i oluşturmaz ya da seed etmez.

Eski ve güncel modülde 20 talimat dosya baytlarıyla doğrulandı. Değişen üç CALL aynı GetTickCount, _srand ve _rand import kimliklerine gider. Kaynak kanıtı `FarmexBot_random_yardimci_kod_kaniti.json` dosyasındadır; bu kendi Ghidra/dosya kanıtıdır, REA runtime Evidence değildir.

Yordam kendi GetTickCount sonucunu `_srand` argümanı yapar; normal dönüşten sonra `_rand` çağrılır. Model her ulaşılan çağrı için ayrı `tick`, `srand_returned=True` ve raw DWORD `rand_eax` ister. Aynı snapshot'a sonradan rand değeri eklemek, önceki eksik seed dönüşü gözlemini tamamlamaz. Dış callback veya predicate tick değeri helper saatinin yerine geçmez.

Hesap:

1. Üst sınır eksi alt sınır artı 1 düşük32bitte hesaplanır ve işaretli32 bölen olarak yorumlanır.
2. Rand EAX işaretli32 alınır. `CDQ; IDIV ECX` biçimi nedeniyle bölüm sıfıra doğru kesilir; kalan bölünenin işaretini taşır. Python'un negatif sayılardaki `%` sonucu doğrudan kullanılamaz.
3. Kalana alt sınır düşük32bitte eklenir; sonuç DWORD olarak döner.

Kaynak ters sınırları doğrulamıyor. Genel API bu yüzden ters sınırları kendiliğinden reddetmez. Sıfır bölen ve INT_MIN/-1 bölüm taşması normal dönüş üretmez; ayrı fault planı verir. Bu, gerçek bir exception çalıştırılması değildir. Üç bağlı kaynak çağrısının sabit 3..20 ve 60000..300000 sınırlarında bölenler pozitif ve sıfırdan farklıdır.

Nonnegative rand girdileriyle aritmetik aralık iki ucu dahil olacak şekilde hesaplanır. Gerçek `_rand` çıktılarının hangi değerlere ulaşabildiği ve dağılımı ayrıca doğrulanmalıdır. Örneğin üst uç için kullanılan sentetik test girdisi, yüklü CRT'nin o girdiyi üretebildiğinin kanıtı değildir. Ham EAX gözlem yolu RNG algoritması varsaymaz. Bulunan dosyanın isteğe bağlı ayrı CRT replay kapsamı aşağıdadır; gerçek oturum RNG dizisi doğrulanmadı.

## Callback JSON bağı

Eski açık dönüş alanları kullanılabilir. Yerine aşağıdaki alanlar verilirse dönüş kaynak hesabından çıkarılır:

- `initial_random_inputs`: ilk aralık yardımcısı; `initial_random_return` ile birlikte kullanılamaz.
- `final_random_inputs`: son aralık yardımcısı; `final_random_return` ile birlikte kullanılamaz.
- `predicate_inputs.random_inputs`: dakika yardımcısı; aynı predicate içindeki `random_return` ile birlikte kullanılamaz.

Çakışma kontrolü yalnız kaynak gerçekten ilgili helper'a ulaştığında yapılır. Önceki guard dönüşü, ulaşılmayan helper'ı çalıştırmaz. JSON şeması duplicate/bilinmeyen alanları ve sahte doğrulama iddialarını her düzeyde reddeder.

```json
{
  "initial_state": {"interval_dword": 1000, "last_attempt_qword": 0},
  "observation": {
    "tick": 3000,
    "session_stamp_qword": 0,
    "predicate_inputs": {"mode_byte": 0, "tick": 300000, "stamp_qword": 0},
    "flag_after_predicate": 1,
    "final_random_inputs": {"tick": 33, "srand_returned": true, "rand_eax": 7}
  }
}
```

Bu örnekte son aralık hesabı60007 olur. Bu yerel hesap, gerçek oyunda gözlenen random dönüşü değildir. İlk aralık helper'ından sonraki taze stamp/last-attempt gözlemleri, predicate sonrası taze bayrak ve callback sonrası kilit/mod kapıları ayrıca kalır. Eksik son helper gözlemi, bilinen caller timestamp yazımlarını yalnız prospective state'te bırakır; kabul edilmiş state değişmez.

## Bulunan disk CRT dosyasının isteğe bağlı replay modeli

[CRT_RUNTIME.md](CRT_RUNTIME.md) dosyasında warmup, 15 bit çıktı ve açık disk_crt_replay/same_thread_context seçimi açıklanır. Ham rand_eax gözlemiyle aynı ulaşılan çağrıda birlikte kullanılamaz. Bu seçim gerçek oyunda yüklü DLL kimliğini, thread pointer'larını veya helper normal dönüşünü doğrulamaz. Yerel plan rand_source=local_disk_crt_replay etiketi taşır; eski gözlem yolu ayrı kalır.
