import math
import os
import random
import sys
import time
import pygame as pg


# 【条件】実行ファイルのあるディレクトリをカレントディレクトリに設定
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 定数設定
WIDTH = 800
HEIGHT = 600
GROUND_Y = 500

# 色定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
SKY = (120, 200, 255)
YELLOW = (255, 220, 0)
GREEN = (0, 200, 0)
BROWN = (120, 80, 40)
GAUGE_COLOR = (255, 165, 0)

def check_bound_horizontal(obj_rct: pg.Rect) -> bool:
    """
    オブジェクトが画面の左端より外に出たかを判定する
    """
    if obj_rct.right < 0:
        return True
    return False

class Bird(pg.sprite.Sprite):
    """
    プレイヤー（キャラクター）に関するクラス
    """
    def __init__(self, xy: tuple[int, int]):
        super().__init__()
        
        # キャラクター画像の読み込みとサイズ調整
        self.img_run = pg.transform.scale(pg.image.load("fig/2.png").convert_alpha(), (60, 80))   # 動いている時
        self.img_jump = pg.transform.scale(pg.image.load("fig/6.png").convert_alpha(), (60, 80))  # ジャンプ時
        self.img_crouch = pg.transform.scale(pg.image.load("fig/4.png").convert_alpha(), (60, 30))  # しゃがんでいる時
         # 無敵画像
        self.img_invincible = pg.transform.scale(pg.image.load("fig/Gemini_Generated_Image_5cmamr5cmamr5cma.png").convert_alpha(),(80, 80))
        
        # ジャンプ時の効果音を読み込む
        self.se_jump = pg.mixer.Sound("fig/sound/junp.wav")

        self.image = self.img_run
        self.rect = self.image.get_rect()
        self.rect.center = xy
        
        self.y_speed = 0
        self.on_ground = True
        self.jump_force = -18
        self.gravity = 1
        self.double_jump_stock = 0
        self.has_double_jumped = False # すでに空中で2段目を使ったか
        self.invincible = 0  # 無敵時間
        self.hit_cooldown = 0  # ← 追加



    def update(self, key_lst: list[bool] = None, invincible=False):

        if key_lst is None:
            key_lst = pg.key.get_pressed()

        # しゃがみ入力の判定
        is_crouching = key_lst[pg.K_DOWN] and self.on_ground

        # 無敵時画像
        if invincible:
            center = self.rect.center
            self.image = self.img_invincible
            self.rect = self.image.get_rect()
            self.rect.center = center

        else:
            old_bottom = self.rect.bottom
            old_centerx = self.rect.centerx
            if is_crouching:
                self.image = self.img_crouch
            elif self.on_ground:
                self.image = self.img_run
            else:
                self.image = self.img_jump
            self.rect = self.image.get_rect()
            if is_crouching:
                self.rect.bottom = old_bottom
                self.rect.centerx = old_centerx
            else:
                # 通常時やジャンプ時は中心基準で座標を設定
                self.rect.center = (old_centerx, old_bottom - self.rect.height // 2)
        # 重力
        self.y_speed += self.gravity
        self.rect.y += self.y_speed

        # 地面判定
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.y_speed = 0
            self.on_ground = True
            self.has_double_jumped = False
        else:
            self.on_ground = False

        if self.hit_cooldown > 0:
            self.hit_cooldown -= 1

    def jump(self):

        # 1段目ジャンプ
        if self.on_ground:
            # ジャンプ時に効果音を鳴らす
            self.se_jump.play()
            self.y_speed = self.jump_force
            self.on_ground = False
        
            return False
        
        # 2段目ジャンプ（条件：ゲージ満タンかつ、まだ空中ジャンプしていない）
        elif self.double_jump_stock > 0 and not self.has_double_jumped:
            self.y_speed = self.jump_force
            self.has_double_jumped = True
            self.double_jump_stock -= 1
            return True # 2段ジャンプ成功を通知
        return False

class Obstacle(pg.sprite.Sprite):
    """
    障害物（ジャンプで避けられる赤い矩形）に関するクラス
    """
    def __init__(self, speed):
        super().__init__()
        self.fire = pg.image.load("fig/fire.png").convert_alpha()
        height = random.randint(55, 80)
        self.image = pg.transform.scale(self.fire, (60, height))
        self.rect = self.image.get_rect()
        self.rect.left = WIDTH
        self.rect.bottom = GROUND_Y
        self.speed = speed

    def update(self):
        self.rect.x -= self.speed
        if check_bound_horizontal(self.rect):
            self.kill()

class Helfobstacle(pg.sprite.Sprite):
    """
    障害物（しゃがみで避けられる青い矩形）に関するクラス
    """
    def __init__(self, speed):
        super().__init__()
        self.wall = pg.image.load("fig/wall.jpg").convert_alpha()
        self.image = pg.transform.scale(self.wall, (50, HEIGHT))
        self.rect = self.image.get_rect()
        self.rect.left = WIDTH
        self.rect.bottom = GROUND_Y - 50
        self.speed = speed

    def update(self):
        self.rect.x -= self.speed
        if check_bound_horizontal(self.rect):
            self.kill()

class Coin(pg.sprite.Sprite):
    """
    コイン（画像）に関するクラス
    """
    def __init__(self, speed, coin_img):
        super().__init__()
        self.image = coin_img
        self.rect = self.image.get_rect()
        self.rect.left = WIDTH
        self.rect.top = random.randint(300, 430)
        self.speed = speed

    def update(self):
        self.rect.x -= self.speed
        if check_bound_horizontal(self.rect):
            self.kill()


class Star(pg.sprite.Sprite):
    def __init__(self, speed):
        super().__init__()

        self.image = pg.Surface((40, 40), pg.SRCALPHA)

        pg.draw.polygon(
            self.image,
            YELLOW,
            [
                (20, 0), (25, 15), (39, 15),
                (28, 24), (32, 39),
                (20, 30), (8, 39),
                (12, 24), (1, 15),
                (15, 15)
            ]
        )

        self.rect = self.image.get_rect()

        self.rect.left = WIDTH + random.randint(0, 200)
        self.rect.bottom = random.randint(200, 450)

        self.x_speed = -10
        self.y_speed = 10
        self.gravity = 0.5

    def update(self):
        self.rect.x += self.x_speed

        self.y_speed += self.gravity
        self.rect.y += self.y_speed

        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.y_speed = -10

        if self.rect.right < 0:
            self.kill()


class Score:
    """
    スコアとコイン数を表示するクラス
    """
    def __init__(self):
        self.font = pg.font.SysFont(None, 40)
        self.score_value = 0
        self.coin_value = 0

    def update(self, screen: pg.Surface):
        score_img = self.font.render(f"Score : {self.score_value}", True, WHITE)
        coin_img = self.font.render(f"Coins : {self.coin_value}", True, WHITE)
        screen.blit(score_img, (20, 20))
        screen.blit(coin_img, (20, 60))

def draw_text_with_shadow(screen, text, font, text_color, shadow_color, x, y):
    """文字に影をつけて見やすく描画する補助関数"""
    shadow = font.render(text, True, shadow_color)
    main_text = font.render(text, True, text_color)
    screen.blit(shadow, (x + 3, y + 3)) # 影を右下にずらす
    screen.blit(main_text, (x, y))

class Life:
    """
    ライフ数を表示するクラス
    """
    def __init__(self, num: int):
        self.num = num

    def update(self, screen: pg.Surface):
        font = pg.font.SysFont(None, 40)
        life_img = font.render(f"Life : {self.num}", True, WHITE)
        screen.blit(life_img, (20, 100))

class Beam(pg.sprite.Sprite):
    """
    障害物を破壊する弾
    """
    def __init__(self, x, y):
        super().__init__()
        self.image = pg.Surface((20, 6))
        self.image.fill((255, 255, 0))  # 黄色い弾
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 15

    def update(self):
        self.rect.x += self.speed
        if self.rect.left > WIDTH:
            self.kill()


def main():
    pg.display.set_caption("Kokaton Run")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()
    
    # --- 画像の読み込みと準備 ---
    
    # 1. 通常背景 (back_graund.jpg)
    bg_img = pg.image.load("fig/back_graund.jpg").convert()
    bg_w = int(bg_img.get_width() * (HEIGHT / bg_img.get_height()))
    bg_img = pg.transform.scale(bg_img, (bg_w, HEIGHT))
    # 元の暗いオーバーレイ（通常背景用）
    dark_overlay = pg.Surface((bg_w, HEIGHT), pg.SRCALPHA)
    dark_overlay.fill((0, 0, 0, 120)) 
    bg_img.blit(dark_overlay, (0, 0))
    
    # 2. ゲームオーバー用背景 (died_kokaton.png) 
    bg_img_go = pg.transform.scale(pg.image.load("fig/died_kokaton.png").convert_alpha(), (WIDTH, HEIGHT))
    
    # --- 変更: ゲームオーバー背景を少し明るくするためにアルファ値を 150 から 80 に変更 ---
    bg_img_go_overlay = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
    bg_img_go_overlay.fill((0, 0, 0, 80))  # 80に下げることで背景画像をより明るくはっきり見せます
    bg_img_go.blit(bg_img_go_overlay, (0, 0))
    # ---------------------------------------------------------------------------------

    # 地面画像の読み込みとサイズ調整
    ground_tile = pg.image.load("fig/jimen.jpg").convert()
    ground_size = HEIGHT - GROUND_Y
    ground_tile = pg.transform.scale(ground_tile, (ground_size, ground_size))
    
    raw_coin_img = pg.image.load("fig/coin.png").convert_alpha()
    coin_img = pg.transform.scale(raw_coin_img, (35, 35))

    # 効果音を読み込む
    se_coin = pg.mixer.Sound("fig/sound/coin_get.wav")
    se_gameover = pg.mixer.Sound("fig/sound/game_over.mp3")

    # スタート画面用のBGMを読み込んでループ再生
    pg.mixer.music.load("fig/sound/start_bgm.mp3")
    pg.mixer.music.play(-1) 

    bird = Bird((150, GROUND_Y - 40))
    obstacles = pg.sprite.Group()
    coins = pg.sprite.Group()
    beams = pg.sprite.Group()
    score = Score()

    stars = pg.sprite.Group()

    # 無敵関連
    invincible = False
    invincible_start = 0

    is_started = False
    life = Life(3)
    game_over = False
    tmr = 0
    charge_start_tmr = 0 # 2段ジャンプ使用後のリセット用基準点

    title_font = pg.font.SysFont(None, 100)
    msg_font = pg.font.SysFont(None, 50)
    
    go_title_font = pg.font.SysFont(None, 120)  
    go_score_font = pg.font.SysFont(None,  60)   

    while True:
        key_lst = pg.key.get_pressed()

        # 現在のチャージ量計算 (0〜600)
        charge = tmr - charge_start_tmr
        if charge >= 600:
            bird.double_jump_stock += 1
            charge_start_tmr += 600 # 溢れた分を次のチャージへ引き継ぐ
            charge_current = tmr - charge_start_tmr # 更新
        else:
            bird.double_jump_ready = False
        
        # イベント処理
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE and not game_over:
                    bird.jump()
                if event.key == pg.K_r and game_over:
                    # ゲームのリセット（mainを再帰呼び出しせず変数を初期化）
                    main()
                    return
                if event.key == pg.K_l and score.coin_value >= 20 and not game_over:
                    score.coin_value -= 20
                    life.num += 1 #Lキーでライフ回復
                if event.key == pg.K_b and score.coin_value >= 10 and not game_over:
                    score.coin_value -= 10
                    beams.add(Beam(bird.rect.right, bird.rect.centery))#Bキーで弾発射


                if not is_started:
                    if event.key == pg.K_SPACE:
                        is_started = True
                        pg.mixer.music.stop() 
                        pg.mixer.music.load("fig/sound/game_bgm.mp3") 
                        pg.mixer.music.play(-1) 
                elif game_over:
                    if event.key == pg.K_r:
                        main()
                        return
        
        

        # プレイ中の更新処理
        if is_started and not game_over:
            current_speed = 8 + score.score_value // 10

            if tmr % 60 == 0:
                ob_type = random.randint(0,100)
                if 0 <= ob_type <= 50:
                    obstacles.add(Obstacle(current_speed))
                elif 51 <= ob_type <= 100:
                    obstacles.add(Helfobstacle(current_speed))

            if tmr % 80 == 0:
                coins.add(Coin(current_speed, coin_img))

                        # スター生成
            if tmr % 1000 == 0:
                stars.add(Star(current_speed))

            bird.update(pg.key.get_pressed(), invincible)
            obstacles.update()
            coins.update()
            stars.update()
            beams.update()

            for coin in pg.sprite.spritecollide(bird, coins, True):
                se_coin.play()
                score.coin_value += 1

            # スター取得
            if pg.sprite.spritecollide(bird, stars, True):
                invincible = True
                invincible_start = time.time()

            # 無敵時間終了
            if invincible and time.time() - invincible_start >= 10:
                invincible = False                

            if not invincible:
                if pg.sprite.spritecollide(bird, obstacles, False):
                    if life.num <= 0:
                        game_over = True
                        pg.mixer.music.stop()
                        se_gameover.play()
            
            # 衝突判定：障害物（当たったらゲームオーバー）
            for obstacle in pg.sprite.spritecollide(bird, obstacles, False):
                if not invincible and bird.hit_cooldown == 0:
                    life.num -= 1
                    bird.hit_cooldown = 30  # ← 30フレーム無敵


                else:
                    pass  # 無敵時間中は何もしない
                if life.num <= 0:         # ライフが0ならゲームオーバー
                     game_over = True
                     pg.mixer.music.stop()
                     se_gameover.play()

            # 弾と障害物の衝突
            for beam in beams:
                hit_list = pg.sprite.spritecollide(beam, obstacles, True)
                if hit_list:
                    beam.kill()

            # 通過判定（画面外に消えた障害物をスコアに加算）
            for obstacle in obstacles:
                if obstacle.rect.x < -10 and not hasattr(obstacle, "scored"):
                    score.score_value += 1
                    obstacle.scored = True # 重複加算防止フラグ

        # ==================================
        # 描画処理
        # ==================================
        
        # 描画
        screen.fill(SKY) # 背景（空のみ、雲なし）

        # 地面
        pg.draw.rect(screen, GREEN, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pg.draw.rect(screen, BROWN, (0, GROUND_Y, WIDTH, 10))

        # 【削除】ここに雲の描画処理がありましたが、削除しました

        # 各オブジェクト描画
        obstacles.draw(screen)
        coins.draw(screen)
        beams.draw(screen)
        screen.blit(bird.image, bird.rect)
        score.update(screen)
        life.update(screen)

        if game_over:
            # ゲームオーバー時は他のオブジェクトの描画を一切行わない
            # 1. 明るめに調整された「died_kokaton.png」の背景を一番前に描画
            screen.blit(bg_img_go, (0, 0))
            
            # 2. その上からゲームオーバー関連の文字を重ねる
            over_str = "GAME OVER"
            score_str = f"Final Score : {score.score_value}"
            coin_str = f"Coins : {score.coin_value}"
            retry_str = "Press R to Retry"
            
            over_w = go_title_font.size(over_str)[0]
            score_w = go_score_font.size(score_str)[0]
            coin_w = go_score_font.size(coin_str)[0]
            retry_w = msg_font.size(retry_str)[0]
            
            draw_text_with_shadow(screen, over_str, go_title_font, RED, BLACK, WIDTH//2 - over_w//2, HEIGHT//2 - 120)
            draw_text_with_shadow(screen, score_str, go_score_font, YELLOW, BLACK, WIDTH//2 - score_w//2, HEIGHT//2 - 10)
            draw_text_with_shadow(screen, coin_str, go_score_font, YELLOW, BLACK, WIDTH//2 - coin_w//2, HEIGHT//2 + 50)
            draw_text_with_shadow(screen, retry_str, msg_font, WHITE, BLACK, WIDTH//2 - retry_w//2, HEIGHT//2 + 130)
            
        else:
            # 通常時 (プレイ中またはスタート画面) の描画
            # 背景のスクロール描画
            bg_scroll_x = tmr % bg_w 
            screen.blit(bg_img, (-bg_scroll_x, 0))
            if bg_w - bg_scroll_x < WIDTH:
                screen.blit(bg_img, (bg_w - bg_scroll_x, 0))

            # 地面のスクロール描画
            current_speed = 8 + score.score_value // 10 if is_started else 8
            ground_scroll_x = (tmr * current_speed) % ground_size
            for x in range(-ground_size, WIDTH + ground_size, ground_size):
                screen.blit(ground_tile, (x - ground_scroll_x, GROUND_Y))
            # --- 2段ジャンプゲージの描画 (6段階) ---
            if is_started:
                pg.draw.rect(screen, WHITE, (580, 25, 205, 35), 2) # 外枠
                num_blocks = charge // 100 # 600 / 6 = 100 ごとに1ブロック
                for i in range(num_blocks):
                    pg.draw.rect(screen, GAUGE_COLOR, (585 + i*32, 30, 28, 25))

                stock_font = pg.font.SysFont(None, 36)
                stock_txt = stock_font.render(f"DOUBLE JUMP: {bird.double_jump_stock}", True, RED if bird.double_jump_stock > 0 else WHITE)
                screen.blit(stock_txt, (580, 65))            
                coins.draw(screen)
                stars.draw(screen)
                beams.draw(screen)
            # ゲーム中のオブジェクト描画
            obstacles.draw(screen)
            screen.blit(bird.image, bird.rect) 
            
            # スタート画面の文字描画
            if not is_started:
                title_str = "KOKATON RUN"
                start_str = "Press SPACE to Start"
                title_w = title_font.size(title_str)[0]
                start_w = msg_font.size(start_str)[0]
                draw_text_with_shadow(screen, title_str, title_font, YELLOW, BLACK, WIDTH//2 - title_w//2, HEIGHT//2 - 80)
                draw_text_with_shadow(screen, start_str, msg_font, WHITE, BLACK, WIDTH//2 - start_w//2, HEIGHT//2 + 20)
            else:
                # プレイ中のスコア表示
                score.update(screen)
                life.update(screen)

        pg.display.update()
        if is_started and not game_over:
            tmr += 1
        clock.tick(60)

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()