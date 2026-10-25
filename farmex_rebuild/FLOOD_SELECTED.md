# Flood — seçileni yaz: yerel GUI doğrulaması

`flood_selected.py`, seçili mesajı mevcut yerel kuyruğa ekleyen modeli sağlar. `panel_ui.py` içindeki gerçek `btnChatSelected` düğmesine bağlanmıştır. Güncel tam GUI kontrolü4159 testli çalışma ağacında geçti; önceki4081 testli dağıtım ayrıca saklandı.

Kaynak callback `004b1514` seçimi iki kez okur: ilk signed negatif sonuç çıkış yapar; ikinci indeks yeniden denetlenmeden `0045c9f0` yardımcısına geçer. Yardımcı 12 baytlık kayıtların mesaj ve kanal alanlarını ayrı vector-begin okumalarıyla alır. Otomatik döngünün enable, zaman, indeks veya bekleme alanını güncellemez. Kendi modelimiz değişmez satır görüntüsü kullanır; native eşzamanlı değişim eşliği iddia edilmez. İkinci indeks sınır dışındaysa Python negatif indeks davranışı kullanmak yerine çözülmemiş kapsam döndürülür.

Ortak paket hazırlığı kanal, CString ve mevcut boyut sınırlarını korur. Yerel admission kapısı sıfırken saat okunmaz; açıkken tek enqueue saati kullanılır. Eksik saat gözleminden sonra aynı frame tekrar devam ettirilebilir; tamamlanmış frame yeniden ekleme yapmaz. Arayüzün gate=1 tercihi yerel önizleme politikasıdır.

10 yeni test dahil toplam 4091 Python testi geçti (`work/flood_selected_full_tests.log`). Arayüz senaryosu `smoke_flood_selected.py`, kullanım limiti sıfırlandıktan sonra tam GUI testinde geçti (`work/merchant_metadata_full_ui.log`). İlk başarısız başlatma geçmiş kayıttır. İki yeni REA isteği de provider timeout ile sonuçlandı ve olumlu kanıt sayılmadı. Ayrı disk denetimi iki Richard sürümündeki 80 talimat kaydını doğrular; bunun kapsamı kaynak baytları ve açık çağrı operandlarıdır.

Native VCL çalışma davranışı, heap/alias/eşzamanlılık, özgün gönderici ve teslimat bu aday tarafından doğrulanmaz. Kuyrukta kayıt bulunması gönderim yapıldığı anlamına gelmez.
