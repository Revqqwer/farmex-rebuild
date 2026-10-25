# Genie yenileme yardımcısının genel işleyiciye bağı

`GenieWorkerObservation.recovery_observation` isteğe bağlı typed alt gözlemdir. `plan_genie_prefix` kaynakta recovery dalına ve en az 5000 ms koşuluna ulaştığında `GenieRecoveryFrame(0x561ef8)` üretir. Çağıran hazır bir child planı veya başarı iddiası veremez. Alt gözlem verilmezse önceki opaque normal/EAX sınırı korunur; bu kullanım yardımcının davranışını doğrulamaz.

Alt tarama, kuyruk kapısı, tick, enqueue dönüşü veya return span eksikse üst normal/EAX olumlu olsa bile işleyici bu noktada bekler. Alt model tamamlandıktan sonra ayrıca üst `recovery_probe` normal dönüşü, raw EAX ve ayrı `recovery_probe_post_tick` gerekir. Pozitif yolda yalnız AL=1 kaynakta bilinir; EAX üst bitleri kısıtlanmaz. False yolda full EAX=0 bilinir. Ancak bundan sonra 553cf0 BYTE ve 553cf4/553cf8 DWORD zaman damgaları projekte edilir.

`GeniePrefixFrame` aynı invocation için kalıcı child frame tutar. Tüketilen slot bilgileri ve tek yerel kuyruk kaydı üst dönüş veya saat beklemesinde korunur. Sonraki gözlem eski slotu değiştirerek veya başka kapı/tick vererek ikinci kayıt oluşturamaz. Ulaşılmayan child örnekleri değerlendirilmez.

Yedi yeni test, kapı sıfırken AL1/kayıtsız sonuç, bilinen full false dönüş, parent/child ayrı beklemeler ve tüketilmiş tarama devamını kapsar. Son tam koşu 3004 testtir. Mevcut helper402 ve worker594 talimat kayıtları eski/güncel snapshot'lara karşı yeniden doğrulandı; yeni fonksiyon veya talimat kapsamı iddia edilmez. Bunlar korunmuş Ghidra/PE kanıtlarıdır; yeni REA Evidence değildir.

Kuyruk yalnız bu invocation'ın bağımsız yerel modelidir; ortak worker session kuyruğuna bağ henüz yoktur. İsim/ID okuyucularının gerçek oyun sonuçları, RTL karşılaştırma eşdeğerliği, bellek/koruma işlemleri, gerçek gönderim ve Genie yenileme etkisi doğrulanmadı. UI değiştirilmedi, bu aşamada yeniden sınanmadı. Bu bağ tam fonksiyon veya canlı eşdeğerlik sertifikası değildir.
