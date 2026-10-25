# Monster Stone hedef secici

`monster_stone_selector.py`, 004c50d0 govdesinin kosullu gozlem modelidir. Gercek bellek okumaz, iterator calistirmaz, hedef degistirmez. Her helper icin sonuc ve normal donus ayri gerekir. Tamamlanmis model sonucu, fonksiyonun butun davranisinin cozuldugu veya oyunda calistigi anlamina gelmez.

Dongu ilk dugum sentinel olsa da adayi isler. Iki mesafe hesabi kind/state elemesinden once yapilir. Metrikler ham DWORD ve karsilastirmalar unsigned'dir. Ilk metrik mevcut en iyi degere veya ikinci metrik50'ye esit/kucukse isim yolu acilir. Daha sonra mode0 ve ilk metrik yeniden kontrol edilir; ikinci metrik tek basina hedef secmeye yetmez. Esit ilk metrikte sonraki aday kazanir. Son secilen kimlik signed olarak pozitif degilse sonuc temizlenir.

Isim storage16'dan kucukse inline kopya sayisi50, diger dalda yakalanmis pointer/storage kullanilir. Unicode donusumu ve temizligi opaque normal span'dir; codec tahmin edilmez. Kopya512'yi asarsa mevcut model acik eksikle durur; bu yerel model siniri kaynakta bir uzunluk guvencesi degildir. Kopya helper'inin destination/init/RTL ayrintilari burada yeniden uygulanmamistir.

EBP-48 slotunun iki ayri okumasi vardir, fakat kapsanan govdede acik yazari yoktur. Guard ve secim okumasi ayri gozlemler ister. ID actor pointer'indan turetilmez. Yardimci/alias etkileri dislanmadigi icin bu kaynak hatasi olarak ilan edilmez. Iterator hedefi553eb0 ve ECX icin56fb3c taze okunur; ABI ve dolayli cagri etkileri cozulmus sayilmaz. Yerel aday butcesinin bitmesi iterator sonu sayilmaz ve sonuc store'lari uretilmez.

`MSSelectorFrame` tuketilen gozlemleri korur. `MSCombatFrame('target_entry')` optional typed selector child kullanabilir; eksik child parent normal/EAX ile atlanamaz. Child tamamlandiktan sonra parent'in ayri normal donusu ve ayni fullEAX degeri gerekir. Child store planlari icinde kalir; gercek yazma yoktur.

13 yeni test; aday degisimi, unsigned/signed sinirlar, AL1 kontrolu, mod1 yolu, iki stack okumasi, do-while, isim sayilari, null allocation, iterator butcesi, devam cercevesi ve parent/child ayrimini kapsar. Eski/guncel PE'deki289'ar talimat ve gercek REA dosyasi yeni audit ile dogrulanir. Bu yeni ikili kapsami degil, mevcut kanitin davranis modeline baglanmasidir. Ana worker baglantisi ve canli uyumluluk aciktir.
