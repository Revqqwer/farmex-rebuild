# Transformation üretici öneki ve tüketici araştırması

`transformation_settings.py`,0040918c yordamının137 talimatlık0040929a..004094ad bölümünü modeller. Bu, bütün417 talimatlık ayar yordamının veya onu çağıran event'in tamamlanması değildir. Daha önceki bölüme ulaşıldığına dair açık receipt gerekir; sonraki bölüme ulaşınca complete olur. Bellek okunmaz/yazılmaz; VCL getter span'ları ve normal dönüşler ayrı gözlemlerdir.

Etkinlik getter'ının raw AL değeri context+20'ye yazılır; ardından context+21 koşulsuz1 yapılır. Kaynak boolean'ı Python bool'a daraltmaz: AL2 de BYTE2 olarak kalır. Bekleme temporary'si kurulur ve Text getter'ından alınan Unicode metin, dış `StrToInt32` fonksiyonuna girer. Bu çağrı StrToInt64/default-catch helper'ı değildir. Model lexical dönüşüm yapmaz; normal rota ve raw EAX gözlemi ister. EAX×1000 düşük32 bit sonucu context+28'e, temporary temizliğinden önce yazılır.

`exception_unresolved` rota gözlemi varsa model açık eksikle durur. Etkinlik/rearm önekini geri almaz, bekleme varsayılanı veya exception cleanup sonucu uydurmaz. Sonraki route getter'ı ancak başarılı parser ve cleanup'tan sonra okunur; raw AL context+22'ye gider. Combo fullDWORD sonucu18 kimlikten birini seçer; diğer değerler ilk skill'e döner. context+24'e yazıldıktan sonra source'un sonraki ayar bölümü başlar.

`TransformationSettingsFrame`, tüketilen enabled/parser/metin önekini korur. Cleanup beklenirken yeni input farklı enabled/parser sonucu getirse de önceki değerler kalır. Henüz okunmayan route ve combo daha sonraki capture'dan gelebilir. Önceki `compile_transformation` kendi strict signed-decimal politikasıyla ayrı kalır; bu yeni raw source modeli onun lexical davranışını native kabul etmez.

Periyodik tüketici araştırmasında parametre+20/+21/+28 alanları içeren00500700 adayına bakıldı. Fakat bilinen çağrı zinciri0040d554→00501b80→00500700,568320 context'ini geçiriyor; TS producer context'i562050'dir. Bu gövde004c8498 veya004c8388'i doğrudan çağırmıyor. Benzer ofsetler yeterli bağ kanıtı olmadığından TS işçisi olarak uygulanmadı. Bu adayın hiçbir dolaylı TS etkisi olamayacağı iddia edilmez.

Eski/güncel keşfedilmiş fonksiyon export'larında562050 tabanına14 açık operand referansı bulundu; source ayar çağrılarıyla ilgilidir.004c8498'e açık call yalnız00455ec0 post-Town gövdesinde görüldü. Etkinlik/rearm/route/wait mutlak adres baytlarının dosyada yokluğu yeniden kontrol edildi. Bu sonuçlar alias, hesaplanan adres, dolaylı çağrı, dış modül, data pointer'ı veya keşfedilmemiş kodu dışlamaz; otomatik periyodik TS'nin bulunmadığına kesin kanıt değildir.

Yedi yeni test; giriş receipt'i, raw AL/rearm öneki, parser exception boşluğu, metin lexical varsayımı yapmama, IMUL sarması,18/default skill, cleanup öncesi wait store ve consumed/fresh alan ayrımını kapsar. İki sürümde toplam274 model-span kaydı, diğer producer/selector/callback kayıtları ve güncel aday/caller kaydı dahil1465 mevcut talimat diskten doğrulandı. Dört gerçek REA raporu assembly ile eşleşti. Yeni ikili keşif kapsamı, periyodik tüketici veya canlı beceri kullanımı sertifikası değildir.

Arayüz değişmedi; dört TS kontrolünün UI compiler bağı hâlâ ayrı iştir. Genel periyodik tetikleme, yeniden kurma ve rota kapısı tüketicileri açık kalır.
