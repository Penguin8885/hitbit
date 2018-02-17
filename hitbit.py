from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import sys
import numpy as np


# class Car:
#     def __init__(self, parameter_list):
#         self.torque = parameter_list[0]
#         self.max_speed = parameter_list[1]
#         self.rotation = parameter_list[2]
#         self.mass = parameter_list[3]
#         self.size = parameter_list[4]
#         self.bounce = parameter_list[5]
#         self.color = parameter_list[6]
#         pass

# class Player:
#     cpu_counter = 1 # 各CPUの番号付けのためのクラス変数

#     def __init__(self, parameter_list):
#         self.name       # プレイヤー名
#         self.car        # 車の種類
#         self.position   # 位置
#         self.velocity   # 速度
#         self.direction  # 車の向き
#         self.input_key  # 入力されているキー
#         pass

#     def accelerate():
#         pass

#     def brake():
#         pass

#     def turn():
#         pass

#     def update():
#         pass

#     def drawCar():
#         pass

#     def __drawCar():
#         pass

#     def __drawRing():
#         theta = [np.pi/5*i for i in range(10)]  # 円を10区切り
#         glColor3f(1, 0, 0)                      # 赤色で描画
#         glBegin(GL_LINE_LOOP)                   # ループする線の描画を開始
#         for th in theta:
#             glVertex3d( # 頂点を打つ
#                 self.position[0] + self.car.size*np.cos(th),    # x座標
#                 self.position[1] + self.car.size*np.sin(th),    # y座標
#                 0                                               # z座標
#             )
#         glEnd()                                 #描画を終了

class Filed:
    def __init__(self, size):
        self.size = size

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









angle = 50
ortho_size = 50


def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGB | GLUT_DOUBLE | GLUT_DEPTH) # RGBカラー, ダブルバッファリング, 隠面消去
    glutInitWindowSize(1080, 1080)                  # ウィンドウ初期サイズ
    glutInitWindowPosition(0, 0)                    # ウィンドウ初期位置
    glutCreateWindow(sys.argv[0].encode('utf-8'))   # ウィンドウ生成，表示
    glutDisplayFunc(display)                        # 描画処理
    glutReshapeFunc(resize)                         # ウィンドウサイズ変更時の処理
    # glutKeyboardFunc(pressKey)                      # キーボード入力時の処理
    # glutSpecialFunc(pressSpKey)                     # 特殊キー入力時の処理
    # glutKeyboardUpFunc(upKey)                       # キーボードを離した時の処理
    initialize()                                    # 初期化
    redisplayLoop(0)                                # 描画ループ
    glutMainLoop()                                  # 処理ループ

def initialize():
    glClearColor(0.0, 0.0, 0.0, 1.0)    # 黒で画面をクリア
    glEnable(GL_DEPTH_TEST)             # 隠面消去を設定
    glEnable(GL_CULL_FACE)              # カリングを設定(描画不要なところを描画しない)

def display():
    global angle
    filed = Filed(50)

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # カラーバッファとデプスバッファをクリア

    glMatrixMode(GL_MODELVIEW)  # モデルビュー行列を選択
    glLoadIdentity()            # 単位行列で初期化
    gluLookAt(
        0.2, -1.0, 1.0,
        0.0, 0.0, 0.0,
        angle, 0.0, 1.0
    )                           # カメラ視点を設定(モデルビュー行列を設定)

    angle = (angle + 1) % 10

    filed.draw()

    glutSwapBuffers()  # 実行していないコマンドを全て実行. glFlushの代わり

def resize(w, h):
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

def printString(string, position, font, color=(1,1,1)):
    glColor3f(color[0], color[1], color[2])              # 文字色を設定
    glRasterPos3d(position[0], position[1], position[2]) # 文字位置を設定
    for i in range(len(string)):
        glutBitmapCharacter(font, string[i])             # 一文字ずつ描画


if __name__ == '__main__':
    main()