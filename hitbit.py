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

    DELTA_T = 0.1 # 更新速度[sec]

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
            if player.status == Player.DEAD or player == self:
                continue    # 相手が死んでいるとき，相手が自分であるときスキップ
            else:
                # 一番近いplayerを探す
                distance = np.linalg.norm(self.position - player.position)
                if distance < d_min:
                    d_min = distance
                    d_min_index = i

        sight = player_list[d_min_index].position - self.position   # 照準ベクトル
        sight = sight / np.linalg.norm(sight)                       # 正規化

        dot = np.dot(self.direction, sight)             # 内積
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
        div = 100   # bitの重なり防止のための時間分割数
        for i in range(div):
            self.position += self.velocity * (Player.DELTA_T/div)
            if self.position[2] < -20:
                self.status = Player.DEAD

    def __drawCar(self):
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
        self.__drawCar()  # 車本体を描画

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
    key_arrow = [False, False, False, False]                            # 矢印キー入力
    bit_control_key = [ [False, False, False, False] for i in range(4)] # 各ユーザーのキー入力

    def __init__(self):
        self.menu_num = 4   # メニュー番号識別のための整数
        self.filed = Filed(size=100, friction=0.75, gravity=9.8)   # フィールド
        self.car_list = [\
            Car(600, 10, 3, 50, 0.6, 1.0, [0,1,0]), \
            Car(600,  5, 1, 50, 0.6, 1.5, [0,1,1]), \
            Car(600, 15, 5, 50, 0.6, 0.8, [1,1,0]), \
            Car(600, 10, 5, 50, 0.8, 1.0, [0,0,1]), \
            Car(600, 15, 5, 50, 0.6, 1.0, [1,1,1]) \
        ]   # 車のリスト (加速, 最高速, 旋回, 重量, 反発, サイズ, 色)
        self.player_list = [\
            Player('yoshida', self.car_list[0], np.array([0,-1,0],dtype=np.float), np.array([0,0,0],dtype=np.float), np.array([1,0,0],dtype=np.float)), \
            Player(None, self.car_list[0], np.array([1,0,0],dtype=np.float), np.array([0,0,0],dtype=np.float), np.array([1,0,0],dtype=np.float)), \
            Player(None, self.car_list[0], np.array([-1,0,0],dtype=np.float), np.array([0,0,0],dtype=np.float), np.array([1,0,0],dtype=np.float)), \
            Player(None, self.car_list[0], np.array([0,1,0],dtype=np.float), np.array([0,0,0],dtype=np.float), np.array([1,0,0],dtype=np.float)) \
        ]   # プレイヤーのリスト

    @staticmethod
    def __printString(string, position, font, color=(1,1,1)):
        glColor3f(color[0], color[1], color[2])              # 文字色を設定
        glRasterPos3d(position[0], position[1], position[2]) # 文字位置を設定
        for i in range(len(string)):
            glutBitmapCharacter(font, string[i])             # 一文字ずつ描画

    def draw(self):
        if self.menu_num == 0:
            self.__drawTitle()          # タイトル画面
        elif self.menu_num == 1:
            self.__drawSettingMenu()    # 設定画面
        elif self.menu_num == 2:
            self.__drawCarSelectionMenu # 車選択画面
        elif self.menu_num == 3:
            self.__drawBattleStartCount # バトル画面 スタートカウント
        elif self.menu_num == 4:
            self.__drawBattle()         # バトル画面
        elif self.menu_num == 5:
            self.__drawBattleFinished   # バトル画面 終了表示
        elif self.menu_num == 6:
            self.__drawWinner           # 勝者表示画面
        elif self.menu_num == 7:
            self.__drawRecord           # 戦闘履歴画面(未実装)

    def __drawTitle(self):
        pass

    def __drawSettingMenu(self):
        pass

    def __drawCarSelectionMenu(self):
        pass

    def __drawBattleStartCount(self):
        pass

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
                    # 運動量保存則から導いた円の衝突の更新式により更新
                    # v1' = v1 - [m2/(m1+m2) * (1+e) * (v1-v2)・(x2-x1)] * (x2-x1)
                    # v2' = v2 + [m1/(m1+m2) * (1+e) * (v1-v2)・(x2-x1)] * (x2-x1)
                    total_mass = player_i.car.mass + player_j.car.mass
                    total_bounce = 1 + player_i.car.bounce * player_j.car.bounce
                    dot = np.dot(player_i.velocity - player_j.velocity, sub_x)
                    sub_tilde = ((total_bounce / total_mass) * dot) * sub_x
                    sub_tilde *= r_in / distance * 0.9 # bitの重なり防止のための擬似的な反発係数(距離に反比例)
                    self.player_list[i].velocity -= player_j.car.mass * sub_tilde
                    self.player_list[j].velocity += player_i.car.mass * sub_tilde

                # jをインクリメント
                j += 1

        # bitの描画及びコントロール，更新
        for i, player in enumerate(self.player_list):
            if player.type == Player.TYPE_USER:
                player.drawCar()                                # 描画
                player.inputKey(Menu.bit_control_key[i])        # コントロールキー入力
                player.update(self.filed.size, self.filed.friction, self.filed.gravity) # 更新
            else:
                player.drawCar()                                # 描画
                player.calcAutoControl(self.player_list)        # オートコントロール
                player.update(self.filed.size, self.filed.friction, self.filed.gravity) # 更新


    def __drawBattleFinished(self):
        pass

    def __drawWinner(self):
        pass

    def __drawRecord(self):
        pass # (未実装)








menu = None

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGB | GLUT_DOUBLE | GLUT_DEPTH) # RGBカラー, ダブルバッファリング, 隠面消去
    glutInitWindowSize(1080, 1080)                  # ウィンドウ初期サイズ
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
    menu = Menu()

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # カラーバッファとデプスバッファをクリア
    menu.draw()        # 画面を表示
    glutSwapBuffers()  # 実行していないコマンドを全て実行. glFlushの代わり

def resize(w, h):
    ortho_size = 50

    glViewport(0, 0, w, h)              # 全画面表示
    glMatrixMode(GL_PROJECTION)         # 投影行列を選択
    glLoadIdentity()                    # 単位行列で初期化
    glOrtho(
        -ortho_size, ortho_size,
        -ortho_size, ortho_size,
        -ortho_size, ortho_size
    )                                   # 描画領域を設定(投影行列を設定)

def redisplayLoop(dummy):
    glutPostRedisplay()                     # 再描画要請
    glutTimerFunc(100, redisplayLoop, 0)    # 100ms毎に再帰させる, 3つ目の引数はdummy
                                            # 更新速度を変更する場合，PlayerクラスのDELTA_Tも変更

def keyboardIn(key, x, y):
    # x,yはkey入力時のマウス位置
    # ユーザー1
    if key == b'q':
        Menu.bit_control_key[0][2] = True
    elif key == b'w':
        Menu.bit_control_key[0][3] = True
    elif key == b'y':
        Menu.bit_control_key[0][0] = True
    elif key == b'u':
        Menu.bit_control_key[0][1] = True
    # ユーザー2
    elif key == b'a':
        Menu.bit_control_key[1][2] = True
    elif key == b's':
        Menu.bit_control_key[1][3] = True
    elif key == b'h':
        Menu.bit_control_key[1][0] = True
    elif key == b'j':
        Menu.bit_control_key[1][1] = True
    # ユーザー3
    elif key == b'z':
        Menu.bit_control_key[2][2] = True
    elif key == b'x':
        Menu.bit_control_key[2][3] = True
    elif key == b'n':
        Menu.bit_control_key[2][0] = True
    elif key == b'm':
        Menu.bit_control_key[2][1] = True
    # ユーザー4
    elif key == b'1':
        Menu.bit_control_key[3][2] = True
    elif key == b'2':
        Menu.bit_control_key[3][3] = True
    elif key == b'6':
        Menu.bit_control_key[3][0] = True
    elif key == b'7':
        Menu.bit_control_key[3][1] = True

def keyboardOut(key, x, y):
    # x,yはkey入力時のマウス位置
    if key == b'q':
        Menu.bit_control_key[0][2] = False
    elif key == b'w':
        Menu.bit_control_key[0][3] = False
    elif key == b'y':
        Menu.bit_control_key[0][0] = False
    elif key == b'u':
        Menu.bit_control_key[0][1] = False
    # ユーザー2
    elif key == b'a':
        Menu.bit_control_key[1][2] = False
    elif key == b's':
        Menu.bit_control_key[1][3] = False
    elif key == b'h':
        Menu.bit_control_key[1][0] = False
    elif key == b'j':
        Menu.bit_control_key[1][1] = False
    # ユーザー3
    elif key == b'z':
        Menu.bit_control_key[2][2] = False
    elif key == b'x':
        Menu.bit_control_key[2][3] = False
    elif key == b'n':
        Menu.bit_control_key[2][0] = False
    elif key == b'm':
        Menu.bit_control_key[2][1] = False
    # ユーザー4
    elif key == b'1':
        Menu.bit_control_key[3][2] = False
    elif key == b'2':
        Menu.bit_control_key[3][3] = False
    elif key == b'6':
        Menu.bit_control_key[3][0] = False
    elif key == b'7':
        Menu.bit_control_key[3][1] = False

def keyboardSpIn(key, x, y):
    # x,yはkey入力時のマウス位置
    if key == GLUT_KEY_UP:
        Menu.key_arrow[0] = True
    elif key == GLUT_KEY_DOWN:
        Menu.key_arrow[1] = True
    elif key == GLUT_KEY_LEFT:
        Menu.key_arrow[2] = True
    elif key == GLUT_KEY_RIGHT:
        Menu.key_arrow[3] = True

def keyboardSpOut(key, x, y):
    # x,yはkey入力時のマウス位置
    print('key out')
    if key == GLUT_KEY_UP:
        Menu.key_arrow[0] = False
    elif key == GLUT_KEY_DOWN:
        Menu.key_arrow[1] = False
    elif key == GLUT_KEY_LEFT:
        Menu.key_arrow[2] = False
    elif key == GLUT_KEY_RIGHT:
        Menu.key_arrow[3] = False

if __name__ == '__main__':
    main()