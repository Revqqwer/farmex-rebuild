# Relative chat skill wrapper ve ortak operand rolü

Sonraki API bağı: generic alt model artık üç sınıf tüketicisine isteğe bağlı typed child olarak bağlanabilir. Aşağıdaki bağın bulunmadığına ilişkin notlar önceki aşamanın kapsamıdır. Native etkiler ve UI bağı hâlâ açık. [Güncel generic bağ](GENERIC_CONSUMER_BINDING.md).

20 Ekim 2026. `generic_chat_skill.py`, `004655e8` generic yardımcısını modeller. Eski/güncel kaynakta bu28talimatlık gövde ve karşılaştırma için `00465640` gövdesi dahil **96 talimat kaydı** disk baytlarıyla doğrulandı. Bu Ghidra/PE kanıtıdır; yeni REA Evidence veya canlı yürütme değildir.

## Kaynak davranışı

`004655e8`, önce `0046256c` yardımcısının EAX sonucunu alır; low32 `EAX*1000 + relative_skill` hesaplar. Örneğin sentetik class EAX107ve relative4için action107004olur. Signed/unsigned bit yorumundan bağımsız olarak taşma32bit sarılır; kaynak overflow flags'lerini koşul olarak kullanmaz.

Hesaplanan action, `00464990` lookup yardımcısına verilir. Sonra taze `553e80` root-slot değeri üzerinden root okunur; `root + 5540a0` ile çağrı context'i alınır. Lookup sonucu ve target actor DWORD'u fiziksel olarak bu sırayla push edilir; `553ee4` hedefi çağrılır. Dönen **ham EAX** yerel değişkene yazılıp tekrar EAX'a alınır. Yalnız düşük BYTE veya bool'a indirgenmez.

Bu wrapper **`00465640`'ı çağırmaz**. İki gövdedeki son sekiz talimat, lookup sonucunun farklı local slot'u normalleştirilince aynı operand rolüne sahiptir. Bağımsız uygulama mevcut operand kodunu paylaşır; çıktı çağrısının source helper kimliği `004655e8` olur. Eski `plan_alternate_skill` varsayılanı `00465640` olarak korunur.

## Bağımsız sözleşme

`GenericSkillObservation`, relative skill, target actor DWORD, class helper normal dönüşü ve ham class EAX ister. Sonraki `SkillObservation.action_id`, hesaplanan action ile; actor alanı da wrapper'ın target actor'üyle tam eşleşmelidir. Farklı snapshot sessizce bağlanmaz.

Lookup wrapper normal dönüşü, dolaylı target normal dönüşü ve target'ın ham EAX'ı ayrı kalır. Bütün alanlar verilmiş olsa bile bu makbuzlardan biri eksikse model tamamlanmaz. EAX0bilinen bir false sonuç olarak tamamlanabilir; başarılı server/skill etkisi sayılmaz. Lookup wrapper'ın diğer mode'larda0üretip yine dispatch'e devam etmesi korunur; kaynakta olmayan “lookup0ise çağırma” guard'ı eklenmez.

Operand map'leri mevcut modelin **kararlı own snapshot** sözleşmesini kullanır; instruction-by-instruction değişen canlı global okumaları sertifikalanmaz. Mode1lookup ECX'i inherited/unknown kalır; sıfır context uydurulmaz. Target callee'nin8bayt temizlemesi ABI varsayımıdır, gerçek ABI kanıtı değildir.

`versioned_generic_skill(source_hash,profile,...)` factory'si eski/güncel kaynak hash'ini ve US/Steam profilini açıkça ister. Mevcut sürümlü literal tablolarını kullanır; seçilmiş tabloyla çelişen fixture değerlerini reddeder. Eksik current root gözleminde legacy adresi otomatik denemez. Bunlar canlı seçilmiş profil veya callable target kanıtı değildir. Kaynak metadata'sı olmayan raw gözlemler de ayrı API'de mümkündür; onlar sürümlü fixture olarak etiketlenmez.

Bu model henüz Mage/Rogue/Priest tüketicilerinin `generic_skill` sınırına bağlanmadı. Onların generic normal dönüş/EAX girdileri önceki şekilde açık kalır. Bu yeni alt modelin tamamlanması gerçek native wrapper'ın çalıştığını veya üst tüketicinin döndüğünü kanıtlamaz. Tüketici bağında ayrıca argüman/sonuç ve ayrı üst normal dönüş kontrolü gerekecektir.

## Doğrulama

**10 yeni testle toplam2845 test geçti (7.025 saniye).** Prefix hesabı ve32bit taşma, source helper kimliği, action/actor uyumu, her normal/raw dönüş boşluğu, mode1/2/other, sıfır EAX, legacy API varsayılanı ve açık sürüm/profil fixture seçimi sınandı. UI/native C değişmedi; UI yeniden test edilmedi. Hiçbir native target veya Windows süreç işlemi yürütülmedi.

Kaynak: `outputs/FarmexBot_generic_chat_skill_kaniti.json`; üretici `work/audit_generic_chat_skill.py`. Uygulama kaydı `GENERIC_CHAT_SKILL_VALIDATION.json`.
