# Farmex rebuild

Knight Online için FarmexBot davranışlarının REA yaklaşımıyla incelenmesi ve
bağımsız bir yerel uygulamada yeniden modellenmesi. Geliştirme sürümüdür.

## Güncel durum

4933 yerel test ve yeni tam arayüz kontrolü (1037 kontrol, 11 form, 18 sekme) geçti. Görev arama child frame'i Al/Ver sağlayıcısına bağlandı; iç cleanup ve ayrı outer dönüş öncesi kuyruğa kayıt eklenmez.
Al/Ver düğmeleri açık gözlemlerle ortak yerel kuyruğa bağlıdır. Gerçek oyun veri
edinimi, gönderim ve uçtan uca uyumluluk doğrulanmadı. Test sayısı tamamlanma
yüzdesi veya orijinal botla tam eşlik kanıtı değildir.

## Çalıştırma

Windows ve Python 3.9 veya üzeri; Tkinter gereklidir.

```powershell
cd farmex_rebuild
python app.py
python -m unittest discover -p "test_*.py"
python -u smoke_ui.py
```

GUI doğrulaması kendi uygulamasını açar; oyuna bağlanmaz. Bazı native referans
deneyleri ayrıca Windows derleyicisi veya dış fixture gerektirir; kapsamları
ilgili belgelerinde açıklanır.

## İçerik

- `farmex_rebuild/`: uygulama, testler, yerel modeller ve aşama belgeleri.
- `analysis/`: seçilmiş analiz, kapsam ve ikili kanıt raporları.
- `verification/`: bu snapshot için tam test ve arayüz kayıtları.
- `SNAPSHOT_MANIFEST.json`: kopyalanmış kaynak ve kanıt dosyalarının SHA-256 değerleri.

Orijinal EXE/DLL/SLV dosyaları, oyun dosyaları, üyelik/giriş bilgileri, büyük
disassembler dökümleri, araç zincirleri ve geçici çalışma dosyaları dahil edilmez.
Eski doğrulama belgeleri tarihsel aşamalardır; güncel kapsam
`farmex_rebuild/QUEST_LOOKUP_COMPOSITION_VALIDATION.json` içindedir. Bazı analiz yolları
yerel çalışma ortamını gösterir; harici orijinal ikililer bu repoda yoktur.
