# Callback ara bölüm API'si

`callback_interlude.py`, `0046f9b4..0046faa8` kaynak caller aralığını modeller. Gerçek callback, pointer değiştirme, random/clock/CRT veya oyun işlemi yürütmez. Maden sayfasındaki varsayılan-kapalı ara bölüm seçeneği bu modeli kullanır;normal-return gözlemi ayrı eski yoldur.

`CallbackInterludeState(interval_dword, last_attempt_qword)` kaynak `5620cc` DWORD ve `5620d4/5620d8` QWORD örneklerini tutar. Boş değer bilinmeyendir. `CallbackInterludeObservation` ayrı interlude `tick` ve `session_stamp_qword` ister. Tick callback unlock clock'undan kendiliğinden üretilmez.

Kaynak session farkı sıfırsa aralık bile okunmadan devam edilir. Aralık0 ise `00467cc4(60000,300000)` çağrısının açık `initial_random_return` sonucu saklanır; sonrasındaki kaynak okumaları için `session_stamp_after_random` ve ulaşıldığında `last_attempt_after_random` ayrı örneklerdir. Bilinmeyen taze last-attempt önceki snapshot'tan doldurulmaz.

Session farkı aralıktan **büyük** olmalıdır. Last-attempt farkı ise aralığa **eşit veya büyük** olduğunda geçer. Farklar zero-extended DWORD tick eksi QWORD stamp olarak signed64 değerlendirilir; aralık signed32 olarak genişletilir. DWORD wrap, QWORD farkına dönüştürülmez. Değerler sağlanan raw örneklerdir; yeni random değeri üretilmez.

Ulaşılan `0046ebd0` için ya ayrı `predicate_al` gözlemi ya da [koşul modeli](CALLBACK_PREDICATE.md) için tipli `predicate_inputs` gerekir;ikisi aynı ulaşılan çağrıda birlikte verilemez. AL nonzero ise ayrıca taze `flag_after_predicate` BYTE'ı gerekir; AL0 bunu okumaz. AL0 veya flag0 iken `target_554218` ve ayrı `replacement_returned=True` istenir. Üretilen helper planı `0046b8fc(0x554228,target,0x46eca8)` olur; herhangi bir belleğe uygulanmaz. Helper'ın iç davranışının veya kurulan callback'in çalıştığı kanıtlanmaz.

Ardından caller last-attempt low=tick/high=0 yazımlarını planlar ve ayrı `final_random_return` DWORD sonucunu aralığa saklar. Final sonuç eksikse bilinen stamp yazımları yalnız prospective state'tedir. `segment_fallthrough_planned` bu sınırlı aralığın kaynak devamına ulaşan yerel planını ifade eder; native yordam dönüşü veya canlı callback kanıtı değildir.

`MiningCallbackState.interlude` ve `MiningCallbackObservation.interlude` ile tipli bağ açılır. Bu yolda `post_timer_completed` hiçbir bool ile verilemez; varsayılan `None` kalmalıdır. Bütün ara bölüm yerine dış completion işareti kabul edilmez. Tam yerel plandan sonra taze `post_timer_lock` ve `mode_after_segment` hâlâ gerekir. Sonraki aşama eksikse accepted callback state değişmez. Aynı çağrıda tipli kontrol modeli de bağlanabilir.


## Arayüzde ara bölüm modeli

Motor denemeleri → Maden içinde **Ara bölümün kaynak modelini kullan** seçilir. Bu seçenek tipli kontrol modelini de açar; panel ayarlarının seçilmiş olması gerekir. Kontrol giriş/saat/party/yardım/alarm gözlemleri mevcut alanlardan alınır. Kontrol ve timer geçmeden ara bölüm JSON'u okunmaz. Model açıkken eski ara-bölüm normal-return kutusunun değeri kullanılmaz.

JSON yalnız `initial_state` ve `observation` nesnelerini kabul eder. Örneğin aşağıdaki kendi örneği sadece kaynak akışını planlar:

```json
{
  "initial_state": {"interval_dword": 1000, "last_attempt_qword": 0},
  "observation": {
    "tick": 3000,
    "session_stamp_qword": 0,
    "predicate_al": 1,
    "flag_after_predicate": 1,
    "final_random_return": 70000
  }
}
```

Bu örnek ara bölüm çağrı planını tamamlar;sonraki taze kilit ve mode alanları ayrıca gerekir. `tick` callback unlock saatinden veya deneme saatinden üretilmez. Boş `{}` kaynak clock'u bilinmeyen bırakır. Interval0 yolunda `initial_random_return`, `session_stamp_after_random` ve ulaşılan noktada `last_attempt_after_random` ayrıca gerekir. Predicate/helper/pointer-plan girdileri önceki API bölümündeki alanlarla aynıdır. Random üretilmez ve helper çağrılmaz.

`initial_state` sıfırlamadan sonraki ilk ulaşılan ara bölüm JSON'unda alınır. İlk seed'den sonraki initial_state düzenlemesi mevcut kabul edilmiş state'i değiştirmez;yeniden başlangıç için sıfırlama gerekir. Eksik helper veya sonraki kilit/mod/maden aşaması tam zinciri bekletir;bilinen store'lar yalnız prospective state'te görünür. Tam yerel callback planı tamamlanınca own state kabul edilir. Bu gerçek oyun belleğinin transaction/rollback davranışı değildir;araç bellek etkisi yürütmez.

Duplicate alanlar,doğrulama iddiaları,bilinmeyen alanlar,yanlış raw genişlikleri ve bool yerine sayı kullanımı reddedilir. Model adres etiketleri eski kaynak tanımlayıcılarıdır. Dar kaynak kapsamının yeni modülde korunması,opaque predicate veya yüklenmiş runtime DLL davranışının canlıda doğrulandığı anlamına gelmez.

## Kaynak koşul modeline bağ

16 Ekim callback koşul modeli: 0046ebd0 yordamının74talimatı eski/güncel dosya baytlarıyla doğrulandı;farklı2CALL aynı GetTickCount importuna gider. Önceden opaque olan AL sonucu artık isteğe bağlı predicate_inputs snapshot'ından hesaplanıyor. Sabit300000 eşik,işaretli dört DWORD önkoşulu,düşük32bit dakika çarpımı,ayrı clock ve kaynak BYTE1 yazım planı uygulandı.9yeni test dahil1554birim testi ve genişletilmiş gizli UI testi geçti. Kaynak saat/random/stamp gözlemleri ayrı kalır;sonraki taze flag ve callback kilit/mod kapıları atlanmaz. Gerçek oyun okuma/yazma/yükleme veya eylem yapılmadı;canlı uyumluluk açık.

JSON şeması ve kullanım: [CALLBACK_PREDICATE.md](CALLBACK_PREDICATE.md). Predicate snapshot her çağrıda taze sağlanır;random minutes yazım planı gerçek belleğe veya sonraki snapshot'a otomatik taşınmaz.

## Kurulan callback için kaynak kapsamı

[CALLBACK_CONTEXT.md](CALLBACK_CONTEXT.md) içindeki 12 talimatlık 0046eca8 gövdesi ayrıca çözüldü. Kurulum helper'ının normal döndüğü gözlemi, bu callback'in çağrıldığı veya oyun alıcısının çalıştığı anlamına gelmez. Beş yeni native vaka yalnız kendi host/alıcı sözleşmesini sınar.

## Kaynak random hesabı bağı

Hazır helper dönüşü yerine ayrı gözlenen clock/srand dönüşü/rand EAX değerleriyle hesap seçilebilir. Şema, üç çağrı noktasındaki alan adları ve sınırlar [SOURCE_RANDOM.md](SOURCE_RANDOM.md) içindedir. Bu bağlantı gerçek RNG çalıştırmaz veya canlı doğrulama üretmez.
