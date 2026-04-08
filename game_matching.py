import pygame
import sys
import random

# === KONFIGURASI WARNA & LAYAR ===
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BG_COLOR = (40, 40, 60)    # Warna latar belakang
BLUE = (65, 105, 225)      # Warna kotak saat tertutup
RED = (220, 20, 60)        # Warna Player/Kursor
GREEN = (50, 205, 50)      # Warna teks menang
YELLOW = (255, 215, 0)     # Warna combo/score

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# === CLASS ===

# --- [ BASE CLASS ] ---
class GameObject(pygame.sprite.Sprite): # Pakai class bawaan Pygame untuk kemudahan manajemen objek
    def __init__(self, x, y, width, height, color):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

# --- [ SUBCLASS ] ---
# Class PlayerCursor
class PlayerCursor(GameObject):
    def __init__(self):
        # Memanggil constructor induk, membuat kotak merah kecil sebagai player
        super().__init__(0, 0, 15, 15, RED)
        self.score = 0  # Skor pemain
        self.combos = 0 # Hitungan combo berturut-turut
        self.health = 5 # Nyawa player

    def update(self):
        # Karakter player akan selalu mengikuti posisi mouse
        mouse_pos = pygame.mouse.get_pos()
        self.rect.center = mouse_pos

# Class Kotak Puzzle
class PuzzleBox(GameObject):
    def __init__(self, x, y, value, font):
        super().__init__(x, y, 100, 100, BLUE)
        self.value = value       # Angka di balik kotak
        self.font = font         # Font untuk menggambar angka
        self.state = "HIDDEN"    # Status: HIDDEN (tertutup), FLIPPED (terbuka), MATCHED (cocok/hilang)
        
        self.color_hidden = BLUE
        self.color_flipped = WHITE

    def update(self):
        if self.state == "MATCHED": # Jika kotak sudah cocok, hapus objek ini dari game (menghilang)
            self.kill()
        elif self.state == "FLIPPED": # Jika sedang dibuka, warnai putih dan tampilkan angkanya
            self.image.fill(self.color_flipped)
            pygame.draw.rect(self.image, BLACK, self.image.get_rect(), 3) # Garis tepi
            
            # Render teks angka di tengah kotak
            text_surface = self.font.render(str(self.value), True, BLACK)
            text_rect = text_surface.get_rect(center=(50, 50))
            self.image.blit(text_surface, text_rect)
        elif self.state == "HIDDEN": # Jika tertutup, kembalikan ke warna biru
            self.image.fill(self.color_hidden)
            pygame.draw.rect(self.image, WHITE, self.image.get_rect(), 2) # Garis tepi putih

# Class Button
class Button(GameObject):
    def __init__(self, x, y, width, height, text, font):
        super().__init__(x, y, width, height, WHITE)
        self.text = text
        self.font = font
        self.rect.center = (x, y)

    def draw(self, screen, mouse_pos): # Menampilkan tombol dengan efek hover
        if self.rect.collidepoint(mouse_pos):
            self.image.fill(YELLOW)
        else:
            self.image.fill(WHITE)

        # UI Tombol
        pygame.draw.rect(self.image, BLACK, self.image.get_rect(), 3)
        text_surface = self.font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        self.image.blit(text_surface, text_rect)
        screen.blit(self.image, self.rect)


# === FUNGSI UTAMA (MAIN LOOP) ===
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Memory Puzzle Match")
    clock = pygame.time.Clock()

    # Sembunyikan kursor mouse bawaan Windows/Mac, karena kita pakai PlayerCursor
    pygame.mouse.set_visible(False)

    font_number = pygame.font.SysFont("Arial", 48, bold=True)
    font_ui = pygame.font.SysFont("Arial", 24)
    font_large = pygame.font.SysFont("Arial", 64, bold=True)

    game_state = "MENU"
    btn_start = Button(SCREEN_WIDTH // 2, 400, 250, 60, "START GAME", font_ui)

    running = True

    while running:
        mouse_pos = pygame.mouse.get_pos()
        
        # === Event Handling ===
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if game_state == "MENU":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btn_start.rect.collidepoint(event.pos):
                        game_state = "PLAYING"
                        win = False
                        lose = False

                        # Grup Objek
                        all_sprites = pygame.sprite.Group()
                        boxes = pygame.sprite.Group()

                        # Membuat Karakter Utama (Player)
                        player = PlayerCursor()

                        # Menyiapkan Angka Pasangan (1 sampai 8, masing-masing 2 buah = 16 kotak)
                        box_values = [1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8]
                        random.shuffle(box_values) # Acak posisinya

                        # Membuat Grid Kotak 4x4
                        margin = 20
                        start_x = (SCREEN_WIDTH - (4 * 100 + 3 * margin)) // 2  # Posisi tengah layar 
                        start_y = 100                                           # Posisi atas layar

                        index = 0
                        for row in range(4):
                            for col in range(4):
                                x = start_x + col * (100 + margin)
                                y = start_y + row * (100 + margin)
                                
                                box = PuzzleBox(x, y, box_values[index], font_number)
                                box.state = "FLIPPED"
                                boxes.add(box)
                                all_sprites.add(box)
                                index += 1

                        # Memasukkan player terakhir agar selalu digambar di atas (paling depan)
                        all_sprites.add(player)

                        # Variabel Logika Permainan
                        flipped_boxes = [] # Menyimpan kotak yang sedang terbuka
                        wait_timer = 0     # Waktu tunggu sebelum kotak ditutup kembali jika salah

                        # kotak terbuka selama 5 detik di awal permainan
                        preview_timer = 300 # 5 detik
                        is_previewing = True

            elif game_state == "PLAYING":
                # Jika Player menekan tombol R saat sudah menang atau kalah, ulangi permainan
                if event.type == pygame.KEYDOWN and (win or lose):
                    if event.key == pygame.K_r:
                        main()
                        return

                # Jika Player melakukan Klik Kiri Mouse
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not is_previewing and wait_timer == 0 and not win:
                        for box in boxes:
                            if box.rect.collidepoint(event.pos) and box.state == "HIDDEN":
                                box.state = "FLIPPED"
                                flipped_boxes.append(box)
                                break

        # === LOGIKA PERMAINAN ===
        if game_state == "PLAYING" and not win and not lose:
            if is_previewing:
                preview_timer -= 1
                if preview_timer <= 0:
                    is_previewing = False
                    # Setelah preview selesai, tutup semua kotak yang masih terbuka
                    for box in boxes:
                        if box.state == "FLIPPED":
                            box.state = "HIDDEN"
                    flipped_boxes.clear() # Kosongkan daftar flipped_boxes setelah preview

            # Jika ada 2 kotak yang terbuka, cek apakah angkanya sama
            if len(flipped_boxes) == 2 and wait_timer == 0:
                if flipped_boxes[0].value == flipped_boxes[1].value: # Jika BENAR, tandai kedua kotak sebagai MATCHED (cocok/hilang)
                    flipped_boxes[0].state = "MATCHED"
                    flipped_boxes[1].state = "MATCHED"
                    flipped_boxes.clear() # Kosongkan daftar

                    # Hitung skor dengan bonus combo
                    base_score = 10
                    combo_bonus = player.combos * 5 
                    total_score = base_score + combo_bonus
                    player.score += total_score 
                    player.combos += 1 
                    player.health = min(player.health + 1, 5)
                else: # Jika SALAH, mulai timer tunggu untuk menutup kembali kotak
                    player.health -= 1
                    wait_timer = 45 
                    player.combos = 0
            
            # Mengurangi timer tunggu jika sedang berjalan
            if wait_timer > 0:
                wait_timer -= 1
                if wait_timer == 0:
                    # Waktu habis, tutup kembali kotak yang salah
                    for b in flipped_boxes:
                        b.state = "HIDDEN"
                    flipped_boxes.clear()

            # Update semua objek
            all_sprites.update()

            # Cek kondisi menang (semua kotak sudah menghilang / grup boxes kosong)
            if len(boxes) == 0:
                win = True

            # Jika player kehabisan nyawa
            if player.health <= 0:
                lose = True

        # === GAMBAR & RENDER ===
        screen.fill(BG_COLOR)
        if game_state == "MENU":
            title_text = font_large.render("MEMORY PUZZLE MATCH", True, WHITE)
            screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 150))
            btn_start.draw(screen, mouse_pos)
            pygame.draw.rect(screen, RED, (mouse_pos[0]-7, mouse_pos[1]-7, 15, 15)) # Gambar kursor merah di posisi mouse
        elif game_state == "PLAYING":
            all_sprites.draw(screen) # Menggambar semua objek (Kotak dan Player)

            # UI Teks
            if player.combos > 0:
                warna_skor = YELLOW
            else:
                warna_skor = WHITE

            score_text = font_ui.render(f"Skor: {player.score}", True, warna_skor)
            screen.blit(score_text, (20, 20))

            if player.combos > 0:
                combo_text = font_ui.render(f"Combo x{player.combos}!", True, YELLOW)
                screen.blit(combo_text, (20, 80))

            health_text = font_ui.render(f"Nyawa: {player.health}", True, WHITE)
            screen.blit(health_text, (20, 50))
            
            inst_text = font_ui.render("Klik 2 kotak untuk mencari angka yang sama!", True, WHITE)
            screen.blit(inst_text, (SCREEN_WIDTH - inst_text.get_width() - 20, 20))

            # === Tampilan Akhir Permainan (Menang/Kalah) ===
            if lose:
                win_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                win_bg.set_alpha(180)
                win_bg.fill(BLACK)
                screen.blit(win_bg, (0, 0))

                lose_text = font_large.render("KAMU KALAH!", True, RED)
                screen.blit(lose_text, (SCREEN_WIDTH // 2 - lose_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
                restart_text = font_ui.render("Tekan 'R' untuk Coba Lagi", True, WHITE)
                screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 30))

            if win:
                win_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                win_bg.set_alpha(180)
                win_bg.fill(BLACK)
                screen.blit(win_bg, (0, 0))

                win_text = font_large.render("KAMU BERHASIL!", True, GREEN)
                screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
                
                restart_text = font_ui.render("Tekan 'R' untuk Main Lagi", True, WHITE)
                screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 30))

        pygame.display.flip()
        clock.tick(60) # Batasi 60 FPS

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()