# NPC actor lookup çağrı bağlamı

4609 Python testi ve yeni tam yerel GUI1037 kontrol/11 form/18 sekme geçti. Kayıt NPC_ACTOR_LOOKUP_VALIDATION.json.

00464a10 hedef kimliğini004649e4'e iletir. İç yardımcı553e8c globalinden adresi, sonra bu adresteki DWORD'u ECX'e alır;553e9c çağrı hedefini sağlar. Dolaylı çağrı öncesi EAX0'dır, EDX yazılmaz ve ayrı gözlem gerekir. Stack'e önce1, sonra full hedef ID push edilir. Model entry_stack_dwords alanında yalnız dönüş adresinden sonraki iki argüman DWORD'unu, ESP+4/+8 sırasıyla(ID,1) tutar. Bu, tahmini C fonksiyon imzası veya çalıştırılabilir native çağrı değildir.

Dolaylı hedef dönüşü, EAX sonucu, iç yardımcı dönüşü ve dış yardımcı dönüşü ayrı tutulur. Null context/target için kaynakta guard yoktur; boş actor sonucu veya normal dönüş uydurulmaz. Tamamlanan context/result daha sonraki gözlemlerle değişmez. Yanlış context örnek adresi cache'i bozmaz.

Gerçek NPC düğmesinin lower sağlayıcısı typed lookup gözlemi kabul eder. İkinci hedef okuması88 çağrıya bağlandı; GUI testi EAX0, ECX9000, EDXfeed ve push(1,88) değerlerini doğrulayıp isim/diyalog akışını tamamladı. Lookup beklerken hazır actor değeriyle geçilemez. Dönüş0 ise isim/üçüncü hedef okunmaz.

| Kaynak profil | Context slot literal | Lookup target literal |
|---|---|---|
|Eski US|01115580|0050df80|
|Yeni US|011289cc|00510a50|
|Eski Steam|011ea634|006e4f40|
|Yeni Steam|011e9634|006e4f40|

Bu sabitler iki decoded bot sürümünün initializer MOV'ları ve553e3c caller argümanıyla doğrulandı. Runtime global değeri veya kurulu güncel oyunun fonksiyon gövdesi/ABI kanıtı değildir. Doğrulanan2495 instruction kaydı bu ayrımı korur. Test verileri sentetiktir; gerçek hedef çağrısı, native callee/stack cleanup/SEH ve otomatik oyun veri toplama yürütülmedi. Geç User Trade Unicode üreticisi ve canlı uyumluluk açık kalır.
