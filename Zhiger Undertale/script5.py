import pygame
import random

pygame.init()
pygame.mixer.init()

try:
    pygame.mixer.music.load("battle_theme.mp3")
    pygame.mixer.music.set_volume(0.5)
    music_loaded = True
except pygame.error:
    print("Аудиофайл battle_theme.mp3 не найден! Игра будет без звука.")
    music_loaded = False

screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Конкурсный проект: Битва со мной")
clock = pygame.time.Clock()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
ORANGE = (255, 127, 39)
YELLOW = (255, 255, 0)
GRAY = (100, 100, 100)

font = pygame.font.Font(None, 32)

try:
    boss_img = pygame.image.load("boss.png").convert_alpha()
    boss_talk_img = pygame.image.load("boss_talk.png").convert_alpha()
    heart_img = pygame.image.load("heart.jpg").convert_alpha()
    bullet_img = pygame.image.load("bullet.png").convert_alpha()

    boss_sprite = pygame.transform.scale(boss_img, (80, 100))
    boss_talk_sprite = pygame.transform.scale(boss_talk_img, (80, 100))
    heart_sprite = pygame.transform.scale(heart_img, (16, 16))
    has_textures = True
except pygame.error:
    print("Текстуры не найдены! Используются стандартные фигуры.")
    has_textures = False


class Heart:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 16, 16)
        self.speed = 4
        self.vel_y = 0
        self.gravity = 0.15
        self.jump_force = -5.0
        self.is_on_ground = False

    def handle_movement(self, keys, box_rect):
        if keys[pygame.K_LEFT] and self.rect.left > box_rect.left + 5:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < box_rect.right - 5:
            self.rect.x += self.speed

        if keys[pygame.K_UP] and self.is_on_ground:
            self.vel_y = self.jump_force
            self.is_on_ground = False

        self.vel_y += self.gravity
        self.rect.y += self.vel_y

        if self.rect.bottom >= box_rect.bottom - 5:
            self.rect.bottom = box_rect.bottom - 5
            self.vel_y = 0
            self.is_on_ground = True

        if self.rect.top <= box_rect.top + 5:
            self.rect.top = box_rect.top + 5
            self.vel_y = 0


class Obstacle:
    def __init__(self, rect, vx, vy, obs_type):
        self.rect = rect
        self.vx = vx
        self.vy = vy
        self.type = obs_type

    def update(self, box_rect):
        self.rect.x += self.vx
        self.rect.y += self.vy

        if self.type == "line" and self.vx > 0 and self.rect.left > box_rect.right: self.rect.right = box_rect.left
        if self.type == "line" and self.vx < 0 and self.rect.right < box_rect.left: self.rect.left = box_rect.right
        if self.type in ["rain", "block"] and self.rect.top > box_rect.bottom: self.rect.bottom = box_rect.top
        if self.type == "bar" and self.rect.bottom < box_rect.top: self.rect.top = box_rect.bottom
        if self.type == "run" and self.rect.right < box_rect.left: self.rect.left = box_rect.right

        if self.type == "bounce":
            if self.rect.left <= box_rect.left or self.rect.right >= box_rect.right: self.vx *= -1
            if self.rect.top <= box_rect.top or self.rect.bottom >= box_rect.bottom: self.vy *= -1


class Game:
    def __init__(self):
        self.state = 'DIALOG'
        self.player_hp = 12
        self.boss_hp = 10
        self.box_rect = pygame.Rect(150, 170, 640, 130)
        self.heart = Heart(390, 380)
        self.obstacles = []

        self.is_invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 2000
        self.attack_start_time = 0
        self.attack_duration = 6000

        self.current_question_idx = 0
        self.dialog_text = "Нажми ENTER"
        self.show_answer = False

        self.questions = [
            {"q": "1. Привет! Раскажи о себе",
             "a": "Привет! Меня зовут Жігер, мне 15 лет, учусь в 9 классе. Я создаю игры и изучаю разработку."},
            {"q": "2. Твоя цель?",
             "a": "Стать профессиональным разработчиком программного обеспечения и создавать крупные проекты в IT."},
            {"q": "3. Как ты пришёл в IT?",
             "a": "Всё началось с увлечения играми, мне стало безумно интересно узнать, как они устроены изнутри."},
            {"q": "4. Твой ментор?",
             "a": "Мой преподаватель Арыстан тичер на Getcourse, который направляет меня и помогает разбираться со сложной логикой."},
            {"q": "5. Точка А -> Точка Б",
             "a": "В начале пути я знал только базовые переменные, а сейчас пишу полноценные игры с физикой на Pygame."},
            {"q": "6. Хобби и интересы?",
             "a": "Помимо программирования, я увлекаюсь уличным воркаутом на турниках и брусьях, а также люблю играть в Minecraft."},
            {"q": "8. Ссылка на GitHub",
             "a": "Весь исходный код моих проектов и этой игры загружен в репозиторий на моём GitHub: github.com/zhiger-dev"},
            {"q": "7. Твой лучшие работы?",
             "a": "Я разработал игры Понг, улучшенного Динозаврика, а теперь — эту боевую систему в стиле Undertale!"},
            {"q": "8. Можеш показать?",
             "a": "Конечно!"}
        ]

    def setup_attack(self, wave):
        obs_list = []

        if wave == 10:
            obs_list.append(Obstacle(pygame.Rect(100, 390, 30, 25), 3.5, 0, "line"))
            obs_list.append(Obstacle(pygame.Rect(-100, 390, 30, 25), 3.5, 0, "line"))

        elif wave == 9:
            obs_list.append(Obstacle(pygame.Rect(100, 390, 25, 25), 4, 0, "line"))
            obs_list.append(Obstacle(pygame.Rect(-40, 390, 25, 25), 4, 0, "line"))

        elif wave == 8:
            obs_list.append(Obstacle(pygame.Rect(100, 225, 30, 110), 4.5, 0, "line"))
            obs_list.append(Obstacle(pygame.Rect(-50, 225, 30, 110), 4.5, 0, "line"))
            obs_list.append(Obstacle(pygame.Rect(700, 375, 30, 50), -4.5, 0, "line"))
            obs_list.append(Obstacle(pygame.Rect(850, 375, 30, 50), -4.5, 0, "line"))

        elif wave == 7:
            obs_list.append(Obstacle(pygame.Rect(100, 390, 30, 25), 4, 0, "line"))
            obs_list.append(Obstacle(pygame.Rect(-150, 225, 30, 130), 4, 0, "line"))

        elif wave == 6:
            obs_list.append(Obstacle(pygame.Rect(100, 360, 25, 55), 4, 0, "line"))
            obs_list.append(Obstacle(pygame.Rect(-120, 360, 25, 55), 4, 0, "line"))
            obs_list.append(Obstacle(pygame.Rect(700, 300, 90, 15), -4.5, 0, "line"))
            obs_list.append(Obstacle(pygame.Rect(950, 260, 90, 15), -4.5, 0, "line"))

        elif wave == 5:
            obs_list.append(Obstacle(pygame.Rect(260, 230, 20, 20), 4, 3, "bounce"))
            obs_list.append(Obstacle(pygame.Rect(510, 350, 20, 20), -4, -3, "bounce"))

        elif wave == 4:
            obs_list.append(Obstacle(pygame.Rect(250, 480, 140, 15), 0, -3, "bar"))
            obs_list.append(Obstacle(pygame.Rect(410, 600, 140, 15), 0, -3, "bar"))

        elif wave == 3:
            obs_list.append(Obstacle(pygame.Rect(100, 390, 30, 25), 4.5, 0, "line"))
            obs_list.append(Obstacle(pygame.Rect(700, 230, 30, 120), -4.5, 0, "line"))

        elif wave == 2:
            obs_list.append(Obstacle(pygame.Rect(600, 385, 20, 30), -6.5, 0, "run"))
            obs_list.append(Obstacle(pygame.Rect(850, 385, 25, 30), -6.5, 0, "run"))
            obs_list.append(Obstacle(pygame.Rect(1100, 385, 20, 30), -6.5, 0, "run"))

        elif wave == 1:
            obs_list.append(Obstacle(pygame.Rect(100, 365, 30, 50), 4, 0, "line"))
            obs_list.append(Obstacle(pygame.Rect(-150, 365, 30, 50), 4, 0, "line"))
            obs_list.append(Obstacle(pygame.Rect(280, 100, 40, 40), 0, 4.5, "block"))
            obs_list.append(Obstacle(pygame.Rect(380, 40, 25, 25), 0, 6.5, "block"))
            obs_list.append(Obstacle(pygame.Rect(480, -20, 35, 35), 0, 5.0, "block"))

        return obs_list

    def draw_multiline_text(self, text, color):
        words = text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if font.size(test_line)[0] < self.box_rect.width - 40:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)

        y = self.box_rect.y + 20
        for line in lines:
            rendered_text = font.render(line.strip(), True, color)
            screen.blit(rendered_text, (self.box_rect.x + 20, y))
            y += 30

    def update(self, current_time):
        if self.is_invincible and current_time - self.invincible_timer > self.invincible_duration:
            self.is_invincible = False

        if self.state == 'BOSS_ATTACK':
            if current_time - self.attack_start_time > self.attack_duration:
                self.state = 'PLAYER_TURN'

            keys = pygame.key.get_pressed()
            self.heart.handle_movement(keys, self.box_rect)

            for obs in self.obstacles:
                obs.update(self.box_rect)
                if self.heart.rect.colliderect(obs.rect) and not self.is_invincible:
                    self.player_hp -= 1
                    self.is_invincible = True
                    self.invincible_timer = current_time
                    if self.player_hp <= 0:
                        self.state = 'GAME_OVER'
                        if music_loaded:
                            pygame.mixer.music.stop()

    def handle_input(self, event, current_time):
        if event.type == pygame.KEYDOWN:
            if self.state == 'DIALOG':
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    if not self.show_answer:
                        self.dialog_text = self.questions[self.current_question_idx]["a"]
                        self.show_answer = True
                    else:
                        if self.current_question_idx == len(self.questions) - 1:
                            self.state = 'BOSS_ATTACK'
                            self.box_rect = pygame.Rect(250, 220, 300, 200)
                            self.attack_start_time = current_time
                            self.obstacles = self.setup_attack(self.boss_hp)
                            self.heart.rect.bottom = self.box_rect.bottom - 5
                            self.heart.vel_y = 0
                            if music_loaded:
                                pygame.mixer.music.play(-1)
                        else:
                            self.current_question_idx += 1
                            self.dialog_text = "Жми ENTER"
                            self.show_answer = False

            elif self.state == 'PLAYER_TURN':
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    self.boss_hp -= 1
                    if self.boss_hp <= 0:
                        self.state = 'WIN'
                        if music_loaded:
                            pygame.mixer.music.stop()
                    else:
                        self.state = 'BOSS_ATTACK'
                        self.box_rect = pygame.Rect(250, 220, 300, 200)
                        self.attack_start_time = current_time
                        self.obstacles = self.setup_attack(self.boss_hp)
                        self.heart.rect.bottom = self.box_rect.bottom - 5
                        self.heart.vel_y = 0

    def render(self, current_time):
        if self.state == 'DIALOG':
            self.box_rect = pygame.Rect(80, 170, 640, 130)

            if has_textures:
                screen.blit(boss_talk_sprite, (360, 50))
            else:
                pygame.draw.rect(screen, WHITE, (360, 50, 80, 100), 2)

            pygame.draw.polygon(screen, WHITE, [(360, 100), (340, 110), (360, 120)])
            pygame.draw.rect(screen, WHITE, self.box_rect, 3)

            self.draw_multiline_text(self.dialog_text, WHITE)

            if not self.show_answer:
                q_text = font.render(self.questions[self.current_question_idx]["q"], True, YELLOW)
                screen.blit(q_text, (80, 330))
            else:
                inst_text = font.render("[Нажми ENTER, чтобы продолжить дальше]", True, ORANGE)
                screen.blit(inst_text, (80, 330))

        elif self.state == 'BOSS_ATTACK':
            if has_textures:
                screen.blit(boss_sprite, (360, 50))
            else:
                pygame.draw.rect(screen, WHITE, (360, 50, 80, 100), 2)

            pygame.draw.rect(screen, WHITE, self.box_rect, 5)

            for obs in self.obstacles:
                if has_textures:
                    scaled_bullet = pygame.transform.scale(bullet_img, (obs.rect.width, obs.rect.height))
                    screen.blit(scaled_bullet, (obs.rect.x, obs.rect.y))
                else:
                    pygame.draw.rect(screen, WHITE, obs.rect)

            if not self.is_invincible or (current_time // 120) % 2 == 0:
                if has_textures:
                    screen.blit(heart_sprite, (self.heart.rect.x, self.heart.rect.y))
                else:
                    pygame.draw.rect(screen, RED, self.heart.rect)

        elif self.state == 'PLAYER_TURN':
            self.box_rect = pygame.Rect(250, 220, 300, 200)
            if has_textures:
                screen.blit(boss_sprite, (360, 50))
            else:
                pygame.draw.rect(screen, WHITE, (360, 50, 80, 100), 2)

            pygame.draw.rect(screen, WHITE, self.box_rect, 5)
            turn_text = font.render("ТВОЙ ХОД! НАЖМИ ENTER", True, YELLOW)
            screen.blit(turn_text, (260, 310))

        if self.state in ['BOSS_ATTACK', 'PLAYER_TURN']:
            hp_text = font.render(f"ВАШЕ HP: {self.player_hp}/12   |   HP БОССА: {self.boss_hp}/10", True, WHITE)
            screen.blit(hp_text, (220, 450))

            btn_rect = pygame.Rect(330, 490, 140, 45)
            btn_color = ORANGE if self.state == 'PLAYER_TURN' else GRAY
            pygame.draw.rect(screen, btn_color, btn_rect, 3)
            btn_label = font.render("АТАКА", True, btn_color)
            screen.blit(btn_label, (365, 502))

            wave_label = font.render(f"АТАКА БОССА: {11 - self.boss_hp} / 10", True, GRAY)
            screen.blit(wave_label, (20, 20))

        elif self.state == 'GAME_OVER':
            go_text = font.render("GAME OVER", True, RED)
            screen.blit(go_text, (250, 280))

        elif self.state == 'WIN':
            win_text = font.render("ПОБЕДА! Ты прошел мою игру!", True, YELLOW)
            screen.blit(win_text, (220, 280))


game = Game()
running = True

while running:
    current_time = pygame.time.get_ticks()
    clock.tick(60)
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        game.handle_input(event, current_time)

    game.update(current_time)
    game.render(current_time)

    pygame.display.flip()

pygame.quit()