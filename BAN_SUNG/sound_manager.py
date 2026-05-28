import pygame
import math
import array
import random
from constants import *


class SoundManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SoundManager, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            self.enabled = True
        except Exception as e:
            print(f"Failed to init pygame.mixer: {e}")
            self.enabled = False

        self.sounds = {}
        self.bg_channel = None
        self.music_volume = 1.0
        self.sfx_volume   = 0.5
        self.current_track = None
        
        if self.enabled:
            pygame.mixer.set_num_channels(16)
            self.bg_channel = pygame.mixer.Channel(15)
            self.bg_channel.set_volume(self.music_volume)
            
            # Khởi chạy sinh âm thanh dưới nền để game khởi động ngay lập tức
            import threading
            threading.Thread(target=self._generate_sounds, daemon=True).start()

    def _generate_sound(self, name, freq, duration, vol=0.1, wave_type="square"):
        if not self.enabled:
            return
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = array.array('h')
        max_amplitude = int(32767 * vol)

        # Local lookups for optimization
        sin = math.sin
        floor = math.floor
        random_val = random.random
        append = buf.append
        two_pi = 2 * math.pi

        for i in range(n_samples):
            t = float(i) / sample_rate
            if wave_type == "square":
                val = max_amplitude if sin(two_pi * freq * t) > 0 else -max_amplitude
            elif wave_type == "sine":
                val = int(max_amplitude * sin(two_pi * freq * t))
            elif wave_type == "saw":
                val = int(max_amplitude * (2 * (t * freq - floor(t * freq + 0.5))))
            elif wave_type == "noise":
                val = int(max_amplitude * (2 * random_val() - 1))
            else:
                val = 0
            
            # Envelope (fade out)
            env = 1.0 - (i / n_samples)
            val = int(val * env)
            
            append(val)
            append(val)

        self.sounds[name] = pygame.mixer.Sound(buffer=buf)

    def _generate_complex_sound(self):
        if not self.enabled:
            return
        sr = 44100
        
        # AK Shot - Try loading external sound first
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        sound_path_space = os.path.join(base_dir, "ANH", "sung ak.mp3")
        sound_path_nospace = os.path.join(base_dir, "ANH", "sungak.mp3")
        
        loaded = False
        for p in (sound_path_space, sound_path_nospace):
            if os.path.exists(p):
                try:
                    self.sounds["ak_shot"] = pygame.mixer.Sound(p)
                    loaded = True
                    break
                except Exception as e:
                    print(f"Loi load file am thanh AK {p}:", e)
                    
        if not loaded:
            # Fallback procedural generation - Metallic crack
            dur = 0.3
            buf = array.array('h')
            for i in range(int(sr * dur)):
                t = i / sr
                env = math.exp(-25 * t)
                noise = (2 * random.random() - 1)
                bass = math.sin(2 * math.pi * (150 - 600*t) * t) if t < 0.15 else 0
                val = int(32767 * 0.8 * env * (0.6*noise + 0.4*bass))
                val = max(-32767, min(32767, val))
            self.sounds["ak_shot"] = pygame.mixer.Sound(buffer=buf)
            
        # SMG Shot - Nạp âm thanh từ file súng tiểuulieen.mp3
        smg_path = os.path.join(base_dir, "ANH", "súng tiểuulieen.mp3")
        smg_loaded = False
        if os.path.exists(smg_path):
            try:
                self.sounds["smg_shot"] = pygame.mixer.Sound(smg_path)
                smg_loaded = True
            except Exception as e:
                print("Lỗi load âm thanh SMG:", e)
        
        if not smg_loaded:
            # Fallback dùng chung tiếng với AK nếu không load được
            self.sounds["smg_shot"] = self.sounds.get("ak_shot")
        
        # Shotgun Shot - Nạp âm thanh shotgun.mp3 từ thư mục ANH
        shotgun_path = os.path.join(base_dir, "ANH", "tieng shotgun.mp3")
        shotgun_loaded = False
        if os.path.exists(shotgun_path):
            try:
                self.sounds["shotgun_shot"] = pygame.mixer.Sound(shotgun_path)
                shotgun_loaded = True
            except Exception as e:
                print("Loi load file am thanh Shotgun:", e)
                
        if not shotgun_loaded:
            # Fallback mô phỏng âm thanh shotgun nổ lớn đầy uy lực
            dur = 0.5
            buf = array.array('h')
            for i in range(int(sr * dur)):
                t = i / sr
                env = math.exp(-12 * t)
                noise = (2 * random.random() - 1)
                bass = math.sin(2 * math.pi * (100 - 300*t) * t) if t < 0.2 else 0
                val = int(32767 * 0.7 * env * (0.8*noise + 0.2*bass))
                val = max(-32767, min(32767, val))
                buf.append(val); buf.append(val)
            self.sounds["shotgun_shot"] = pygame.mixer.Sound(buffer=buf)

        # Sniper Shot
        dur = 0.3
        buf = array.array('h')
        for i in range(int(sr * dur)):
            t = i / sr
            env = math.exp(-15 * t)
            noise = (2 * random.random() - 1)
            bass = math.sin(2 * math.pi * (200 - 1500*t) * t) if t < 0.1 else 0
            val = int(32767 * 0.2 * env * (0.6*noise + 0.4*bass))
            buf.append(val); buf.append(val)
        self.sounds["sniper_shot"] = pygame.mixer.Sound(buffer=buf)
        
        # Enemy Shot
        dur = 0.1
        buf = array.array('h')
        for i in range(int(sr * dur)):
            t = i / sr
            env = math.exp(-40 * t)
            noise = (2 * random.random() - 1)
            val = int(32767 * 0.08 * env * noise)
            buf.append(val); buf.append(val)
        self.sounds["enemy_shot"] = pygame.mixer.Sound(buffer=buf)

        # Explosion
        dur = 0.8
        buf = array.array('h')
        for i in range(int(sr * dur)):
            t = i / sr
            env = math.exp(-5 * t)
            noise = (2 * random.random() - 1)
            # Rumble bass
            bass = math.sin(2 * math.pi * (50 + 10*math.sin(50*t)) * t)
            val = int(32767 * 0.25 * env * (0.6*noise + 0.4*bass))
            buf.append(val); buf.append(val)
        self.sounds["explosion"] = pygame.mixer.Sound(buffer=buf)
        
        # Step
        dur = 0.05
        buf = array.array('h')
        for i in range(int(sr * dur)):
            t = i / sr
            env = math.exp(-50 * t)
            val = int(32767 * 0.02 * env * (2 * random.random() - 1))
            buf.append(val); buf.append(val)
        self.sounds["step"] = pygame.mixer.Sound(buffer=buf)

        # Hurt / Death
        dur = 0.4
        buf = array.array('h')
        for i in range(int(sr * dur)):
            t = i / sr
            env = math.exp(-10 * t)
            freq = 300 - 400 * t
            val = int(32767 * 0.1 * env * math.sin(2 * math.pi * freq * t))
            buf.append(val); buf.append(val)
        self.sounds["death"] = pygame.mixer.Sound(buffer=buf)
        
        # Pickup
        dur = 0.2
        buf = array.array('h')
        for i in range(int(sr * dur)):
            t = i / sr
            env = math.exp(-15 * t)
            freq = 800 + 1000 * t
            val = int(32767 * 0.05 * env * math.sin(2 * math.pi * freq * t))
            buf.append(val); buf.append(val)
        self.sounds["pickup"] = pygame.mixer.Sound(buffer=buf)
        
        # Grenade Throw (Chiuuuuuuuuu)
        dur = 0.6
        buf = array.array('h')
        for i in range(int(sr * dur)):
            t = i / sr
            env = 1.0 - (t / dur)
            freq = 1500 - 1800 * t
            val = int(32767 * 0.15 * env * math.sin(2 * math.pi * freq * t))
            buf.append(val); buf.append(val)
        self.sounds["grenade_throw"] = pygame.mixer.Sound(buffer=buf)
        
        # Typewriter click / Terminal beep (Tiếng gõ phím cơ / bíp terminal)
        dur = 0.03
        buf = array.array('h')
        for i in range(int(sr * dur)):
            t = i / sr
            # Env suy hao cực nhanh tạo tiếng click đanh gọn
            env = math.exp(-120 * t)
            # Tần số quét cao từ 1600Hz đến 2000Hz tạo âm thanh bíp cơ học tinh tế
            freq = 1600 + 400 * t
            sine_wave = math.sin(2 * math.pi * freq * t)
            # Thêm tạp âm trắng (white noise) mô phỏng tiếng click phím cơ
            noise = (2 * random.random() - 1) * 0.45
            val = int(32767 * 0.28 * env * (sine_wave + noise))
            val = max(-32767, min(32767, val))
            buf.append(val); buf.append(val)
        self.sounds["typing"] = pygame.mixer.Sound(buffer=buf)
        
        # Wood break - crackling wood sound
        dur = 0.35
        buf = array.array('h')
        for i in range(int(sr * dur)):
            t = i / sr
            env = math.exp(-15 * t)
            freq = 350 - 250 * t
            wave = math.sin(2 * math.pi * freq * t)
            # simulate wood cracking by combining low freq sweep and white noise
            noise = (2 * random.random() - 1)
            val = int(32767 * 0.22 * env * (0.35 * wave + 0.65 * noise))
            val = max(-32767, min(32767, val))
            buf.append(val); buf.append(val)
        self.sounds["wood_break"] = pygame.mixer.Sound(buffer=buf)

        # Hiss - high-frequency leaking barrel hiss sound
        dur = 0.4
        buf = array.array('h')
        for i in range(int(sr * dur)):
            t = i / sr
            # oscillating envelope to sound like steam/gas spraying out
            env = (0.6 + 0.4 * math.sin(2 * math.pi * 35 * t)) * (1.0 - t/dur)
            noise = (2 * random.random() - 1)
            val = int(32767 * 0.12 * env * noise)
            val = max(-32767, min(32767, val))
            buf.append(val); buf.append(val)
        self.sounds["hiss"] = pygame.mixer.Sound(buffer=buf)
        
        # Music - Intense Jungle Beat
        dur = 2.0
        buf = array.array('h')
        for i in range(int(sr * dur)):
            t = i / sr
            
            # Kick on 0, 0.5, 1.0, 1.5
            k_t = t % 0.5
            kick = 0.15 * math.exp(-20 * k_t) * math.sin(2 * math.pi * 60 * k_t)
            
            # Hat
            h_t = t % 0.25
            hat = 0.05 * math.exp(-40 * h_t) * (2*random.random()-1) if h_t < 0.05 else 0
            
            # Bass pulse
            b_t = t % 0.25
            bass = 0.08 * math.sin(2 * math.pi * 40 * t) * (1 - b_t/0.25)
            
            val = int(32767 * max(-1.0, min(1.0, kick + hat + bass)))
            buf.append(val); buf.append(val)
        self.sounds["bgm_jungle"] = pygame.mixer.Sound(buffer=buf)

        # Siren / Alarm (Wah-wah sound)
        dur_siren = 1.0
        buf_siren = array.array('h')
        for i in range(int(sr * dur_siren)):
            t = i / sr
            # Frequency sweeps up and down between 600Hz and 1000Hz (2Hz modulation)
            freq = 800 + 200 * math.sin(2 * math.pi * 2.0 * t)
            val = int(32767 * 0.15 * math.sin(2 * math.pi * freq * t))
            buf_siren.append(val); buf_siren.append(val)
        self.sounds["siren"] = pygame.mixer.Sound(buffer=buf_siren)

    def _generate_sounds(self):
        # Generate basic procedural sounds
        self._generate_sound("menu_select", 880, 0.08, vol=0.06, wave_type="sine")
        self._generate_sound("error", 180, 0.15, vol=0.08, wave_type="saw")
        self._generate_sound("hurt", 130, 0.15, vol=0.1, wave_type="saw")
        self._generate_sound("reload", 600, 0.25, vol=0.08, wave_type="noise")
        
        # Generate complex sounds
        self._generate_complex_sound()

    def play(self, name, maxtime=0):
        if not self.enabled:
            return
        if name in self.sounds:
            self.sounds[name].set_volume(self.sfx_volume)
            if maxtime > 0:
                self.sounds[name].play(maxtime=maxtime)
            else:
                self.sounds[name].play()

    def play_loop(self, name):
        if not self.enabled:
            return None
        if name in self.sounds:
            self.sounds[name].set_volume(self.sfx_volume)
            return self.sounds[name].play(loops=-1)
        return None

    def stop_channel(self, channel):
        if not self.enabled or not channel:
            return
        try:
            channel.stop()
        except: pass

    def set_music_volume(self, volume):
        self.music_volume = max(0.0, min(1.0, volume))
        try:
            pygame.mixer.music.set_volume(self.music_volume)
        except: pass
        if self.bg_channel:
            self.bg_channel.set_volume(self.music_volume)

    def set_sfx_volume(self, volume):
        self.sfx_volume = max(0.0, min(1.0, volume))

    def play_bg_music(self, track="lobby"):
        if not self.enabled:
            return
            
        if getattr(self, "current_track", None) == track:
            return
            
        self.stop_bg_music()
        self.current_track = track
        import os
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Sảnh chờ
        if track == "lobby":
            lobby_music = os.path.join(base_dir, "ANH", "nhac sanh cho.mp3")
            if os.path.exists(lobby_music):
                try:
                    pygame.mixer.music.load(lobby_music)
                    pygame.mixer.music.set_volume(self.music_volume)
                    pygame.mixer.music.play(-1)
                    return
                except Exception as e:
                    print("Loi load nhac sanh cho:", e)
                    
        # Nhạc chiến đấu/Lớp chơi chính
        custom_music = os.path.join(base_dir, "ANH", "nhạc game.mp3")
        if not os.path.exists(custom_music):
            custom_music = os.path.join(base_dir, "ANH", "Nhac_nen.mp3")
        if not os.path.exists(custom_music):
            custom_music = os.path.join(base_dir, "ANH", "NHAC_NEN_.mp3")
            
        if os.path.exists(custom_music):
            try:
                pygame.mixer.music.load(custom_music)
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1)
                return
            except Exception as e:
                print("Loi load nhac nen chien dau:", e)
                
        if "bgm_jungle" in self.sounds:
            if self.bg_channel:
                self.bg_channel.play(self.sounds["bgm_jungle"], loops=-1)

    def stop_bg_music(self):
        if not self.enabled:
            return
        try:
            pygame.mixer.music.stop()
        except: pass
        if self.bg_channel:
            self.bg_channel.stop()
        self.current_track = None

# Global instance
sound_manager = SoundManager()
