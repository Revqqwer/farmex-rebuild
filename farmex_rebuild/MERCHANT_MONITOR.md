# BUY aşama 5 izleme planı

18 Ekim 2026: `merchant_monitor.py`, `004220c8` fonksiyonunun
`00422e9f..004230ac` normal akışını verilen gözlemler üzerinde planlar. İki
ikili sürümde 264 caller talimat kaydı dosya baytlarıyla doğrulandı. Ayrıca
yer değiştirmiş dört dahili string wrapper'ının toplam 184 talimat kaydı
diskten doğrulandı; bunlar FF25 import thunk'ları değildir. Wrapper çiftlerinin
iç davranış eşdeğerliği kanıtlanmadı ve modelde uygulanmadı. Audit:
`work/audit_merchant_monitor.py`; rapor:
`outputs/FarmexBot_pazar_izleme_kod_kaniti.json`. Bunlar Ghidra kaynaklı statik
kanıttır, REA Evidence veya orijinal kodun çalıştırılması değildir. Önceki geniş
auditlerle örtüşebilen kayıtlar benzersiz talimat toplamına eklenmemelidir.

Reopen BYTE `+110=0` iken saat/damga/dakika veya geri sayım görüntüleme gözlemi
aranmaz. Doğrudan taze `0042070c` çanta yardımcısına geçilir. Diğer değerlerde:

1. `interval=signed32(lowDWORD(minutes_DWORD*60000))` hesaplanır.
2. Taze DWORD tick'ten `+10` QWORD damganın yalnız düşük DWORD'u çıkarılır;
   `elapsed=signed32(lowDWORD(tick-stamp.low))` olur. Üst damga kullanılmaz.
3. `elapsed>=interval` ise phase DWORD `+4=0` yazması planlanır. Akış burada
   bitmez; aynı çağrıda çanta yardımcısına devam eder.
4. Henüz dolmadıysa geri sayım iki ayrı signed IDIV sonucunun farkıdır:
   `signed32(trunc(interval/1000)-trunc(elapsed/1000))`. Bölme sıfıra doğrudur.
   Örneğin interval60000/elapsed999 için 60 gösterge değeri elde edilir;
   farkın önce alınması aynı sonuç değildir.
5. Bu yoldaki string/VCL bloğunun normal dönüşü ayrı
   `display_span_returned=True` gözlemidir. Bu bir batch gözlem sınırıdır,
   kaynakta tek bir helper çağrısı bulunduğu iddiası değildir.
6. Her iki timer yolunun ardından taze çanta helper EAX sonucu signed32
   olarak `+120` signed32 eşiğiyle karşılaştırılır. Count<=threshold ise
   tekrar `+4=0` yazması planlanır. Aynı planda iki sıfırlama yazması olabilir.

Çanta sonucu açık ham DWORD veya mevcut 28 yuvalık
`MerchantInventoryObservation` modelinden alınır. İkisi birlikte verilmez.
Timer dolmuşken çanta gözlemi eksikse `prospective_phase_dword=0` ve eksiklik
birlikte gösterilir; tamamlanmış sonuç üretilmez. Plan gerçek belleği değiştirmez.
Eksik plandaki prefix kabul edilen runner durumuna uygulanmaz. Yeniden planlama
yeni bir gözlem örneğidir; native callback ortasında duraklatma/devam etme veya
istisna/reentrancy davranışı emüle edilmez.

`MerchantSnapshot.buy_monitor_inputs` ile açık bağlanan BUY aşama 5 yolu,
tam plan olmadan runner'ı ilerletmez. Tam plan phase0 verirse yeniden kurma
işaretlenir; phase5 verirse izleme sürer. Eski çanta girişleriyle birlikte
vermek çakışma hatasıdır. Bu bound yolun gözlemleri yetkilidir; ayarlardan ikinci
bir timer/threshold hesabı yapılmaz. Diğer aşamalar ve legacy giriş yolu bu
yeni planın kapsamı dışındadır.

Arayüzün yanıt örneği modunda ayar, own yanıt damgası ve sentetik DWORD tick
bu modele bağlanır. “Hazır” kutusu yalnız geri sayım gösterge bloğunun sentetik
normal dönüş gözlemidir; due dalında gerekmez. Timer dolsa da hazırlık/çanta
örneği kapalıysa taze çanta sonucu beklenir. Yerel kuyruk boşaltılmaz, oyun
paketi gönderilmez ve işlem onayı üretilmez.

14 yeni birim testi; timer sınırı, signed çarpım/çıkarma, damganın yüksek
kısmının dışlanması, bölme sırası, iki yazma sırası, eksik görüntü/çanta,
28 yuva ve runner bağını kapsar. Tam çalıştırmada 1757 test geçti (7.022 s).
Gizli yanıt/monitor arayüz testi ve önceki caller/kuyruk testi geçti. Genel
UI smoke önceki yanıt bağlantısı aşamasındaki kayıttır, bu değişiklik için
tekrar çalıştırılmadı. Native string/VCL/heap etkileri ve canlı uyumluluk açık.
