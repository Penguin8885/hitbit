# -*- coding: utf-8 -*-

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import sys
import numpy as np

class Car:
    id_counter = 500

    def __init__(self, torque, max_speed, rotation, mass, bounce, size, color):
        self.id = Car.id_counter    # 車の番号
        self.torque = torque        # 加速トルク [N]
        self.max_speed = max_speed  # 最高速度 [m/s]
        self.rotation = rotation    # 旋回速度 [rad/s]
        self.mass = mass            # 質量 [kg]
        self.bounce = bounce        # 疑似反発係数
        self.size = size            # 車両サイズ [m]
        self.color = color          # 車両色

        # 描画設定リストのためのidカウンターをインクリメント
        Car.id_counter += 1
        if Car.id_counter >= 600:
            print('Error : Class Car -> id_counter overflows')
            sys.exit(1)

        # 描画設定リストを設定
        glNewList(int(self.id), GL_COMPILE)  # 画面描画リストの登録開始
        glColor3f(self.color[0], self.color[1], self.color[2])  # 色を設定
        glPushMatrix()                  # 前の設定行列をスタックして退避
        glScaled(1.5, 1, 1)             # 細長い形状に伸縮
        glutSolidCube(self.size)        # キューブを描画
        glPopMatrix()                   # 前の設定行列をスタックから取り出して復帰
        glEndList()                     # 画面描画リストの登録終了

class Player:
    cpu_id_counter = 1  # 各CPUの番号付けのためのクラス変数

    # Playerタイプ
    TYPE_USER = 0
    TYPE_CPU  = 1

    # 生存ステータス
    ALIVE = 0
    DEAD  = 1

    DELTA_T = None # 更新速度[sec]

    def __init__(self, name, car, position, velocity, direction):
        if name != None:
            self.name = name                        # プレイヤー名
            self.type = Player.TYPE_USER            # ユーザーとして設定
        else:
            self.name = 'CPU' + str(Player.cpu_id_counter) # CPU名
            Player.cpu_id_counter += 1              # CPU数をインクリメント
            self.type = Player.TYPE_CPU             # CUPとして設定

        self.car = car              # 車の種類
        self.position = position    # 位置(ベクトル)[m]
        self.velocity = velocity    # 速度(ベクトル)[m/sec]
        self.direction = direction  # 車の向き(単位ベクトル)
        self.status = Player.ALIVE  # 生存ステータス
        self.input_key = [False, False, False, False]   # 入力キー

    def __accelerate(self):
        # 車の向き(単位ベクトル)との内積から，車の向きの速さを求める
        head_velocity = self.velocity.dot(self.direction)
        if head_velocity < 0:
            head_velocity = 0   # 速度ベクトルが車の向きからみて負の方向なら0とする

        # トルクと質量から加速度を計算し，車の向きに合わせて加速
        if head_velocity < self.car.max_speed:
            self.velocity += (self.car.torque / self.car.mass * Player.DELTA_T) * self.direction

    def __brake(self):
        brake_coefficient = 0.6  # トルクからブレーキ性能を決める擬似的な係数

        # トルクとブレーキ係数，質量から減速度を計算し，車の速度方向に合わせて減速
        if np.linalg.norm(self.velocity) > 0:   # 速度があるときのみ
            self.velocity -= (self.car.torque / self.car.mass * Player.DELTA_T) * brake_coefficient \
                                                * (self.velocity / np.linalg.norm(self.velocity))

    def __turnLeft(self):
        # ベクトルを回転角に変換，車の回転パラメータ(角速度)から新しい角度を求めて，ベクトルに戻す．左旋回
        new_theta = np.arctan2(self.direction[1], self.direction[0]) + self.car.rotation * Player.DELTA_T
        self.direction[0] = np.cos(new_theta)
        self.direction[1] = np.sin(new_theta)

    def __turnRight(self):
        # ベクトルを回転角に変換，車の回転パラーメタ(角速度)から新しい角度を求めて，ベクトルに戻す．右旋回
        new_theta = np.arctan2(self.direction[1], self.direction[0]) - self.car.rotation * Player.DELTA_T
        self.direction[0] = np.cos(new_theta)
        self.direction[1] = np.sin(new_theta)

    def inputKey(self, key_array):
        self.input_key = key_array

    def calcAutoControl(self, player_list):
        d_min = np.inf      # 距離が一番近いplayerまでの距離
        d_min_index = -1    # 距離が一番近いplayerのインデックス
        for i, player in enumerate(player_list):
            if player.position[2] < 0 or player is self:
                continue    # 相手が場外(死んでいない)のとき，相手が自分であるときスキップ
            else:
                # 一番近いplayerを探す
                distance = np.linalg.norm(self.position - player.position)
                if distance < d_min:
                    d_min = distance
                    d_min_index = i

        sight = player_list[d_min_index].position - self.position   # 照準ベクトル
        sight = sight / np.linalg.norm(sight)                       # 正規化

        dot = self.direction.dot(sight)                 # 内積
        cross_z = np.cross(self.direction, sight)[2]    # 外積のz成分のみ

        if np.linalg.norm(self.velocity) > self.car.max_speed or d_min_index == -1:
            # 自分の速度が速すぎる or 相手がいない
            self.input_key[0] = False   # 加速 OFF
            self.input_key[1] = True    # 減速 ON
        else:
            if dot > 0 and np.abs(cross_z) < 0.5: # 相手が前方にいる & 相手がだいたい前
                self.input_key[0] = True    # 加速 ON
                self.input_key[1] = False   # 減速 OFF
            else:
                self.input_key[0] = False   # 加速 OFF
                self.input_key[1] = False   # 減速 OFF

        if cross_z > 0.1:       # 相手が左側にいる
            self.input_key[2] = True    # 左旋回 ON
            self.input_key[3] = False   # 右旋回 OFF
        elif cross_z < -0.1:    # 相手が右側にいる
            self.input_key[2] = False   # 左旋回 OFF
            self.input_key[3] = True    # 右旋回 ON
        else:                   # 相手が正面にいる
            self.input_key[2] = False   # 左旋回 OFF
            self.input_key[3] = False   # 右旋回 OFF

    def update(self, filed_size, filed_friction, gravity):
        # 落下済みの場合
        if self.status == Player.DEAD:
            return # 落下済みの場合，更新しないで終了

        # 落下中の場合
        if abs(self.position[0]) > filed_size/2 or abs(self.position[1]) > filed_size/2:
            self.velocity[2] -= gravity * Player.DELTA_T  # 重力加速度による落下処理

        # 行動可能状態の場合
        else:
            # 入力に従って，加速・減速・旋回
            if self.input_key[0] == True:
                self.__accelerate()  # 加速
            if self.input_key[1] == True:
                self.__brake()       # ブレーキ
            if self.input_key[2] == True:
                self.__turnLeft()    # 左旋回
            if self.input_key[3] == True:
                self.__turnRight()   # 右旋回

            # 摩擦による減速
            div = 100   # 逆方向加速防止のための時間分割数
            for i in range(div):
                if np.linalg.norm(self.velocity) > 0.1:
                    # 速度が一定以上の場合，車の速度方向に合わせて減速する
                    self.velocity -= (filed_friction * gravity) * (Player.DELTA_T/div) \
                                                    * (self.velocity / np.linalg.norm(self.velocity))
                else:
                    # 速度が一定以下の場合，完全に停止させる(0で初期化)
                    self.velocity = np.array([0,0,0], dtype=np.float)

        # 位置座標を更新
        self.position += self.velocity * Player.DELTA_T
        if self.position[2] < -20:
            self.status = Player.DEAD

    def drawCarBody(self):
        glPushMatrix() # 前の設定行列をスタックにpushして退避

        glTranslatef(self.position[0], self.position[1], self.position[2])                  # 車の位置を設定
        glRotatef(np.rad2deg(np.arctan2(self.direction[1], self.direction[0])), 0, 0, 1)    # 車の向きを設定．z軸方向に回転
        glScaled(self.car.size, self.car.size, self.car.size)                               # 車のサイズを設定
        glCallList(self.car.id)                                                             # 車の基本描画呼び出し

        # 前方方向に角を描画したい(未実装)
        # v = crossVec(trans2Vec(0, 0, 1), p.direct);
        # glColor3d(1, 0, 0);
        # glRotatef(90, v.x, v.y, v.z);
        # glutSolidCone(0.8, 2, 10, 10);

        glPopMatrix() # スタックして退避しておいた設定行列を元に戻す

    def __drawRing(self):
        theta = [np.pi/5*i for i in range(10)]  # 円を10区切り
        glColor3f(1, 0, 0)                      # 赤色で描画
        glBegin(GL_LINE_LOOP)                   # ループする線の描画を開始
        for th in theta:
            glVertex3d( # 頂点を打つ
                self.position[0] + self.car.size*np.cos(th),    # x座標
                self.position[1] + self.car.size*np.sin(th),    # y座標
                0                                               # z座標
            )
        glEnd()                                 #描画を終了

    def drawCar(self):
        if self.status == Player.DEAD:
            return # 落下済みの場合は描画しないで終了
        self.__drawRing() # 車の周りにリングを描画
        self.drawCarBody()  # 車本体を描画

class Filed:
    def __init__(self, size, friction, gravity):
        self.size = size
        self.friction = friction
        self.gravity = gravity

    def __setGround(self):
        pass

    def __drawGround(self):
        vertex = [-self.size/2 + self.size/10*i for i in range(11)] # 線の頂点座標を計算
        glColor3f(1, 1, 1)  # 白色で描画
        glBegin(GL_LINES)   # 複数の線の描画を開始
        for v in vertex:
            glVertex3d(-self.size/2, v, 0)  # xy平面の縦線始点(グラフ x=c)
            glVertex3d(self.size/2, v, 0)   # xy平面の縦線終点
            glVertex3d(v, -self.size/2, 0)  # xy平面の横線始点(グラフ y=c)
            glVertex3d(v, self.size/2, 0)   # xy平面の横線終点
        glEnd()             # 描画を終了

    def __setAxis(self):
        pass

    def __drawAxis(self):
        glBegin(GL_LINES)       # 複数の線の描画を開始
        glColor3f(1, 0, 0)      # x軸 赤色
        glVertex3d(0, 0, 0.1)   # x軸 線描画始点
        glVertex3d(5, 0, 0.1)   # x軸 線描画終点
        glColor3f(0, 1, 0)      # y軸 緑色
        glVertex3d(0, 0, 0.1)   # y軸 線描画始点
        glVertex3d(0, 5, 0.1)   # y軸 線描画終点
        glColor3f(0, 0, 1)      # z軸 青色
        glVertex3d(0, 0, 0.1)   # z軸 線描画始点
        glVertex3d(0, 0, 5.1)   # z軸 線描画終点
        glEnd()                 # 描画を終了

    def draw(self):
        self.__drawGround()
        self.__drawAxis()

class Menu:
    def __init__(self):
        self.delta_t = 0.1                      # 画面の更新速度
        Player.DELTA_T = self.delta_t           # Playerクラスの更新速度を設定
        self.ortho_size = 50                    # 画面の表示サイズ
        self.menu_num = 0                       # メニュー番号識別のための整数

        self.enter_key = False                                                   # Enterキー入力
        self.arrow_key = {'up':False, 'down':False, 'left':False, 'right':False} # 矢印キー入力
        self.bit_control_key = [ [False, False, False, False] for i in range(4)] # 各ユーザーのキー入力

        self.setting_menu_row = 0               # 設定画面メニュー選択行
        self.user_num_list = [1, 2, 3, 4, 0]    # ユーザー数の選択リスト
        self.user_num_index = 0                 # 選択しているユーザー数の選択リストのインデックス
        self.cpu_num_list = [8, 10, 12, 5]      # CPU数の選択リスト
        self.cpu_num_index = 0                  # 選択しているCPU数の選択リストのインデックス
        self.filed_num_list = [20, 50, 75]      # フィールドサイズの選択リスト
        self.filed_num_index = 0                # 選択しているフィールドサイズの選択リストのインデックス

        self.car_list = [\
            Car(600, 12, 5, 50, 0.6, 1.0, [0,1,0]), \
            Car(600, 12, 5, 50, 0.6, 1.0, [0,1,1]), \
            Car(600, 12, 5, 50, 0.6, 1.0, [1,1,0]), \
            Car(600, 12, 5, 50, 0.6, 1.0, [0,0,1]), \
            Car(600, 12, 5, 50, 0.6, 1.0, [1,1,1]) \
        ]   # bit carのリスト (加速, 最高速, 旋回, 重量, 反発, サイズ, 色)

        self.model = Player(
            'model',
            self.car_list[0],
            np.array([0,0,0],dtype=np.float),
            np.array([0,0,0],dtype=np.float),
            np.array([1,0,0],dtype=np.float)
        )                                       # bit car選択画面の表示するモデル
        self.model_index = 0                    # モデルのbit carの種類を指すインデックス
        self.model_show_angle = 0               # モデルの回転表示用の回転角
        self.user_car_list = []                 # ユーザーが選択したbit carのリスト

        self.filed = None                       # フィールド
        self.player_list = []                   # プレイヤー(ユーザーとCPU)のリスト

        self.wait = 0                           # 画面停止(カウントダウン)のための変数

    @staticmethod
    def __printString(string, position, font, color=(1,1,1)):
        string = bytes(string.encode('utf-8'))               # バイト文字列に変換
        glColor3f(color[0], color[1], color[2])              # 文字色を設定
        glRasterPos3d(position[0], position[1], position[2]) # 文字位置を設定
        for i in range(len(string)):
            glutBitmapCharacter(font, string[i])             # 一文字ずつ描画

    def draw(self):
        if self.menu_num == 0:
            self.__drawTitle()            # タイトル画面
        elif self.menu_num == 1:
            self.__drawSettingMenu()      # 設定画面
        elif self.menu_num == 2:
            self.__drawCarSelectionMenu() # 車選択画面
        elif self.menu_num == 3:
            self.__drawBattleStartCount() # バトル画面 スタートカウント
        elif self.menu_num == 4:
            self.__drawBattle()           # バトル画面
        elif self.menu_num == 5:
            self.__drawBattleFinished()   # バトル画面 終了表示
        elif self.menu_num == 6:
            self.__drawWinner()           # 勝者表示画面
        elif self.menu_num == 7:
            self.__drawRecord()           # 戦闘履歴画面(未実装)

    def __drawTitle(self):
        glMatrixMode(GL_MODELVIEW)  # モデルビュー行列を選択
        glLoadIdentity()            # 単位行列で初期化
        gluLookAt(
            0, -1, 1,
            0, 0, 0,
            0, 0, 1
        )                           # カメラ視点を設定(モデルビュー行列を設定)

        # タイトルを表示
        Menu.__printString('HIT BIT', (-6, 15, 0), GLUT_BITMAP_TIMES_ROMAN_24)
        Menu.__printString('<ENTER>', (-7, 0, 0), GLUT_BITMAP_TIMES_ROMAN_24)
        # Enterキーで次のメニューへ
        if self.enter_key == True:
            self.enter_key = False  # 連続入力防止
            self.menu_num += 1      # 次のメニューへ移動

    def __drawSettingMenu(self):
        glMatrixMode(GL_MODELVIEW)  # モデルビュー行列を選択
        glLoadIdentity()            # 単位行列で初期化
        gluLookAt(
            0, -1, 1,
            0, 0, 0,
            0, 0, 1
        )                           # カメラ視点を設定(モデルビュー行列を設定)

        # セッティングメニューを表示
        Menu.__printString('SETTING', (-6, 30, 0), GLUT_BITMAP_TIMES_ROMAN_24)
        Menu.__printString(
            'PLAYER NUM :  ' + str(self.user_num_list[self.user_num_index]),
            (-8, 10, 0),
            GLUT_BITMAP_HELVETICA_18
        ) # ユーザーの数
        Menu.__printString(
            'CPU NUM :  ' + str(self.cpu_num_list[self.cpu_num_index]),
            (-7, 0, 0),
            GLUT_BITMAP_HELVETICA_18
        ) # CUPの数
        Menu.__printString(
            'FILED SIZE :  ' + str(self.filed_num_list[self.filed_num_index]),
            (-7.5, -10, 0),
            GLUT_BITMAP_HELVETICA_18
        ) # フィールドのサイズ

        # メニュー上下移動
        if self.arrow_key['up'] == True:            # 上移動
            self.arrow_key['up'] = False            # 連続入力防止
            self.setting_menu_row = (self.setting_menu_row + 2) % 3
        elif self.arrow_key['down'] == True:        # 下移動
            self.arrow_key['down'] = False      # 連続入力防止
            self.setting_menu_row = (self.setting_menu_row + 1) % 3

        # メニュー左右移動
        bracket = '<                                    >'     # 現在選択中のメニューの囲い
        if self.setting_menu_row == 0:
            Menu.__printString(bracket, (-10, 10, 0), GLUT_BITMAP_HELVETICA_18)
            if self.arrow_key['left'] == True:      # 左移動
                self.arrow_key['left'] = False      # 連続入力防止
                self.user_num_index = \
                    (self.user_num_index + len(self.user_num_list) - 1) % len(self.user_num_list)
            elif self.arrow_key['right'] == True:   # 右移動
                self.arrow_key['right'] = False     # 連続入力防止
                self.user_num_index = (self.user_num_index + 1) % len(self.user_num_list)
        elif self.setting_menu_row == 1:
            Menu.__printString(bracket, (-10, 0, 0), GLUT_BITMAP_HELVETICA_18)
            if self.arrow_key['left'] == True:      # 左移動
                self.arrow_key['left'] = False      # 連続入力防止
                self.cpu_num_index = \
                    (self.cpu_num_index + len(self.cpu_num_list) - 1) % len(self.cpu_num_list)
            elif self.arrow_key['right'] == True:   # 右移動
                self.arrow_key['right'] = False     # 連続入力防止
                self.cpu_num_index = (self.cpu_num_index + 1) % len(self.cpu_num_list)
        elif self.setting_menu_row == 2:
            Menu.__printString(bracket, (-10, -10, 0), GLUT_BITMAP_HELVETICA_18)
            if self.arrow_key['left'] == True:      # 左移動
                self.arrow_key['left'] = False      # 連続入力防止
                self.filed_num_index = \
                    (self.filed_num_index + len(self.filed_num_list) - 1) % len(self.filed_num_list)
            elif self.arrow_key['right'] == True:   # 右移動
                self.arrow_key['right'] = False     # 連続入力防止
                self.filed_num_index = (self.filed_num_index + 1) % len(self.filed_num_list)

        # Enterキーで次のメニューへ
        if self.enter_key == True:
            # プレイヤー数が2以上のとき
            if self.user_num_list[self.user_num_index] + self.cpu_num_list[self.cpu_num_index] >= 2:
                self.enter_key = False  # 連続入力防止

                # ユーザーがいるときbit carの選択画面へ移動
                if self.user_num_list[self.user_num_index] != 0:
                    self.menu_num += 1      # 次のメニューへ移動

                # ユーザーがいないときbit carの選択画面をスキップ
                else:
                    self.__setGameContent() # ゲーム内容の設定
                    self.menu_num += 2      # 次の次のメニューへ移動

    def __drawCarSelectionMenu(self):
        glMatrixMode(GL_MODELVIEW)  # モデルビュー行列を選択
        glLoadIdentity()            # 単位行列で初期化
        gluLookAt(
            0, 1, -0.2,
            0, 0, 0,
            0, 1, 0
        )                           # カメラ視点を設定(モデルビュー行列を設定)

        # bit carの情報を表示
        Menu.__printString(
            'PLAYER ' + str(len(self.user_car_list)+1) + '                ',
            (20, 0, 20),
            GLUT_BITMAP_TIMES_ROMAN_24
        )   # 現在選択しているプレイヤー名
        Menu.__printString(
            'Bit Size ' + str(self.model.car.size * 10) + '              ',
            (0, 0, -17),
            GLUT_BITMAP_HELVETICA_18
        )   # bit carのサイズ
        Menu.__printString(
            'Weight ' + str(self.model.car.mass) + '                ',
            (0, 0, -19),
            GLUT_BITMAP_HELVETICA_18
        )   # bit carの重さ
        Menu.__printString(
            'Acceleration Force ' + str(self.model.car.torque) + '    ',
            (0, 0, -21),
            GLUT_BITMAP_HELVETICA_18
        )   # bit carの加速力
        Menu.__printString(
            'MAX Speed ' + str(self.model.car.max_speed) + '             ',
            (0, 0, -23),
            GLUT_BITMAP_HELVETICA_18
        )   # bit carの最高速
        Menu.__printString(
            'Rotation Performance ' + str(self.model.car.rotation) + '',
            (0, 0, -25),
            GLUT_BITMAP_HELVETICA_18
        )   # bit carの旋回性能

        # bit carのモデルを表示
        glPushMatrix()                              # 前の設定行列をスタックして退避
        glRotated(self.model_show_angle, 0, 0, 1)   # 回転
        glScaled(10, 10, 10)                        # 拡大
        self.model.drawCarBody()                    # 車のボディを表示
        glPopMatrix()                               # 前の設定行列をスタックから取り出して復帰

        # メニュー左右選択
        if self.arrow_key['left'] == True:          # 左移動
            self.arrow_key['left'] = False          # 連続入力防止
            self.model_index = (self.model_index + len(self.car_list) - 1) % len(self.car_list)
            self.model.car = self.car_list[self.model_index] # bit carの切り替え

        elif self.arrow_key['right'] == True:       # 右移動
            self.arrow_key['right'] = False         # 連続入力防止
            self.model_index = (self.model_index + 1) % len(self.car_list)
            self.model.car = self.car_list[self.model_index] # bit carの切り替え

        # Enterキーで次のメニューへ
        if self.enter_key == True:
            self.enter_key = False                      # 連続入力防止
            self.user_car_list.append(self.model.car)   # 選択したモデルを登録

            if len(self.user_car_list) >= self.user_num_list[self.user_num_index]:
                # 全員のbit carの選択が終了したとき
                self.__setGameContent()             # ゲーム内容の設定
                self.model_show_angle = 0           # リセット
                self.menu_num += 1                  # 次のメニューへ移動

            else:
                # 全員のbit carの選択が終了していないとき
                self.model.car = self.car_list[0]   # 次の選択のために表示をリセット
                self.model_index = 0                # 次の選択のために表示をリセット
                self.model_show_angle = 0           # 次の選択のために表示をリセット

        # 表示角度を変更
        self.model_show_angle += 5

    def __setGameContent(self):
        # フィールドの設定
        self.filed = Filed(
            size = self.filed_num_list[self.filed_num_index],   # フィールドのサイズ
            friction = 0.75,                                    # 摩擦係数
            gravity = 9.8                                       # 重力加速度
        )

        # プレイヤー数を取得
        user_num = self.user_num_list[self.user_num_index]
        cpu_num = self.cpu_num_list[self.cpu_num_index]
        player_num = user_num + cpu_num

        # プレイヤーを円形に配置のための変数
        theta = 0
        d_theta = 2*np.pi / player_num

        # ユーザーのbit carと初期位置などを設定
        for i in range(user_num):
            x = np.cos(theta)
            y = np.sin(theta)
            p_x = (self.filed.size / 4) * x
            p_y = (self.filed.size / 4) * y
            theta += d_theta

            user = Player(
                'User' + str(i+1),                  # ユーザー名
                self.user_car_list[i],              # bit car
                np.array([p_x,p_y,0], np.float),    # 初期位置
                np.array([0,0,0], np.float),        # 初期速度
                np.array([-x,-y,0], np.float)       # 初期角度
            )
            self.player_list.append(user)           # リストに追加

        # CPUのbit carと初期位置などを設定
        for i in range(cpu_num):
            x = np.cos(theta)
            y = np.sin(theta)
            p_x = (self.filed.size / 4) * x
            p_y = (self.filed.size / 4) * y
            theta += d_theta

            cpu = Player(
                None,                               # CPU名
                self.car_list[0],                   # bit car
                np.array([p_x,p_y,0], np.float),    # 初期位置
                np.array([0,0,0], np.float),        # 初期速度
                np.array([-x,-y,0], np.float)       # 初期角度
            )
            self.player_list.append(cpu)            # リストに追加

        # 視点の設定
        self.ortho_size = self.filed.size   # 描画領域の数値を設定
        glMatrixMode(GL_PROJECTION)         # 投影行列を選択
        glLoadIdentity()                    # 単位行列で初期化
        glOrtho(
            -self.ortho_size, self.ortho_size,
            -self.ortho_size, self.ortho_size,
            -self.ortho_size, self.ortho_size
        )                                   # 描画領域を設定(投影行列を設定)

    def __drawBattleStartCount(self):
        glMatrixMode(GL_MODELVIEW)  # モデルビュー行列を選択
        glLoadIdentity()            # 単位行列で初期化
        gluLookAt(
            0.2, -1.0, 1.0,
            0.0, 0.0, 0.0,
            0.0, 0.0, 1.0
        )                           # カメラ視点を設定(モデルビュー行列を設定)

        self.filed.draw()           # 地面を描画

        for player in self.player_list:
            player.drawCar()            # bit car描画
            Menu.__printString(
                player.name,            # 表示名
                player.position + 0.8,  # 表示位置(ブロードキャストに注意)
                GLUT_BITMAP_8_BY_13     # フォント
            ) # プレイヤー名を表示

        # カウントダウンを表示
        if self.wait < 5:
            string = str(int(6 - self.wait))    # 5秒間カウントダウン
        else:
            string = 'START'                    # 最後1秒は'START'を表示
        Menu.__printString(
            string,
            (-1, 0, 0),
            GLUT_BITMAP_HELVETICA_18,
            color=(1,0,1)
        ) # 文字列表示

        # カウントダウンを計算
        if self.wait < 6:
            self.wait += self.delta_t   # 時間を加算
        else:
            self.wait = 0               # 待ち時間を初期化
            self.menu_num += 1          # 次のメニューへ移動

    def __drawBattle(self):
        glMatrixMode(GL_MODELVIEW)  # モデルビュー行列を選択
        glLoadIdentity()            # 単位行列で初期化
        gluLookAt(
            0.2, -1.0, 1.0,
            0.0, 0.0, 0.0,
            0.0, 0.0, 1.0
        )                           # カメラ視点を設定(モデルビュー行列を設定)

        self.filed.draw()   # 地面を描画

        # 衝突コントロール
        for i in range(len(self.player_list)):
            j = 0
            while j < i: # i番目とj番目の衝突を計算
                player_i = self.player_list[i]
                player_j = self.player_list[j]

                # プレイヤー間の距離を計算
                sub_x = player_j.position - player_i.position
                distance = np.linalg.norm(sub_x)
                r_in = np.abs(player_i.car.size + player_j.car.size)

                # 衝突していないとき
                if distance > r_in:
                    j += 1
                    continue # do nothing

                # 衝突しているとき
                else:
                    if distance < 0.1: # bitの重なり防止のランダム反発
                        sub_x[0] += np.random.rand()*0.5
                        player_i.velocity[1] += np.random.rand()*0.5

                    # 運動量保存則から導いた円の衝突の更新式により更新
                    # v1' = v1 - [m2/(m1+m2) * (1+e) * (v1-v2)・(x2-x1)] * (x2-x1)
                    # v2' = v2 + [m1/(m1+m2) * (1+e) * (v1-v2)・(x2-x1)] * (x2-x1)
                    total_mass = player_i.car.mass + player_j.car.mass
                    total_bounce = 1 + player_i.car.bounce * player_j.car.bounce
                    dot = (player_i.velocity - player_j.velocity).dot(sub_x)
                    sub_tilde = ((total_bounce / total_mass) * dot) * sub_x

                    sub_tilde *= r_in / distance * 0.85 # bitの重なり防止のための擬似的な反発係数(距離に反比例)

                    self.player_list[i].velocity += -player_j.car.mass * sub_tilde
                    self.player_list[j].velocity += +player_i.car.mass * sub_tilde

                # jをインクリメント
                j += 1

        # bitの描画及びコントロール，更新
        self.alive_count = 0 # 生存者カウンター
        for i, player in enumerate(self.player_list):
            if player.type == Player.TYPE_USER:
                player.drawCar()                                # bit car描画
                player.inputKey(self.bit_control_key[i])        # コントロールキー入力
                player.update(self.filed.size, self.filed.friction, self.filed.gravity) # 更新
            else:
                player.drawCar()                                # bit car描画
                player.calcAutoControl(self.player_list)        # オートコントロール
                player.update(self.filed.size, self.filed.friction, self.filed.gravity) # 更新

            # 生存者をカウント
            if player.status == Player.ALIVE:
                self.alive_count += 1

        # 試合終了判定(生存者が0人または1人)
        if self.alive_count == 0 or self.alive_count == 1:
            self.menu_num += 1   # 次のメニューへ移動

    def __drawBattleFinished(self):
        glMatrixMode(GL_MODELVIEW)  # モデルビュー行列を選択
        glLoadIdentity()            # 単位行列で初期化
        gluLookAt(
            0.2, -1.0, 1.0,
            0.0, 0.0, 0.0,
            0.0, 0.0, 1.0
        )                           # カメラ視点を設定(モデルビュー行列を設定)

        self.filed.draw()           # 地面を描画
        for i, player in enumerate(self.player_list):
            player.drawCar()        # bit car描画
        Menu.__printString(
            'FINISH',
            (-1, 0, 0),
            GLUT_BITMAP_HELVETICA_18,
            color=(1,0,1)
        )                           # 'FINISH'を描画

        # カウントダウンを計算
        if self.wait < 3:
            self.wait += self.delta_t
        else:
            self.wait = 0       # 待ち時間を初期化

            # 視点をリセット
            self.ortho_size = 50                # 描画領域の数値を設定
            glMatrixMode(GL_PROJECTION)         # 投影行列を選択
            glLoadIdentity()                    # 単位行列で初期化
            glOrtho(
                -self.ortho_size, self.ortho_size,
                -self.ortho_size, self.ortho_size,
                -self.ortho_size, self.ortho_size
            )                                   # 描画領域を設定(投影行列を設定)

            # Winnerをモデルとして保持
            if self.alive_count != 0:
                for player in self.player_list:
                    if player.status == Player.ALIVE:
                        self.model.name = player.name   # Winnerの名前を保持
                        self.model.car = player.car     # Winnerのbit carを保持
                        break                           # 生存者は1人しかいないので終了

            self.menu_num += 1  # 次のメニューへ移動

    def __drawWinner(self):
        glMatrixMode(GL_MODELVIEW)  # モデルビュー行列を選択
        glLoadIdentity()            # 単位行列で初期化
        gluLookAt(
            0, 1, -0.2,
            0, 0, 0,
            0, 1, 0
        )                           # カメラ視点を設定(モデルビュー行列を設定)

        # 生存者が1人だけのとき
        if self.alive_count == 1:
            # Winnerの情報を表示
            Menu.__printString(
                'WINNER',
                (3, 0, 20),
                GLUT_BITMAP_TIMES_ROMAN_24
            )   # 'WINNER'と表示
            Menu.__printString(
                self.model.name,    # Winnerの情報はmodelに保持してある
                (1.5, 0, -25),
                GLUT_BITMAP_HELVETICA_18
            )   # Winnerの名前を表示

            # bit carのモデル(Winner)を表示
            glPushMatrix()                              # 前の設定行列をスタックして退避
            glRotated(self.model_show_angle, 0, 0, 1)   # 回転
            glScaled(10, 10, 10)                        # 拡大
            self.model.drawCarBody()                    # 車のボディを表示
            glPopMatrix()                               # 前の設定行列をスタックから取り出して復帰

            # 表示角度を変更
            self.model_show_angle += 5

        # 生存者がいないとき
        else:
            Menu.__printString(
                'DRAW',
                (0, 0, 0),
                GLUT_BITMAP_TIMES_ROMAN_24
            ) # 'DRAW'(引き分け)と表示

        # Enterキーで次のメニューへ
        if self.enter_key == True:
            self.enter_key = False      # 連続入力防止
            self.__init__()             # 全設定をリセット
            Player.cpu_id_counter = 1   # CPUのIDカウンターをリセット

    def __drawRecord(self):
        pass # (未実装)








menu = None

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGB | GLUT_DOUBLE | GLUT_DEPTH) # RGBカラー, ダブルバッファリング, 隠面消去
    glutInitWindowSize(1080, 700)                   # ウィンドウ初期サイズ
    glutInitWindowPosition(0, 0)                    # ウィンドウ初期位置
    glutCreateWindow(sys.argv[0].encode('utf-8'))   # ウィンドウ生成，表示
    initialize()                                    # 初期化
    glutDisplayFunc(display)                        # 描画処理
    glutReshapeFunc(resize)                         # ウィンドウサイズ変更時の処理
    glutKeyboardFunc(keyboardIn)                    # キーボード入力時の処理
    glutKeyboardUpFunc(keyboardOut)                 # キーボードを離した時の処理
    glutSpecialFunc(keyboardSpIn)                   # 特殊キー入力時の処理
    glutSpecialUpFunc(keyboardSpOut)                # 特殊キーを離したときの処理
    redisplayLoop(0)                                # 描画ループ
    glutMainLoop()                                  # 処理ループ

def initialize():
    glClearColor(0.0, 0.0, 0.0, 1.0)    # 黒で画面をクリア
    glEnable(GL_DEPTH_TEST)             # 隠面消去を設定
    glEnable(GL_CULL_FACE)              # カリングを設定(描画不要なところを描画しない)
    global menu
    menu = Menu()                       # メニュー画面を生成

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # カラーバッファとデプスバッファをクリア
    menu.draw()        # 画面を表示
    glutSwapBuffers()  # 実行していないコマンドを全て実行. glFlushの代わり

def resize(w, h):
    ortho_size = menu.ortho_size        # 画面表示サイズを設定

    glViewport(0, 0, w, h)              # 全画面表示
    glMatrixMode(GL_PROJECTION)         # 投影行列を選択
    glLoadIdentity()                    # 単位行列で初期化
    glOrtho(
        -ortho_size, ortho_size,
        -ortho_size, ortho_size,
        -ortho_size, ortho_size
    )                                   # 描画領域を設定(投影行列を設定)

def redisplayLoop(dummy):
    glutPostRedisplay()                                     # 再描画要請
    glutTimerFunc(int(menu.delta_t*1000), redisplayLoop, 0) # 一定時間毎に再帰させる, 3つ目の引数はdummy

def keyboardIn(key, x, y):
    # x,yはkey入力時のマウス位置
    if key == b'\r':   # Enter Key
        menu.enter_key = True
    # ユーザー1
    elif key == b'e':
        menu.bit_control_key[0][2] = True
    elif key == b'r':
        menu.bit_control_key[0][3] = True
    elif key == b'u':
        menu.bit_control_key[0][0] = True
    elif key == b'i':
        menu.bit_control_key[0][1] = True
    # ユーザー2
    elif key == b'd':
        menu.bit_control_key[1][2] = True
    elif key == b'f':
        menu.bit_control_key[1][3] = True
    elif key == b'j':
        menu.bit_control_key[1][0] = True
    elif key == b'k':
        menu.bit_control_key[1][1] = True
    # ユーザー3
    elif key == b'c':
        menu.bit_control_key[2][2] = True
    elif key == b'v':
        menu.bit_control_key[2][3] = True
    elif key == b'm':
        menu.bit_control_key[2][0] = True
    elif key == b',':
        menu.bit_control_key[2][1] = True
    # ユーザー4
    elif key == b'3':
        menu.bit_control_key[3][2] = True
    elif key == b'4':
        menu.bit_control_key[3][3] = True
    elif key == b'7':
        menu.bit_control_key[3][0] = True
    elif key == b'8':
        menu.bit_control_key[3][1] = True

def keyboardOut(key, x, y):
    # x,yはkey入力時のマウス位置
    if key == b'\r':   # Enter Key
        menu.enter_key = False
    # ユーザー1
    elif key == b'e':
        menu.bit_control_key[0][2] = False
    elif key == b'r':
        menu.bit_control_key[0][3] = False
    elif key == b'u':
        menu.bit_control_key[0][0] = False
    elif key == b'i':
        menu.bit_control_key[0][1] = False
    # ユーザー2
    elif key == b'd':
        menu.bit_control_key[1][2] = False
    elif key == b'f':
        menu.bit_control_key[1][3] = False
    elif key == b'j':
        menu.bit_control_key[1][0] = False
    elif key == b'k':
        menu.bit_control_key[1][1] = False
    # ユーザー3
    elif key == b'c':
        menu.bit_control_key[2][2] = False
    elif key == b'v':
        menu.bit_control_key[2][3] = False
    elif key == b'm':
        menu.bit_control_key[2][0] = False
    elif key == b',':
        menu.bit_control_key[2][1] = False
    # ユーザー4
    elif key == b'3':
        menu.bit_control_key[3][2] = False
    elif key == b'4':
        menu.bit_control_key[3][3] = False
    elif key == b'7':
        menu.bit_control_key[3][0] = False
    elif key == b'8':
        menu.bit_control_key[3][1] = False

def keyboardSpIn(key, x, y):
    # x,yはkey入力時のマウス位置
    if key == GLUT_KEY_UP:
        menu.arrow_key['up'] = True
    elif key == GLUT_KEY_DOWN:
        menu.arrow_key['down'] = True
    elif key == GLUT_KEY_LEFT:
        menu.arrow_key['left'] = True
    elif key == GLUT_KEY_RIGHT:
        menu.arrow_key['right'] = True

def keyboardSpOut(key, x, y):
    # x,yはkey入力時のマウス位置
    if key == GLUT_KEY_UP:
        menu.arrow_key['up'] = False
    elif key == GLUT_KEY_DOWN:
        menu.arrow_key['down'] = False
    elif key == GLUT_KEY_LEFT:
        menu.arrow_key['left'] = False
    elif key == GLUT_KEY_RIGHT:
        menu.arrow_key['right'] = False

if __name__ == '__main__':
    main()