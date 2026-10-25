# Otomatik dağıtım listelerinin üretimi

`allocation_producer.py`,004576ec'nin360 talimatlık00457700..00457c5f önekini modeller. Daha önceki native frame kurulumuna ulaşıldığına dair açık receipt gerekir; iki listenin üretiminden sonra sonraki genel ayar bölümüne ulaşınca complete olur. Bütün1219 talimatlık üretici veya callback tamamlanmış sayılmaz.

Form+f40 `LwAutoStat`, form+f44 `LwAutoSkill` listesidir. Üç görünüm sütunu `SkillIndex`, `Stat/Skill`, `Yap` biçimindedir; `SkillIndex` genişliği0 olduğu için gizlidir. Kaynak satır düzeni şöyledir:

| Native satır alanı | Kaynak UI verisi | Üretim |
|---|---|---|
| +0 | İlk alt sütun, index0 | Unicode→ANSI sonucu, AnsiString alanı |
| +4 | Ana başlık, gizli SkillIndex | 0045ef80 varsayılan−1, sonuç EAX düşükDWORD |
| +8 | İkinci alt sütun, index1 | Ayrı0045ef80 varsayılan−1, sonuç EAX düşükDWORD |

Native satır12 bayttır. `AllocationRow` bunların bağımsız semantik karşılığıdır: name bytes, actionDWORD ve thresholdDWORD. Ek `source_index` yalnız kendi metadata'sıdır, native satırın dördüncü alanı değildir. Bu nesne gerçek AnsiString pointer'ı veya oyun vektörü olarak paketlenmez.

İki etkinlik getter'ı raw AL olarak context+20/+21 store planına girer. Etkinlik0 olsa da stat vektörü temizlenip yeniden kurulur, sonra skill vektörü aynı şekilde kurulur. Liste satırlarını checked durumuna göre eleyen bir dal bu önekte yoktur. Her iterasyonda UI Count getter'ı yeniden çağrılır ve signed count>index koşulu uygulanır. Kendi model yerel bütçesini kaynak liste sonu olarak kabul etmez.

İsim temporary kurulumu/getter'ı, Unicode→ANSI atama/temizleme span'ı ve final ANSI bytes gözlemi ayrıdır. Locale/codec tahmin edilmez. Ana başlık ve eşik için iki ayrı generated `SourceIntegerFrame(text,0xffffffff)` vardır. Normal StrToInt64 EDX:EAX sonucu veya açık catch-landing receipt'i gerekir. Normal sonuç büyük QWORD olsa da yalnız düşükDWORD alınır. Boş/bozuk metin tek başına fallback−1 üretmez. Child tamamlandıktan sonra dış0045ef80 dönüşü ve ilgili UI temporary temizliği ayrıca gerekir.

Vektör size/capacity sonuçları fresh raw DWORD gözlemleridir; kendi row sayısından çıkarılmaz. Unsigned size<capacity ise hızlı helper00458ae8, diğer durumda iterator/00458b4c insert span'ı gerekir. Kaynak çağrı hızlı helper'a count1 verir; normal dönüş kuyruğundaki hesap end+12*count'tır. Model düşük32 end+12'yi üretir ve verilmiş çelişkili EAX capture'ını reddeder. Caller bu değeri vektör end alanına store planı yapar. Genişleyen dalın native allocator/end etkileri opaque kalır.

Append normal döndükten sonra satır, row-temporary cleanup beklenirken de üretilmiş ön ekte kalır. Devam çerçevesi tüketilen isim, parser ve helper sonuçlarını korur; satır tekrar eklenmez. `cleared_vectors` yalnız clear span'ı tamamlanan listeleri gösterir. Eksik clear durumunda boş `stat_rows` sonucu, önceki native vektörün gerçekten boş olduğu anlamına gelmez; bu alanlar yeni üretim önekidir.

On yeni test; giriş, flags0 iken liste üretimi, sütun çağrıları, bağımsız64bit/default dönüşümleri, eksik metin/child, signed count, capacity eşitliği, append sonrası cleanup, bounded devam ve hızlı end sarması/çelişkisini kapsar. Eski/güncel ikililerde3188 mevcut talimat kaydı ve yedi gerçek REA raporu eşleşti. Bunun720 kaydı yeni bounded producer öneğidir. Yeni binary keşif veya tam fonksiyon sertifikası değildir.

Bu aşama API/model bağıdır. UI liste snapshot'ı compiler'ı, ANSI adı gerçek sorgu pointer'ına bağlama, native vector/copy/allocator etkileri, tüketicinin canlı bellek okumaları ve gerçek puan dağıtımı açık kalır. Compiler kontrol sayısı293 ve sınırlı fonksiyon eşlemesi123 olarak kalır.
