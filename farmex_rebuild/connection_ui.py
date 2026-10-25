import concurrent.futures
import tkinter as tk
from tkinter import ttk
from game_provider import ReadOnlyGameProvider, Observation, find_game_processes, ProcessDiscoveryError
from native_ipc import NativeVitalsProvider


class ConnectionPage:
    def __init__(self, frame, status):
        self.frame, self.status = frame, status
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.pending = None
        self.pending_mode = None
        ttk.Label(frame, text='Mevcut oyun oturumunu kontrol et', padding=10).pack(anchor='w')
        ttk.Label(frame, text='Bu kontrol yalnız HP/MP okumayı dener. Oyun eylemleri henüz etkin değildir.',
                  padding=10, wraplength=950).pack(anchor='w')
        self.profile = tk.StringVar(value='us')
        self.select = ttk.Combobox(frame, values=['us', 'steam'], textvariable=self.profile,
                                   state='readonly', width=12)
        self.select.pack(anchor='w', padx=10)
        self.mode = tk.StringVar(value='external')
        ttk.Radiobutton(frame, text='Oyun sürecinden salt okuma', variable=self.mode,
                        value='external').pack(anchor='w', padx=10)
        ttk.Radiobutton(frame, text='Hazır yayıncıdan HP/MP al', variable=self.mode,
                        value='native').pack(anchor='w', padx=10)
        binding = ttk.Frame(frame)
        binding.pack(anchor='w', padx=10, pady=5)
        self.publisher_pid = tk.StringVar()
        self.publisher_nonce = tk.StringVar()
        self.fixture = tk.BooleanVar(value=False)
        ttk.Label(binding, text='Yayıncı PID:').pack(side='left')
        ttk.Entry(binding, textvariable=self.publisher_pid, width=10).pack(side='left', padx=5)
        ttk.Label(binding, text='Oturum değeri:').pack(side='left')
        ttk.Entry(binding, textvariable=self.publisher_nonce, width=36).pack(side='left', padx=5)
        ttk.Checkbutton(frame, text='Kendi test yayıncımız (sentetik veri)', variable=self.fixture
                        ).pack(anchor='w', padx=10)
        ttk.Label(frame, text='Hazır yayıncı seçeneği oyunu veya yayıncıyı başlatmaz. '
                  'PID ve oturum değeri yayıncı testinden alınır; oyun bağlantısı henüz doğrulanmadı.',
                  wraplength=950, padding=10).pack(anchor='w')
        self.button = ttk.Button(frame, text='Oturumu kontrol et', command=self.check)
        self.button.pack(anchor='w', padx=10, pady=10)
        self.result = tk.StringVar(value='Kontrol bekleniyor.')
        ttk.Label(frame, textvariable=self.result, wraplength=950, padding=10).pack(anchor='w')

    def check(self):
        if self.pending is not None:
            return
        if self.mode.get() == 'native':
            try:
                provider = NativeVitalsProvider(int(self.publisher_pid.get()), self.publisher_nonce.get(),
                          profile=self.profile.get(), source_kind=1 if self.fixture.get() else 2)
            except ValueError as error:
                self.result.set('Yayıncı ayarları geçersiz: ' + str(error))
                return
            target_pid = provider.pid
        else:
            provider = ReadOnlyGameProvider(profile=self.profile.get())
            target_pid = None
        def observe():
            if target_pid is not None:
                return provider.observe(target_pid)
            try:candidates = find_game_processes()
            except ProcessDiscoveryError as error:
                return Observation('unavailable',error='Süreç listesi alınamadı: '+str(error),
                    failed_operation=error.failed_operation,error_code=error.winerror)
            if not candidates:
                return Observation('unavailable', error='Bu oturumdan oyun süreci görülemiyor')
            if len(candidates) != 1:
                return Observation('unavailable', error='Birden fazla oyun oturumu bulundu; tek oturum gerekli')
            return provider.observe(candidates[0])
        self.button.state(['disabled'])
        self.pending_mode = self.mode.get()
        self.result.set('Mevcut oturum kontrol ediliyor…')
        self.pending = self.executor.submit(observe)
        self.frame.after(100, self.poll)

    def poll(self):
        if not self.pending.done():
            self.frame.after(100, self.poll)
            return
        try:
            observation = self.pending.result()
            if observation.status in ('candidate', 'candidate_unverified', 'fixture_candidate'):
                fields = observation.fields
                text = 'HP: {hp}/{hp_max} • MP: {mp}/{mp_max}\n'.format(**fields)
                if observation.status == 'fixture_candidate':
                    text += 'Kendi test yayıncımızdan sentetik veri; gerçek oyun okuması değildir.'
                    self.status.set('Test yayıncısı • Sentetik HP/MP')
                else:
                    text += 'Okuma bağımsız olarak doğrulanmayı bekliyor.'
                    self.status.set('HP/MP adayı • Canlı doğrulama bekliyor')
            elif self.pending_mode == 'native':
                text = 'Yayıncı verisi kabul edilmedi (%s).\n%s' % (observation.status, observation.error)
                self.status.set('Yayıncı kontrolü • Veri alınamadı')
            elif observation.pid:
                verified = getattr(observation,'disk_identity_verified',False) is True
                text = ('Kayıtlı oyun dosyası eşleşti; canlı veri alınamadı.\n' if verified
                        else 'Oyun oturumu bulundu; kayıtlı dosya sürümü doğrulanmadı. Canlı veri alınamadı.\n') + observation.error
                self.status.set('Oyun dosyası eşleşti • Canlı veri yok' if verified else 'Oturum bulundu • Canlı veri yok')
            else:
                text = observation.error
                self.status.set('Oturum kontrolü: ' + observation.error)
            self.result.set(text)
        except Exception as error:
            self.result.set('Oturum kontrolü tamamlanamadı: ' + str(error))
        finally:
            self.pending = None
            self.pending_mode = None
            self.button.state(['!disabled'])

    def close(self):
        self.executor.shutdown(wait=False)
