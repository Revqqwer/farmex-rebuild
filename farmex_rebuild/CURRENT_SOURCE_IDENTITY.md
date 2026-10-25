# Kurulu dosyalarla analiz kaynağının güncel eşleşmesi

21 Ekim2026 kontrolünde aşağıdaki beş kurulu dosya yalnız okunarak karşılaştırıldı. Dosyalar çalıştırılmadı, değiştirilmedi veya yeniden indirilmedi.

| Bileşen | Güncel SHA-256 | Sonuç |
|---|---|---|
| FarmexUS_ST_Loader.exe | 97d946ddec5df814e0042384b78b711c029f136aa6c43701910fd21cef5a0775 | Analiz piniyle aynı |
| Damon.slv | ffbe8ad8f8aa06728d6059443eb76b3bc88badbc1e29ffa201549ad50efd26ad | Korunmuş ham dosyayla byte eşitliği |
| Richard.slv | ffbe8ad8f8aa06728d6059443eb76b3bc88badbc1e29ffa201549ad50efd26ad | Korunmuş ham dosyayla byte eşitliği |
| Stephan.slv | f2864fc683a5517b6f1fee6a68138fdcb4337a3fa4780339039e577468161944 | Korunmuş ham dosyayla byte eşitliği |
| KnightOnLine.exe | ca69cecebdefd82b409ca8cf041655da53cb97113b068a086c5f7a6ef7e952a9 | Korunmuş oyun dosyasıyla byte eşitliği |

Her okumadan önce/sonra boyut ve değişiklik zamanı karşılaştırıldı. Damon/Richard için daha önce kaynakla eşleştirilen marker/sabit dönüşümü yeniden uygulandı; her ikisi de korunmuş febdac805f370fb3ecc1ba5bf76482eb1f3d9b52c080113eb1dc9f12d2e45759 görüntüsüyle byte byte aynı. Stephan'ın ayrı marker/sabit dönüşümü korunmuş c3610fbe55bdc69a9e146887487f9103a78ac71b219ceffd2a9cd0b35dbab012 görüntüsüyle aynı. Bu sonuçlar Stephan'ın bütün davranışlarının çözüldüğü anlamına gelmez.

21 Ekim16:36:07 UTC host sorgusunda yalnız süreç adı/PID kapsamında Knight, Farmex veya Loader ile eşleşen süreç bulunmadı. Bellek açılmadı/okunmadı. Bu, yalnız o anın gözlemidir; daha sonra oyun açılmadığı sonucu çıkarılamaz.

Bu kontrol, mevcut statik bulgular için yeni bir dosya sürümüne geçme gereği olmadığını gösterir. Disk eşleşmesi çalışan görüntü kimliğini, US/Steam profilini, oyun fonksiyonlarının ABI'sini veya HP/MP alanlarını doğrulamaz. Önceki yönetici erişim başarısızlığının nedeni de bu kontrolden çıkarılamaz. Yeni UAC başlatması, oyun belleğine erişim ve ağ isteği yapılmadı.

Üretim HP/MP okuyucularında eski ve güncel disk kimlikleri için ayrı aday tablolar zaten bulunuyor (`game_provider.py` ve `native/vitals_bridge.c`). Sırf dosya eşleştiği için aday alanlar canlı doğrulanmış sayılmadı ve kimlik/erişim kapıları gevşetilmedi.

Yeniden üretim: `work/verify_installed_analysis_sources.py`. Tam kayıt: `outputs/FarmexBot_guncel_analiz_kaynak_saglamasi.json`; host metadata kaydı: `outputs/FarmexBot_canli_surec_surumsaglama_20261021.json`. Bu aşamada uygulama davranışı değişmedi; son3315 test yeniden çalıştırılmadı ve yeni canlı test olarak sunulmadı.
