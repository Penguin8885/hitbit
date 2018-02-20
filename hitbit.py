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

class MobableObject: # (未実装)
    def __init__(self):
        pass

    def update(self, delta_t, filed_size, filed_friction):
        pass

class UnmobableObject: # (未実装)
    def __init__(self):
        pass

    def update(self, hit):
        pass

class Player:
    cpu_id_counter = 1 # 各CPUの番号付けのためのクラス変数

    # キー入力のためのキーコード
    key_up      = 1
    key_down    = 2
    key_left    = 3
    key_right   = 4

    # 生存ステータス
    alive = 0
    death = 1

    def __init__(self, name, car, position, velocity, direction):
        if name != None:
            self.name = name                        # プレイヤー名
        else:
            self.name = 'CPU' + str(Player.cpu_id_counter) # CPU名
            Player.cpu_id_counter += 1

        self.car = car              # 車の種類
        self.position = position    # 位置(ベクトル)[m]
        self.velocity = velocity    # 速度(ベクトル)[m/sec]
        self.direction = direction  # 車の向き(単位ベクトル)
        self.status = Player.alive  # 生存ステータス

    def __accelerate(self, delta_t):
        # 車の向き(単位ベクトル)との内積から，車の向きの速さを求める
        head_velocity = self.velocity.dot(self.direction)
        if head_velocity < 0:
            head_velocity = 0   # 速度ベクトルが車の向きからみて負の方向なら0とする

        # トルクと質量から加速度を計算し，車の向きに合わせて加速
        if head_velocity < self.car.max_speed:
            self.velocity += (self.car.torque / self.car.mass * delta_t) * self.direction

    def __brake(self, delta_t):
        brake_coefficient = 10  # トルクからブレーキ性能を決める擬似的な係数

        # トルクとブレーキ係数，質量から減速度を計算し，車の速度方向に合わせて減速
        if np.linalg.norm(self.velocity) > 0:   # 速度があるときのみ
            self.velocity -= (self.car.torque / self.car.mass * delta_t) * brake_coefficient \
                                                * (self.velocity / np.linalg.norm(self.velocity))

    def __turnLeft(self, delta_t):
        # ベクトルを回転角に変換，車の回転パラメータ(角速度)から新しい角度を求めて，ベクトルに戻す．左旋回
        new_theta = np.arctan2(self.direction[1], self.direction[0]) + self.car.rotation * delta_t
        self.direction[0] = np.cos(new_theta)
        self.direction[1] = np.sin(new_theta)

    def __turnRight(self, delta_t):
        # ベクトルを回転角に変換，車の回転パラーメタ(角速度)から新しい角度を求めて，ベクトルに戻す．右旋回
        new_theta = np.arctan2(self.direction[1], self.direction[0]) - self.car.rotation * delta_t
        self.direction[0] = np.cos(new_theta)
        self.direction[1] = np.sin(new_theta)

    def update(self, input_key, delta_t, filed_size, filed_friction, gravity):
        # 落下済みの場合
        if self.status == Player.death:
            return # 落下済みの場合，更新しないで終了

        # 落下中の場合
        if abs(self.position[0]) > filed_size/2 or abs(self.position[1]) < filed_size/2:
            self.velocity[2] -= gravity * delta_t # 重力加速度による落下処理

        # 行動可能状態の場合
        else:
            # 入力に従って，加速・減速・旋回
            if input_key == Player.key_up:
                self.__accelerate(delta_t)  # 加速
            elif input_key == Player.key_down:
                self.__brake(delta_t)       # ブレーキ
            elif input_key == Player.key_left:
                self.__turnLeft(delta_t)    # 左旋回
            elif input_key == Player.key_right:
                self.__turnRight(delta_t)   # 右旋回
            else:
                pass # do nothing

            # 摩擦による減速
            if np.linalg.norm(self.velocity) > 0.1:
                # 速度が一定以上の場合，車の速度方向に合わせて減速する
                self.velocity -= (filed_friction * self.car.mass * gravity) * delta_t \
                                                * (self.velocity / np.linalg.norm(self.velocity))
            else:
                # 速度が一定以下の場合，完全に停止させる(0で初期化)
                self.velocity = np.array([0,0,0])

        # 位置座標を更新
        self.position += self.velocity * delta_t
        if self.position[2] < -20:
            self.status = Player.death

        # 座標とかの表示を標準出力にするといいかも．．．(未実装)

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
        if self.status == Player.death:
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
    def __init__(self):
        self.menu_num = 4   # メニュー番号識別のための整数
        self.filed = Filed(size=50, friction=0.75, gravity=9.8)   # フィールド
        self.car_list = [\
                            Car(300, 10, 0.3, 200, 0.6, 1.0, [0,1,0]), \
                            Car(400,  5, 0.1, 260, 0.6, 1.5, [0,1,1]), \
                            Car(200, 15, 0.5, 100, 0.6, 0.8, [1,1,0]), \
                            Car(300, 10, 0.5, 200, 0.8, 1.0, [0,0,1]), \
                            Car(500, 15, 0.5, 300, 0.6, 1.0, [1,1,1]) \
                        ]   # 車のリスト
        self.player_list = \
        [Player('yoshida', self.car_list[0], np.array([0,0,0]), np.array([0,0,0]), np.array([0,0,0]))] # プレイヤーのリスト

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

        self.filed.draw()
        for player in self.player_list:
            player.drawCar()

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
    # glutKeyboardFunc(pressKey)                      # キーボード入力時の処理
    # glutSpecialFunc(pressSpKey)                     # 特殊キー入力時の処理
    # glutKeyboardUpFunc(upKey)                       # キーボードを離した時の処理
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


if __name__ == '__main__':
    main()