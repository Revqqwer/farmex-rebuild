# Durum mesajındaki64 bit oran hesabı

Önceki `ratio_ftol_eax` adı yanlıştı. Güncel339 instruction'lık004f9f68 gövdesinde 004626f8 sonucu EDX:EAX olarak saklanır;004626d8 sonucu100 ile00503e38 yardımcısında çarpılır;00503e75 yardımcısı saklanmış ilk sonuca böler. Bu iki yardımcı tam sayı çarpma ve yazılımsal tam sayı bölmesidir. FPU/__ftol dönüşümü yoktur. Alan adı `ratio_division_eax` olarak düzeltildi.

`source_math64.py` şu sonuç bitlerini üretir:

1. İkinci getter'dan gelen hamQWORD100 ile çarpılır; yalnız düşük64 bit kalır.
2. Ürün ve ilk getter'ın hamQWORD değeri işaretli64 bit sayılar gibi bölünür; bölüm sıfıra doğru yuvarlanır.
3. Sonucun EAX kısmı ve bundan AL baytı durum mesajına bağlanır.

Kaynak bölücü genel bir CPU IDIV64 değildir. ÜstDWORD ve bölen alanlarına göre hızlıDIV EBX veya64 adımlı SHL/RCL/CMP/SUB döngüsü kullanır. Sıfır bölen hızlıDIV yolunda işlemci bölme hatasına gider; model bu durumda sonuç üretmez ve mesajı serileştirmez. Gerçek Windows istisna teslimi/SEH yolu doğrulanmadı. MIN_INT64/-1 ise yazılımsal döngü ve son iki-tümleyen işaretiyle tekrar8000000000000000 üretir; Python'ın sınırsız pozitif tamsayısını veya IDIV64 taşma davranışını doğrudan kullanmak eşdeğer değildir.

Örneğin ham numerator=ffffffffffffffff ve denominator=50 için önce ürünffffffffffffff9c(-100), sonra bölümfffffffffffffffe(-2), mesaj baytıfe olur. Taşmayı bölmeden sonra uygulamak bu sonucu değiştirebilir.

`build_status_from_ratio`, bağımsız bir sonuç alanı kabul etmeden hesabın EAX sonucunu `session_status_wire.py` üreticisine bağlar. Getters normal döndükten sonraki hamQWORD gözlemleri girdidir; canlı getter, nesne kimliği veya veri anlamı sertifikası yoktur. Durum/mod seçimi ve string dönüştürme hâlâ ayrı gözlemlerdir.

004626f8 ve004626d8, aynı kök global553e7c ile farklı553fc8/553fcc offsetlerini kullanıp0045dc0c yardımcısına gider. Son yardımcı null adres/hata yollarında EDX:EAX sıfır döndürür; normal okuma öncesinde VirtualProtect(adres,8,40,&oldProtect) çağrısı vardır. Bu yalnız kaynak gözlemidir: bağımsız model bu çağrıyı çalıştırmaz ve koruma değişimi, okuma hakkı veya canlı erişim engelinin nedeni hakkında sonuç çıkarmaz.

İki sürümde6 yordamın922 instruction kaydı byte doğrulandı;5 yeni REA ve1 önceki REA çıktısı karşılaştırıldı.9 yeni test; sıfıra bölme, işaretli yuvarlama,64 bit sarma, hızlı/yavaş yol ve mesaj bağlantısını sınar.400 geniş operand çifti ayrıca ayrı bir64 adımlı instruction döngüsüyle karşılaştırılır. Bu testler native çalıştırma değildir.

Kanıt: `outputs/FarmexBot_oturum_oran64_kaniti.json`; yeniden üretim: `work/audit_session_ratio.py`.
