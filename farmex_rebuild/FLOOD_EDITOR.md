# Çalışan yerel Flood liste düzenleyicisi

Güncelleme: aşağıdaki ondalık-alt-küme sınırlaması artık önceki aşamayı anlatır. Panel yeni scalar RTL ayrıştırıcısı ve bağımsız fallback10 politikasına bağlandı; güncel kapsam ve native exception sınırları [RTL panel bağlantısında](RTL_INTEGER_PANEL.md) açıklanır.

Gerçek `ConfigurationPanel` üzerindeki üç düğme artık çalışır: `btnAddFloodList`, `btnRemoveFloodList`, `btnClearFloodList`. Üç gerçek girdi (`cmbAddFloodList`, `txtAddFloodList`, `txtAddFloodingWait`) ve `lwFlooding` Treeview'i kullanılır. Değişen satırlar mevcut profil mekanizmasıyla kaydedilir ve yeniden yüklenir. `flood_editor.py` immutable yerel satırlar üzerinde işlem planı üretir; panel bu sonucu kendi listesine ve widget'ına uygular.

Eklemede kaynak kanıtıyla kullanılan davranışlar: kanal caption, mesaj subitem0, gecikme subitem1; gecikme64bit değerinin düşük DWORD'unun signed yorumu;5'ten küçükse ekleme yok. Tekrar eden ve boş mesajlar ayrıca engellenmez. Seçileni sil, kendi Treeview'inin tek seçili satırını kaldırır; seçili yoksa listeyi değiştirmez. Temizle yalnız Flood listesini boşaltır. Diğer profiller/listeler etkilenmez. Başarılı eklemede yeni satır seçilir; bu, bağımsız arayüzümüzün seçim politikasıdır ve kaynak VCL ile eşliği iddia edilmez.

Bu **bağımsız yerel UI uygulamasıdır**. Daha önce çözülen native çağrı modellerinin helper receipt'leri gerçek VCL dönüşü diye üretilmez. Kaynak `MessageAddClickFrame`/`MessageListDeleteFrame` API modelleri ayrı kalır. Panel henüz kaynak byte-row derleyicisine veya gerçek oyun worker'ına bağlanmış değildir. Bu nedenle düzenlenebilir alanların compiler inventory sayısı bu aşamayla artırılmaz. Gerçek yerel liste düzenleme artık vardır; native VCL semantiği veya oyuna gönderim doğrulanmış değildir.

Sayı ayrıştırıcısının açık kapsamı: boşlukla çevrili isteğe bağlı +/− işaretli ASCII ondalık, en fazla21 karakterlik sayı gövdesi, signed64 aralığı. Diğer biçimler ve taşma açık hata verir, mevcut listeyi korur. Native `StrToInt64` hex/boş/diğer hata yolları ve fallback10 ile tam eşlik henüz uygulanmadı; bu girdilerde kaynakla aynı davranış iddiası yoktur. Unicode metin yerel listede korunur; native ANSI dönüşümü yapılmaz. Bu eksikler tüm hedefin açık kalan gereksinimleridir.

`btnAutoFlood` ve `btnChatSelected` bu UI sürümünde bağlı değildir. Timestamp/index/enable source shadow'u veya byte-row derleme durumu burada oluşturulmaz. Genel eski Flood simülasyonu ayrı bir gösterimdir. Profil yüklemede önceki düzenleme sonucu silinir ve yeni belge/widget'lar bağlanır.

Doğrulama:6 yeni saf model testi ve gerçek gizli Tk widget testi; düğme invoke, ComboBox seçimi, Text trace, Unicode, lowDWORD5 sınırı, duplicates/empty, seçimsiz silme, doğru satırın silinmesi, unsupported sayı girdisinde liste korunması, profile roundtrip ve disabled worker düğmeleri. Tam UI testi1037 kontrol/11 form/18 sekmeyi kapsar. Testler kendi uygulamamıza aittir, orijinal VCL runtime veya oyun oturumu testi değildir.
