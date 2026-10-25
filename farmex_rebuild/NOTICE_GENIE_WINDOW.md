# Ban Notice mod3 Genie zaman penceresi

Sonraki aşama: genel/Notice worker’ındaki7getter çağrısı optional typed child ile bağlandı. Güncel kapsam [GENIE_GETTER_BINDING.md](GENIE_GETTER_BINDING.md); aşağıdaki metin önceki aşamanın sınırlarını korur.

21 Ekim 2026. `notice_genie_window.py`, `0045a05c` işleyicisinin yalnız `0045a38c` noktasına ulaşıldığı verilmiş normal tail'ini modeller. Chat bildirim handler'ında mod3çağrısının bulunmaması bu işleyiciyi dışlamaz. Bu model gerçek bildirim dinlemez; açık kaynak gözlemleriyle inert çağrı/store planı üretir.

Kaynakta önce569139enable ve taze56913cmode kontrol edilir. Enable kapalı veya mode3değilse yerel2ebayrağı1olur. Mode3te569558/56955czaman damgasının signedQWORD değeri pozitif olmalıdır; highDWORD sıfırsa lowDWORD ayrıca pozitif kontrol edilir. Damga geçersiz/sıfırsa yerel bayrak yine1olur.

Aktif damgada yeni GetTickCount ve taze damga low/high okumaları kullanılır. `(zero_extended_tick-stamp)&FFFFFFFFFFFFFFFF` sonucu signed64yorumlanır. Eşik, `minutes*60000` işleminin low32sonucunun signed32değeri ve bunun sign extension'ıdır. Elapsed eşikten küçükse pencere aktiftir; eşitlikte kapanır. Bu hesap DWORD saat sarma farkı değildir. Dakika çarpımı taşınca negatif eşik oluşabilir; model clamp yapmaz.

Pencere içindeyken569148açıksa561fa8=1store planı, Genie state kontrolünden **önce** oluşur.4631c8sonucunun düşük AL'si nonzero ise start atlanır. Sıfırsa ortak553cfc/553d00damgasına karşı ayrı tick ile signedQWORD elapsed>=1000beklemesi kontrol edilir.4631e8düşük AL'si pozitifse466cc4fiziksel `(1,)` çağrı planı, ardından yeni tick ile cooldown lowDWORD'u ve highDWORD0store'ları gelir.

Yerel2e0iken final stop kontrolü atlanır.2e1ise önceki genel mantığın yerel2dbayrağı ayrıca gözlenmelidir; bu model onu varsayılan1yapmaz. İki bayrak nonzero ise fresh4631c8AL'si **tam1** olduğunda cooldown>=1000koşuluyla466cc4`(0,)` planlanır. Bu son gate yolu normal tamamlandıktan sonra, state/cooldown nedeniyle stop çağrısı yapılmamış olsa da561fa8=0planı oluşur. Eksik gözlem bu store'u erkenden üretmez.

İki yerel bayrağın45a200/45a204adreslerindeki sıfır başlangıçlarının notice girişini normal CFG üzerinde domine ettiği doğrulandı. Genel2dbayrağı bu girişten önce değişebildiğinden güncel değeri ayrıca gerekir. Önceki worker'ın erken dönüşleri, mode seçimleri veya runtime çağrı etkileri notice modelinden çıkarılmaz.

`work/audit_notice_genie_window.py` eski/güncel297'şer gövde talimatını baytlarla doğruladı:594kayıt. Bütün gövdenin byte doğrulaması bütün davranışın modellendiği anlamına gelmez. Model kapsamı reached notice tail'idir. Kaynak `outputs/FarmexBot_notice_genie_pencere_kaniti.json`; korunmuş Ghidra/PE kanıtıdır, yeni REA Evidence değildir.

Sekiz yeni test pencere eşitliğini, signed dakika taşmasını, taze presence/window damgalarını, DWORD saat sarma farkını, düşük AL start/stop ayrımını, no-attack store sırasını ve eksik genel bayrak/normal dönüşü kapsar. Sonuçlar `NOTICE_GENIE_WINDOW_VALIDATION.json` dosyasındadır. Gerçek Genie/atak etkisi, tam worker, otomatik notice entegrasyonu ve canlı uyumluluk doğrulanmadı. UI/native C değiştirilmedi; UI yeniden test edilmedi.
