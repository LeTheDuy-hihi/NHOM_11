import pygame
import sys
import os

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

def play_video(screen, video_path):
    if not os.path.exists(video_path):
        return

    if not CV2_AVAILABLE:
        print("Error: OpenCV (cv2) is not installed. Cannot play video.")
        return

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return

    # Check for accompanying audio file (extracted from MP4)
    audio_path = video_path.rsplit('.', 1)[0] + ".mp3"
    has_audio = os.path.exists(audio_path)
    
    if has_audio:
        try:
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
        except:
            has_audio = False

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0: fps = 30
    
    pygame.event.pump()
    clock = pygame.time.Clock()

    playing = True
    while playing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if has_audio: pygame.mixer.music.stop()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_RETURN]:
                    playing = False

        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert frame to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize to full screen size (Stretch to fill)
        sw, sh = screen.get_size()
        frame = cv2.resize(frame, (sw, sh))
        frame = frame.copy()
        
        # Create Pygame surface
        frame_surface = pygame.image.frombuffer(frame.data, (sw, sh), 'RGB')

        screen.blit(frame_surface, (0, 0))

        # Draw "Press ENTER to skip" prompt
        font_skip = pygame.font.SysFont("segoeui", 20, bold=True)
        skip_txt = font_skip.render("Nhấn ENTER để bỏ qua", True, (200, 200, 200))
        skip_txt.set_alpha(150)
        screen.blit(skip_txt, (sw - skip_txt.get_width() - 20, sh - skip_txt.get_height() - 20))
        
        pygame.display.update()
        
        clock.tick(fps)

    if has_audio:
        pygame.mixer.music.stop()
    cap.release()
