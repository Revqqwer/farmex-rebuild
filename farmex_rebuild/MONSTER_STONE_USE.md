# Monster Stone taş kullanımı

`monster_stone_use.py`,4c567cnormal işleyicisini ve4ca900kayıt yardımcısını modeller. İşleyici önce üç farklı46209cEAXgözlemini sırasıyla51/52/53ile karşılaştırır; eşleşme erken döner. Tek bir sabit alan sonucu bütün okumaların yerine geçmez. Ardından GetTickCountve56fb40/44damgasıyla signedQWORDelapsed>=1000kapısı kullanılır. DWORDtickwrapnegatif fark üretirse unsigned-geçmiş süre gibi sayılmaz.

Envanter14..41tarama çerçevesi `genie_recovery.py`içindeki ortak tüketilmiş-input mekanizmasını kullanır; hedefliteral `Monster Stone`, payloadüretimiNone, inline frame setupgereksinimiFalseolarak açıkça seçilir. Worker'ın kendi setup'ı ayrıdır. Varsayılan GenieAPIliteral/template/setup davranışı değişmedi. Sourceeqwrapper varsayılan olarak opaque0/1gözlemidir; tam byteeşitliği yalnız açık own adapterseçimidir. İsim ve freshIDtyped okuyucuları da gerçek slotla bağlanabilir.

İlk isim eşleşmesi bulunduğunda taze4634a4kimliği0bile olsa tarama durur ve4ca900çağrısı hazırlanır. Yardımcı sıfırIDkoruması içermez:6baytlık `5f06`başlığının arkasına fullDWORDkimlik yerleştirilir, delay0enqueueplanlanır. Setup, memcpy, kuyruk gate/tick/normal ve returnspangözlemleri ayrıdır. Kapı0da kayıt kopyalanmadan yardımcı dönebilir. Önceki ownqueuekayıtları korunur; clock/returnbeklemesinde ikinci kayıt oluşmaz. Hiçbiri gerçek taş tüketimi veya dungeonbaşarısı değildir.

Eşleşme yokluğu için28slotun tamamı görülmelidir. Bu yolda sıra: completionmessage/ilk cleanup→MScheckboxsetterFalse→40ae0cstop(0,561f34)→taze context+4alarmBYTE→varsaDefaultalarmspan→outermessagecleanup. Stopisterse generated `BotSwitchFrame`ile bağlanır; eksik childolumlu parentnormal ile geçilemez. Checkboxsetter'ın iç callback'i opaqueolduğu için worker doğrudan561f5c0yazmış gibi bir sonuç uydurulmaz. UIprojeksiyonu kendi planıdır; kullanıcı ekranına uygulanmaz.

İki scan-sonrası yol da en sonda yeni GetTickCountile56fb40DWORDlowve56fb44DWORD0damgası üretir; alan/cooldownerken dönüşleri damga üretmez. Son epiloguenormal ayrıca gerekir. `MSUseFrame`yalnız bir invocation'ı ve onun ownqueue'sunu tutar; ana worker/session'a henüz bağlanmadı.

12yeni test;6bayt/fullID0, kapı ve tickdevamı, üç areaörneği,1000eşitliği ve signedwrap, ilk ID0eşleşmesi,28slotyokluk, exhaustionçağrı sırası, parentclockgapduplicateengeli, generatedstopgapi, hedefbytepolicy ve typedisim/kimlik bağını kapsar. Son tam koşu3051testtir; Genieortak scannerregresyonları da geçti. UIdeğişmedi/yeniden sınanmadı.

İki mevcut REAEvidence(4c567cve yeni4ca900)güncel PE/exportile eşleştirildi; eski/güncel150+28gövde toplam356mevcut talimat kaydı disk doğrulandı. Bu yeni ikili envanter kapsamı veya native/effectsertifikası değildir. Hareket/saldırı ve ana workerbağı açık; canlı oyun uyumluluğu doğrulanmadı.
