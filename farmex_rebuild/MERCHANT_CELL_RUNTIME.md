# Gerçek yerel PM/GİT hücreleri

`OwnedMerchantCells`, gerçek sonuç tablosundaki satır/sütun kimliğini tüketen bağımsız yerel frontend'dir. Native kaynakta sabit ekran-X aralıklarını kullanan `MerchantCellFrame` ayrı korunur; frontend bu frame'i çalıştırmış veya native gözlemler üretmiş sayılmaz. Kaynak form/DPI/hit-region uyumluluğu açık kalır. Böylece yerel hücre bağlantısı ile orijinal piksel handler'ı eşliği aynı sertifika sayılmaz.

PM, görünür caption Unicode metnini açık kendi Windows kod sayfasıyla ANSI'ye çevirir. CString'in ilk NUL'a kadarki adı için doğrulanan35/01/WORD/name byte yapısını hazırlar.100 byte üstü name kopyası counter-alias kapsam eksiğidir. Yerel preview admission gate1 ve kendi GetTickCount politikası kullanılır; bunlar oyun bağlantı gözlemleri değildir. Kayıt, Flood'un mevcut kendi kuyruğunu paylaşır; otomatik Flood enabled/index/timestamp durumu değiştirilmez. Kuyruk oyuna boşaltılmaz ve PM teslimi iddia edilmez.

GİT, kendi active/busy durumunu sıfırlar, kanonik X/Y sütunlarını ölçülmüş nearest-even integer→binary32 politikasıyla hazırlar ve Y/X fiziksel push sıralı bir hedef intenti saklar. Oyun hareket helper'ı çağrılmaz. Kaynaktaki üç SetEnabled/scan-session etkisi ayrı typed source frame'inde kalır; henüz handler'ı olmayan düğmeler sessizce etkinleştirilmez. Native inputlar bilinmeden SourceFrame'e sahte handle/return alanları doldurulmaz.

Gerçek `<ButtonRelease-1>` adapter'ı cell bölgesi, PM/GİT sütunu, seçili satır ve güncel immutable snapshot'ı kontrol eder. Widget satırı snapshot'tan farklıysa eski caption/koordinatla eylem üretilmez. Geçersiz CP tekrar codec/clock veya kuyruk etkisi uydurmaz; CP düzelince yeni click çalışabilir. Profil değişimi kendi cell intent geçmişini sıfırlar; ortak kendi kuyruğu korunur. Başlık tıklaması veya başka sütun PM/GİT işlemi değildir.

Tabloda source MinWidth/Width bilgileri uygulanır:110/200/50/90/45/45/0/0. Adet default90 yerine kaynak minimum50 olur, X/Y saklama sütunları genişletilmez. Bu değişiklik yalnız Merchant sonuç listesine uygulanır.

8 API testi ve gerçek Tk basma/bırakma olaylarıyla GUI kontrolü PM wire/shared queue, GİT float bitleri, stale row, codec hata/toparlanma, saklı koordinatlar ve profil sıfırlamayı doğrular. Ttk ilk mapped layout olmadan cell parcel üretmediği için GUI smoke kısa süre saydam/borderless/ekran dışı kendi root'unu eşler, sonra yeniden gizler. Tk bu sırada kendi root'unu aktive edebilir; test withdraw sonrası kendi process'inin ön planı tutmadığını denetler. Bu aşama kullanıcı/game pencerelerine input veya ekran yakalama yapmaz. Ön planın hiç değişmediği iddia edilmez.

Kalan işler: gerçek source hit geometry/CP/FPU/object identity, native PM sender/queue drain ve hareket çağrıları, source üç kontrol etkisinin scan oturumuyla bağı, cleanup/SEH ve canlı uçtan uca doğrulama. Yeni başarılı REA analizi yoktur; mevcut Ghidra/PE kanıtı, finite own native referans ve kendi frontend yürütümü ayrıdır.
