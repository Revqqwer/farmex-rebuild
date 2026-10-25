# Achieve MS istek dizisi

Kaynak panelindeki `btnAchieveGetMS` düğmesi `btnAchieveGetMSClick` olayına bağlıdır.004b0380 gövdesi53 talimattır; başında uygunluk, MS modu veya profil-yükleme kapısı görünmez.004ca958 yardımcısına sırayla şu11 DWORD kimlik gönderilir:

`182,183,184,185,186,187,56,58,65,74,5f` (hex).

Her fiziksel push sırası `(kimlik,561ef8)` şeklindedir. Bunlar kaynakta ödül/başarı tanımlayıcı adayıdır; anlamları, hak sayısı veya11 taş kazanımı doğrulanmış değildir.

004ca958 gövdesi28 talimattır.5477cf adresindeki6 baytlık `990200000000` şablonunu alır, DWORD kimliği offset2'ye kopyalar ve004c7710'ya6 bayt/0 gecikme ile context'i aktarır. Yardımcı sıfır kimliği veya fullDWORD'un üst bitlerini elemez. `AchievementRequestFrame` bu serializer'ı ve kendi kuyruğuna koşullu enqueue davranışını uygular; oyun adresleri çağırmaz.

`MSAchievementFrame`,11 ayrı generated request child oluşturur. Her birinin kurulum, kopya, kuyruk kapısı, zamanı, enqueue normal dönüşü ve helper epiloğu ayrıdır. Kuyruk kapısı0 ise o deneme kayıt üretmeyebilir; bu, sonraki kaynak çağrıları atlamak için kullanılmaz. Child tamamlandıktan sonra olay gövdesindeki dış helper normal dönüşü de gerekir. Bir çağrı eksikse sonraki kimliğe geçilmez.

Kuyruk kaydı oluşturulup enqueue normal dönüşü veya parent dönüşü beklenirken advance yeniden çağrılırsa aynı kayıt çoğaltılmaz. Son11 çağrıdan sonra olayın kendi epilog dönüşü ayrıca gerekir. Tamamlanan frame yeniden advance edilince eski sonuç döner; yeni kullanıcı olayı için yeni frame gerekir. Önceki kendi kuyruğu constructor üzerinden korunabilir.

Sekiz yeni test; kimlik/sıra/context/6 bayt/offset2/0 gecikme,11 ayrı timestamp, sıfır ve fullDWORD, gate0 ile tüm çağrılar, ilk eksikte durma, tüketilmiş gate, enqueue/outer/event dönüş boşlukları ve tek kayıt davranışını sınar. Eski ve güncel ikililerin toplam162 mevcut talimat kaydı, template ve iki gerçek REA raporu eşleşti.

Bu aşamada paneldeki asıl düğmenin bağımsız event modeline bağlantısı henüz eklenmedi. UI/compiler kontrol sayısı293 olarak kalır. Ağ gönderimi, sunucu yanıtı/ACK ve ödül kazanımı doğrulanmamıştır; yerel11 girişimin tamamlanması bunları kanıtlamaz.
