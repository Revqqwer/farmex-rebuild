# Free Genie — pasif kaynak analizi

`chFreeGenie` kontrolü, `chGenieWithBot` ve kupon yenileme yardımcısından ayrı bir kaynaktır. Güncel published form alanı51C, callback4aec84ve üretici4576ecbağı doğrulandı. Callback561f55kapısı açıksa562194bağlamıyla genel ayar üreticisini çağırır.

Üreticide45866eadresi checkbox düşükALdeğerini context+102BYTEalanına yazar. Bu alan hemen yeniden okunur. Sıfırsa45869dyoluna geçilir; seçiliyse aşağıdaki çağrı hazırlığı yapılır:

1. Yazılacak argüman0x78hazırlanır.
2. DWORD[553e7c]adresinden guarded DWORD okuyucu45dc44ile kök sonucu alınır.
3. SonucaDWORD[554074]eklenir; adres hesabı32bit sarar.
4.45de4cile tek baytlık yazma girişimi çağrılır.

45de4cgövdesi VirtualProtect(adres,1,0x40,&eskiKoruma)çağrısı yapar. DönüşEAX0ise kopyalamadan çıkar; nonzeroise argümanın düşük baytından memcpy(adres,&argüman,1)çağırır. Bu gövdede eski korumayı geri yükleyen çağrı yoktur. Bu bir statik kod tespitidir; inceleme sırasında bellek yazımı veya koruma değişikliği yapılmadı.

554074ayrı Genie kalanBYTEokuyucusunda da kullanılan ofset slotudur. Değer0x78=120olmasına rağmen bunu “120saniye” veya gerçek süre yenilemesi olarak adlandırmak için kanıt yoktur. Sunucu tarafındaki süre/üyelik/yenileme etkisi doğrulanmadı. Kupon tarama4ca588ve970101yerel kuyruk kaydı bu ayar yazımının yerine geçmez.

Profil kaydetme42b829..42b8acve yükleme439bd3..439c38kesitlerinde aynı kontrol ve `GENEL`/`FREEGENIE`literal'leri bulundu. Yükleme yardımcısına0argümanı hazırlanır ve dönen sonuç VCLsetter'a verilir; yardımcının hata/eksik anahtar ve setter callback etkileri bu kesitlerden tam sertifikalanmaz.

Eski ve güncel snapshot'larda toplam224talimat kaydı disk baytlarıyla, VirtualProtect/memcpy import kimlikleri ve dört profil literal'iyle doğrulandı. Kaynak korunmuş Ghidra/PE/DFMverisidir, yeni REA Evidence değildir. Aynı102ofsetini farklı struct'larda kullanan başka fonksiyonlar bu özelliğin tüketicisi sayılmadı; bağlam eşitliği gerekir. Bu kesitte sürekli tekrar eden timer kanıtlanmadı.

Runtime/UIkodu değiştirilmedi; son tam test sonucu3025olarak kaldı. Bu aşamada yeni test veya canlı okuma yapılmadı. Bulgular pasif analizdir; bağımsız sürümde gerçek yazım uygulaması veya canlı Free Genie eşdeğerliği tamamlandı sayılmaz.
