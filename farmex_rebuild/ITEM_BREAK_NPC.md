# Item kırma NPC seçimi

23 Ekim 2026. `item_break_npc.py`, Richard00470d98'in SEH prologundan
sonraki normal akışını, opak helper/girdi gözlemleriyle yerel plana taşır.
Eski/güncel iki ikilide149 NPC ve64 caller kaydı, toplam426 disk kaydı
doğrulanır. Yeni REA analizi149-talimat gövdesiyle eşleşir. Bu sayılar native
helper etkilerinin veya tam fonksiyonun tamamlanması anlamına gelmez.

İlk managed kurulum bölümü boş ad literalini hazırlar; taze yapılandırma+c
DWORD'u0 ise Moira literal ataması gerekir. Sıfır olmayan modda bu atama
atlanır. `lookup_name` alanı bu kaynak literal dalını gösterir. Sonraki
managed argüman kopyalama bölümü ve00465960 gerçek lookup girdisi/etkisi
opak kalır; normal dönüş tek başına oluşturulan native string'i kanıtlamaz.

Lookup EAX0 ise obje/koordinat yardımcıları atlanır ve ayrı failure cleanup
normal dönüşüyle sonuçEAX0 olur. Kimlik sıfır değilse00464a10 kimliği alır.
Obje EAX0 da aynı başarısızlık temizliğine gider. Sıfır olmayan bütün ham
DWORD obje değerleri kaynak unsigned karşılaştırmasına göre devam edebilir.

Koordinatlar sırayla okunur: taze554008 offseti + obje, sonra taze554010
offseti + obje. Adres toplaması32 bitte taşar. Her0045ddb8 normal dönüşünden
sonra ayrı FSTP float32 bit gözlemi gerekir.00460548 fiziksel argüman
sırası ikinci_koordinat, birinci_koordinattır. Uzaklık helper sonucu FSTP32
ve iki FNSTSW AX yakalaması birbirinin yerine geçmez.

İlk karşılaştırma sabiti0, ikinci sabiti10'dur. Kaynak önce `TEST AH,5/JNZ`,
sonra `TEST AH,41/JP` uygular. Normal sıralı karşılaştırma sonuçlarında aralık
**0≤mesafe≤10** olur. Negatif, büyük ve unordered sonuçlar başarısızlık
dalına gider. Model doğrudan captured AX maskelerini tüketir; gerçek x87
hesabı, exception/control word veya float/helper doğruluğunu varsaymaz.

Aralıktaysa00462630 taze seçili kimliği verir. Kimlik zaten aynıysa0046493c
atlanır. Farklıysa obje pointer'ıyla seçim yardımcısının normal dönüşü
gerekir. Ardından context+8'e bulunan kimliğin store planı çıkar. Kaynak
yalnız AL1 yazar: eşleşme dalında üstEAX seçili kimlikten, değiştirme dalında
seçim helper'ından sonra gözlenen EAX'tan kalır. Son cleanup, PUSH/POP ile
korunan bu dönüşten ayrıdır. Cleanup beklerken store kaydı korunur.

`ItemBreakNpcCycleFrame`, mevcut tipli envanter korumasını ve NPC çocuğunu
aynı caller'a bağlar. Dışarıdan raw NPC EAX/normal bayrağını reddeder. Çocuk
tamamlanınca ayrıca parent normal dönüşü gerekir. Başarısız çocuk mevcut
caller stop/notice yolunu, başarılı çocuk tipli clock yolunu açar; bu yerel
çağrı planları gerçek oyun seçimi, hareket veya item kırma işlemi değildir.

16 yeni test; toplam3916 test geçti. UI375 bağlı/148 bağlanmamış olarak
değişmedi. Native string/lookup/obje/koordinat/distance/select/cleanup etkileri,
kırma isteği serileştirmesi ve gerçek oyun bağlantısı henüz doğrulanmadı.
