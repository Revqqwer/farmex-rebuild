# Gönderici adresinin kaynak referanslarını yeniden denetleme

21 Ekim2026. Profil seçimi ve initializer değerleri önceki analizde zaten modellenmişti. Bu aşamadaki yeni iş, baştaki sıfırları farklı yazılan assembly adreslerini aynı aramada toplamak ve ek referansları sınıflandırmaktır.

Önceki audit, `0x553e84` ve `0x553e90`alt dizelerini arıyordu. Bu biçimde dört mention bulunuyordu; `0x00553e84/90`gibi sıfır dolgulu operandlar kapsam dışında kalıyordu. Düzeltilen regexve sabit adres kümesi denetimi15başvuru verir:13memory-readve2address-argument. Ek kaynak gövdeleri de disk doğrulandı; yeni rapor1375benzersiz mevcut talimat kaydını kapsar. Önceki rapor tarihsel kanıt olarak korundu, üzerine yazılmadı.

553e90için kaynak sender464918alanı taze okuyupCALL EAXyapar.4e2f8cve4e3014alanı okuyup sırasıyla+1CC/+37ile başka gözlenen DWORDdeğerlerini karşılaştırır; bu karşılaştırmalar slota yazım değildir.464834içindeki `PUSH 553e90`memcpykaynak argümanıdır: slotun dört baytı yerel şablon ofsetine kopyalanır.553e84için de aynı kaynak-argüman ilişkisi doğrulandı. Bu fonksiyon çalıştırılmadı; uzak bellek işlemi veya thread başlatılmadı.

Bu kapsamda sender alanlarının iki bilinen kurucu tarafından bağlama göre yazıldığı doğrulanmaya devam ediyor. Güncel US kurucusu4fd640, Steam kurucusu4e4398; caller553e3cbağlamını gönderir. Fiziksel slot553e84için literal'ler1128a94/11eaa84, slot553e90için70b360/6241a0'dır. Bunlar runtime gözlemi veya ABIsertifikası değildir.

Profil detector4a199cTApplication.GetExeName→ANSI→ExtractFilePath→`steam_api.dll`eklendiği yol→FileExists(...,true)zinciridir. ALnonzeroise2, sıfırsa1döner. Bu bilgi yeni bulunmuş sayılmadı. Startupiki farklı modeokuması yapar; tekif/elseveya değişmez global varsayımına indirgenmez.

01:13yerel dosya kontrolünde kurulu EXEhash'i korunmuş güncel USdisk snapshot'ıyla aynıydı; yanındaki steam_api.dllbulunmadı. Eğer native ApplicationEXEbu konumdaysa USdalını destekleyen bir dosya durumudur. Gerçek uygulama EXEyolu ve FileExistsdönüşü gözlenmediğinden canlı profil seçimi otomatik doldurulmadı.

Güncel70b360adayının önceki doğrusal disk çözümlemesi ABIkanıtı olmaya hâlâ yetmiyor. Bu referans düzeltmesi çalışan bağlantı sağlamaz. Aliased/hesaplanmış/dış modül/dinamik yazımlar dışlanmadı. Salt literal aramasında yazıcı görülmemesi, runtime'da değer sabittir kanıtı değildir.

Çalışma kodu/UIdeğişmedi; son tam test3025, yeni koşu yok. Mevcut Ghidra/PEkanıtları kullanıldı; yeni REA Evidence üretilmedi. Güncel audit: `work/audit_source_profile_selection.py --output outputs/FarmexBot_kaynak_profil_tam_referans_kaniti.json`.
