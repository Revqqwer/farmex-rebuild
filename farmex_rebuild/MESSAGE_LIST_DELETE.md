# Flood listesinden silme callback'leri

`message_list_delete.py`, Richard `004b14a4` (`btnRemoveFloodListClick`) ve `004b14dc` (`btnClearFloodListClick`) normal callback gövdelerini modeller. Her biri18 assembly kaydıdır. Published method adları ve list member+0xb98 iki ikilide doğrulandı. Giriş sınırları callback yerel stack hazırlığından sonraki `004b14b0` ve `004b14e8`; bitişler register/stack epilog öncesi `004b14d7` ve `004b150f`.

Önce `lwFlooding` virtual+0x148 veya+0x13c çağrısı yapılır. Sabitlenmiş `vcl260.bpl` SHA256 `84ea9ebbdc4570cb23f4856e7bae7541c2847ef6d1e4b34561f918dbd5f83cc6` içindeki `TListView` ve `TCustomListView` VMT'leri bu slotları sırasıyla `DeleteSelected` (`50d93488`) ve `Clear` (`50d93578`) export'larına bağlar. Bu dosya kanıtıdır; oyunda yüklenmiş VCL sürümü veya override edilmiş runtime nesnesi doğrulaması değildir.

UI işleminin ayrı normal receipt'inden **sonra** global561f55 BYTE yeniden okunur. Sıfırsa liste derlenmeden callback sınırına dönülür; bu kapı UI işlemini engellemez. Herhangi bir nonzero BYTE'da `0045c488(00569910)` typed derleyicisi çalışır, ardından çağıran normal dönüşü ayrıca beklenir. Callback'te aktif Flood BYTE, indeks veya zaman damgası sıfırlaması yoktur; böyle bir reset eklenmedi.

Virtual işlemin gerçekleşmiş etkileri modele uydurulmaz. `DeleteSelected` için bir sıra indeksi düşürmek veya `Clear` için yeni native UI sonucunu varsaymak yerine, gerçek VCL davranışı ayrı kalır. Child derleyicisi kendi taze UI/count/string gözlemlerini ister. Source callback kontrol akışı ile virtual helper semantiği birbirinden ayrıdır. Kendi arayüzüne yapılacak stable binding ayrıca doğrulanmalıdır.

8 yeni test: iki slot/düğme, mutation→gate sırası,0 ve tüm nonzeroBYTE dalları, typed child/parent ayrımı, erken parent receipt'in tüketilmemesi, aynı çağrıda prefix korunması, tamamlanmış callback'in tekrarlanmaması ve native doğrulama bayrakları. Tam VCL/native/SEH/event/UI/canlı sertifikası değildir.
