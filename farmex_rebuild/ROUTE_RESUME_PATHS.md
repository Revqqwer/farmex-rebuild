# Rota çıkışına ulaşan iki ek dal

18 Ekim 2026. `route_resume_paths.py`, güncel `004eb2c4` yordamında
`004eb7f4` ve `004eb987` adreslerine **ulaşılmış olması koşuluyla** aşağıdaki
davranışı modeller. Bu adreslere hangi rota türünün geldiği, önceki hareket ve
mesafe kontrolleri henüz bu modele dahil değildir. Bu iki dalın eklenmesi tüm
rota motorunun tamamlandığı anlamına gelmez.

İlk root/offset/guarded BYTE okumasının AL değeri nonzero ise doğrudan ortak
çıkışa gidilir. Ortak çıkış aynı alanı yeniden okur; ilk gözlem ikinci gözlem
yerine kullanılamaz. İlk okuma için `plan_route_condition`, durum yazmadan
aynı guarded okuyucu semantiğini paylaşır.

## Süre dalı: 004eb7f4

İlk AL sıfır olduğunda GetTickCount DWORD sıfırla genişletilir; global
`0056ff9c/0056ffa0` QWORD damga çıkarılır. Sonuç 64 bitte sarılıp signed64
olarak karşılaştırılır. `0056ffa4` DWORD sınır signed32'den genişletilir.
Sınır geçen süreden büyükse yordam ortak çıkışa uğramadan döner; yeni izin
yazısı yoktur. Eşitlikte aşağıdaki yol çalışır.

`004eb843..004eb885` metin oluşturma/karşılaştırma/temizleme aralığı bağımsız
normal dönüş gözlemidir. Saklanan karşılaştırma AL değeri de ayrı girdidir;
AL nonzero ise `00459fb0(00562194)` çağrısının normal dönüşü gerekir.
Karşılaştırılan metnin anlamı veya yardımcıların tüm yan etkileri bu modelde
çözülmüş sayılmaz. Gerekli dönüşlerden sonra object BYTE+5d9=0, global
BYTE561f6c=1 yazıları, ardından ortak çıkışın taze okuması planlanır.

## İsteğe bağlı yardımcı dalı: 004eb987

İlk AL sıfır olduğunda global BYTE56fade okunur. Nonzero ise
`0047789c(00569a98)` normal dönüşü ayrıca gerekir. Sonra aynı iki durum
yazısı ve ortak çıkışın taze okuması gelir. Bu çağrının işlevine kanıtsız bir
oyun eylemi adı verilmedi.

Ön dal izin yazmışsa, ortak çıkışta AL nonzero bulunması önceki izin yazısını
geri almaz. İkinci AL sıfırsa kaynakta iki yazı yeniden yapılır; kayıt sırası
korunur. İkinci gözlem eksikse bütün yerel deneme tamamlanmaz: kabul edilen
state girişte kalır, bilinen ön yazılar `prospective_state/writes` alanında
ayrı tutulur. Bu saf deneme API'si native yürütme veya resumable native frame
değildir; hiçbir oyuna/belleğe yazmaz.

## Doğrulama

`work/audit_route_resume_paths.py`, eski ve güncel hash'li dosyalarda
**180 talimat kaydının** baytlarını, dalları, iki erken izin yazısını ve
GetTickCount import kimliğini doğrular. Eski sürümde saat import stub'ı
005074da, güncel sürümde 005074f6'dır. Bu kayıtlar diğer auditlerle örtüşür;
benzersiz talimat veya tamamlanan fonksiyon sayısı değildir. Ghidra/disk
kanıtıdır; REA Evidence olarak sunulmaz.

`work/audit_route_active_alias.py` ayrıca iki sürümde 10 kaydı doğrulayarak
bu callback'in geçirdiği 005687a8 object adresi için
`005687a8 + 5d9 = 00568d81` eşliğini kanıtlar. Böylece callback'in okuduğu
route-pending BYTE ile bu object'in active BYTE alanı aynı konumdur.
Başka object örneklerine veya callback sonrası taze global değerlerine
otomatik genelleme yapılmaz.

12 yeni test; önceki ortak çıkış testleriyle 22 ilgili test geçti. Süre
eşitliği, negatif sınır, tam QWORD damga, signed64 sarılma, taze ikinci
okuma, eksik yardımcı dönüşleri ve ön yazının korunması sınandı.
Tam Python kontrolü: **2046 test geçti, 7.300 saniye**. UI ve native kod
değişmedi; bu aşamada UI smoke veya native fixture tekrarlanmadı.
Gerçek rota hareketi, native yardımcı etkileri, callback erişimi ve canlı
oyun uyumluluğu açık kalır. Workbench bu API'yi henüz sunmaz.
