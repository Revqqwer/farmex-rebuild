# Ana callback ile DC yordamının bağı

`CallbackPreQueueObservation.disconnected`, isteğe bağlı ve tipli bir
`DisconnectRoutineObservation` alır. Kaynak callback'in `00459970` çağrısına
ulaşılırsa `DisconnectRoutineFrame(context=0x562194)` oluşturulur. Alt yordamın
girişi ulaşılan CALL'dan türetilir; prologue ve diğer normal dönüşler türetilmez.

`0046f594` bağlantı yardımcısını çağırır; `DEC EAX / JZ46f5b1`, yalnız tamDWORD
`1` için bu çağrıyı atlar. Diğer değerlerde `PUSH562194 / CALL459970 / POPECX`
gelir ve ardından callback temizleme adresi46fb09'a gidilir. AL1 tek başına
bağlılık sayılmaz; örneğin101hex, DC yoluna girer.

| Sınır | Davranış |
|---|---|
| Bağlantı/ready kapısı | Ulaşılmayan alt yordam oluşturulmaz; erken verilen alt gözlemler tüketilmez. |
| Alt yordam | Bir kez bağlandıktan sonra gözlemi sonraki çağrılarda boş bırakmak opak dönüşle atlamayı sağlamaz. Eksik helper, sender veya return sınırı callback'i durdurur. |
| Dış CALL dönüşü | Alt yordam tamamlandıktan sonra da ayrı `disconnected_worker` normal dönüşü gerekir. |
| Sonradan bağlama | Opak dönüş daha önce tüketilmişse geriye dönük ayrıntılı alt model bağlanması reddedilir. Dönüş henüz eksikken bağlanabilir. |
| İz | Tamamlanmış child, byte/write intent ve timestamp önekleri dış callback beklerken korunur. |
| Sonraki callback | Önceki child'ın yazım niyetleri yeni callback gözlemi olarak kullanılmaz. Yeni pending/connection/guard okumaları gerekir. |
| Üst bileşim | `SourceCallbackFrame` bu bağı mevcut entry/event segmentinden taşır. Erken çıkış kuyruğu ve cleanup/epilogue dönüşleri hâlâ ayrı gerekir. |

Bağ opsiyoneldir: eski opak kaynak çağrısı API'si korunur; bağ verilmemesi ayrıntılı
alt yordamın doğrulandığı anlamına gelmez. Yeni alan dataclass'ın sonundadır,
önceki positional kullanımın anlamı değişmez. Lifecycle child'ları ayrı tip ve
etiketlerle kalır.

Ek statik eşleme: DFM'de `frmMain/Panel5/btnRelogGame` düğmesinin OnClick'i
`btnRelogGameClick`tir. Sabitlenmiş eski Ghidra seed kaydı bunu004ae848 ile
eşler. Her iki sürümde004ae848->00412efc çağrısı ve00412eff'deki
`[562202]=1` byte yazımı doğrulanır.562194+6e=562202 olduğundan önceki özel
yeniden bağlanma dalı manuel relog bayrağıyla aynı alandır. Bu statik veri/çağrı
eşlemesidir; düğmenin güncel oyunda çalıştığına veya başarılı yeniden girişe
kanıt değildir. Manuel producer'ın19talimatı bu aşamada ayrı davranış modeli
olarak tamamlanmış sayılmaz.

Mevcut REA kanıtları yeniden kullanılır. Eski ve yenilenmiş modülde kaynak
yordamlar ve tam389talimatlık callback, iki manuel producer/callback gövdesi ve
tick import thunk'ı toplam2892ayrık byte kaydıyla doğrulanır. Önceki üç callback
site kaydı bu kez tam callback gövdesine dahildir, tekrar toplanmaz.

Gerçek native callback/hook, exception/SEH, ABI, RTL, bellek, süreç, ağ veya oyun
çağrısı yapılmaz. `complete` normal kontrol planının tamamlanmasıdır; tam callback
veya tam fonksiyon semantiği/native/canlı uyumluluk sertifikası değildir.
