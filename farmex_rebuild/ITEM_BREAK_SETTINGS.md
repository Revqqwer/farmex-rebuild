# Item kırma ayar üreticisi

23 Ekim 2026. Model, Richard `00470cc4` içindeki `00470cd5..00470d87`
normal akışını kapsar:53 talimat. SEH kurulumu, epilog, gerçek VCL/RTL
çağrıları ve ortak başlat/durdur yardımcısının gövdesi yürütülmez.

| Form alanı | Kaynak kontrol | Yerel yapılandırma |
|---|---|---|
| ec0 | chAutoCrashItems | +0: getter EAX sonucunun AL baytı |
| ec8 | txtCrashItemSpeed | +4: sayısal yardımcı sonucunun düşük DWORD'u |
| a28 | rdAbbys | AL sıfır değilse +c alanına tek DWORD0 yazım planı |

Sayısal alan kapalı kutuda da okunur. Kaynak, sayısal yardımcıya varsayılan1
geçer. Model metinden dönüşümü tahmin etmez: mevcut `SourceIntegerFrame`
normal StrToInt64 veya açık catch-landing kanıtını tüketir. Negatif/büyük
sonuçlar bu üreticide düşük32 bit olarak tutulur; ek hız sınırı uygulanmaz.

Metin temizliği ve Abyss getter'ından sonra kaynak yapılandırma+0 baytını
yeniden okur. `fresh_enabled_byte` ayrı girdidir; önceki kutu/store değerinden
otomatik türetilmez. Sıfırsa `0040ae0c(561f34,0)`, diğer baytlarda
`0040ae0c(561f34,1)` çağrı planı çıkar. Fiziksel PUSH sırası sırasıyla
`(0,561f34)` veya `(1,561f34)` olur. Yardımcının normal dönüşü ayrıca gerekir.

`ItemBreakSettingsFrame` ulaşılan getter, metin, dönüştürücü, store ve karar
girdilerini boşluklar arasında korur. Tekrar gelen örnek önce tüketilmiş
girdileri değiştirmez. Çıktı yalnız kendi scalar/store ve çağrı planıdır;
oyuna yazma, item kullanma, paket, DLL veya süreç erişimi yapmaz.

Eski ve yenilenmiş Richard ikililerinde ana65, integer48, GetText1,
cleanup16 ve iki callback14+14 olmak üzere toplam316 assembly kaydı
disk baytlarıyla doğrulanır. Üç published field kaydı iki ikilide de bulunur.
İki callback profil kapısı561f55 açıkken context569a20 ile üreticiyi çağırır;
callback gövdeleri yeni modelin tam fonksiyon sertifikası olarak sayılmaz.
Yeni REA analizi yenilenmiş65-talimat gövdesiyle karşılaştırılır.

Bu aşama API modelidir. Panel compiler'ına yeni kontrol bağlanmadı;375 bağlı
girdi ve148 bağlanmamış kontrol sayıları değişmedi. Item kırmanın NPC seçimi,
beklemesi, envanter kontrolleri, alt modları ve sunucu sonucu tamamlanmış
sayılmaz. Native yürütme ve canlı uyumluluk kanıtı yoktur.
