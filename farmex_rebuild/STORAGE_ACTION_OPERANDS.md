# Depo aktarımının sıralı operandları — 19 Ekim 2026

`storage_action_operands.py`, altı aktarım/düğme yardımcısında global, korumalı ve doğrudan okumaları sıralı örneklerle yeniden üretir. Önceki `storage_native_plans.py` sözlük modeli aynı adres için tek değer tutuyordu. Yeni yol ikinci kökün/ofsetin veya aynı doğrudan adresin sonraki okumada değişmesini korur; önceki değerle eksik okumayı doldurmaz.

| API'deki tarihsel rol | Güncel ikilide adres | İşlev |
|---|---|---|
| 004fe274 | 004fe290 | VIP depodan eşya seçimi |
| 004fe2fc | 004fe318 | VIP çantadan eşya seçimi |
| 0046fc78 | 0046fc78 | Inn çantadan eşya seçimi |
| 0046fd04 | 0046fd04 | Inn depodan eşya seçimi |
| 00465334 | 00465334 | Miktar penceresinde onay/iptal düğmesi |
| 0046fdf8 | 0046fdf8 | Inn sayfa düğmesi |

Adresler kaynak rollerini tanımlar; çağrılabilir canlı ABI kaydı değildir.

`NativeHelperObservation.operand_samples` yeni `StorageActionSamples` girdisini kabul eder. `global_samples` ve `direct_samples` sıralı adres/değer çiftleridir; `guarded_samples` ayrıca koruma çağrısının ham sonucu ve DWORD değeri ayrımını taşır. Aynı adrese birden çok, farklı örnek verilebilir. Yeni yol ile eski sözlük girdileri karıştırılamaz. Profil etiketi tek başına canlı profil seçimi kanıtı değildir.

Eşya yardımcısı önce korumalı root/context/slot/pointer okumalarını yapar. Kayıt pointer'ı veya ilk DWORD sıfırsa dispatch yapılmaz. Diğer kök/context değerlerinin sıfır olması için fazladan erken çıkış eklenmedi. İkinci root ve context ofseti taze global okumalarıdır; sonraki context/vtable/target okumaları doğrudandır. Doğrudan null adres bile açık gözlem ister; korumalı wrapper'ın null→0 davranışı buna taşınmaz. Adresler ve slot kaydırması DWORD'a sarılır.

Inn eşya yardımcılarının PUSHAD/PUSHFD ve ters geri alma sırası, iki literal push ve dolaylı çağrı hedefi planlanır. Bu, yerel Python sürecinde veya oyunda assembly çalıştırıldığı anlamına gelmez.

Onay ve sayfa yardımcıları iki düğmeyi de seçimden önce okur. Onayda argümanın düşük baytı sıfır değilse ilk düğme, sayfada yalnız tam 1 ise ilk düğme seçilir. Bu yardımcılarda push işlemleri dispatch ofseti/vtable okunmasından öncedir; eşya yardımcılarında sonraya denk gelir. Sıralı iz bu farkı korur.

Mevcut item/page bağları yeni operand planını tanı olarak taşır. Tam operandlar verilse bile ayrı `normal_returned=True` olmadan caller devam etmez. Sayfa helper'ına gelmeden artırılan own slot sayacı, sonraki dönüş boşluğunda korunur. `no_call` operand sonucu da caller normal dönüşünün yerine geçmez. Miktar metni/yazım yardımcısı 004653a8 eski ayrı modelde kalır; yazım veya dönüşü yeni modelle doğrulanmış sayılmaz.

17 yeni test; dört slot helper'ı, değişen ikinci global ve aynı adreste değişen doğrudan değerler, sıfır dalları, koruma başarısızlığı/bilinmeyen ayrımı, bütün eksik örnek önekleri, düğme seçimi/okuma sırası, caller dönüş kapıları ve sayfa sayacının korunmasını kapsar. Son tam sonuç **2526 test, 7.348 saniye**. Arayüz kontrolünün sonucu STORAGE_ACTION_OPERANDS_VALIDATION.json dosyasındadır; yeni sıralı gözlemler API üzerinden verilir.

İki korunmuş ikilide altı yardımcının ve ortak korumalı okuyucunun 598 talimat kaydı dosya baytlarıyla doğrulandı. Yer değiştiren method adresleri ve VirtualProtect import kimliği ayrı eşleştirildi. Bu kapsam önceki denetimlerle örtüşür; 598 yeni benzersiz talimat veya altı tamamen bitmiş fonksiyon olarak sayılmaz. Kanıt Ghidra/disk denetimidir, REA Evidence değildir.

Gerçek bellek okuma/koruma değişimi, dolaylı çağrı, helper dönüşü, native ABI, dialog/aktarım etkileri, eşzamanlılık ve canlı oyun uyumluluğu doğrulanmadı. Çağrı hedefinin sıfır veya bilinen olması da yürütme güvenliği/uyumluluk kanıtı değildir.
