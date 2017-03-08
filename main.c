#define _CRT_SECURE_NO_WARNINGS

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "GL/glut.h"
#include "vector.h"

#define TRUE 1
#define FALSE 0

#define PI 3.141592653589793238462643383279
#define RAD2DEG(r) (r * 180.0 / PI)	//[rad] -> [deg]
#define MPS2KMPH(v) (v * 3.6)		//[m/s] -> [km/h]









#define GRAVITY 9.81				//[m/s^2]
#define UPDATE_RATE 100				//[sec]
#define DIVISION 100				//分割
#define DELTAT ((double)UPDATE_RATE / 1000.0 / DIVISION) //Δt[s]

int ortho_size = 50;

#define ID_BIT1 501
#define ID_BIT2 502
#define ID_BIT3 503
#define ID_BIT4 504
#define ID_BIT5 505

#define LEFT 1
#define RIGHT -1

typedef struct CAR {
	int id;				//ID番号
	double torque;		//トルク[N]
	double max_speed;	//最大速度[m/s]
	double rotation;	//旋回性能[rad]
	double mass;		//質量[kg]
	double size;		//サイズ[m]
	double bounce;		//反発係数
} CAR;

CAR car[5] = {
	{ ID_BIT1, 300, 10, 0.3, 200, 1.0, 0.6 },
	{ ID_BIT2, 400, 5, 0.1, 260, 1.5, 0.6 },
	{ ID_BIT3, 200, 15, 0.5, 100, 0.8, 0.6 },
	{ ID_BIT4, 300, 10, 0.5, 200, 1, 0.8 },
	{ ID_BIT5, 500, 15, 0.5, 300, 1, 0.6 }
};

typedef struct SPKEY {
	char enter;
	char up;
	char down;
	char left;
	char right;
} SPKEY;

SPKEY spkey = { FALSE, FALSE, FALSE, FALSE, FALSE };

typedef struct KEY {
	char a;
	char b;
	char l;
	char r;
} KEY;

typedef struct PLAYER {
	VECTOR direct;
	VECTOR x;
	VECTOR v;
	CAR car;
	KEY input;
} PLAYER;

PLAYER *player = NULL;
int playerNum = 0;
int userNum, cpuNum;

char name[50][16] = {
	"Alice",
	"Bob",
	"Charlie",
	"David",
	"Eric",
	"Flora",
	"Geirge",
	"Helen",
	"Isabel",
	"Jane",
	"Kate",
	"Layla",
	"Marilyn",
	"Nancy",
	"Olive",
	"Pansy",
	"Ted",
	"Ulysses",
	"Victor",
	"William",
	"Alex",
	"Ben",
	"Cory",
	"Danny",
	"Edgar",
	"Frank",
	"Gene",
	"Harry",
	"Ian",
	"Jack",
	"Kent",
	"Leo",
	"Mark",
	"Nick",
	"Oscar",
	"Paul",
	"Quincy",
	"Randolf",
	"Steve",
	"Tom",
	"Ulysses",
	"Virgil",
	"Walt",
	"Zachary",
	"Anthony",
	"Brian",
	"Clark",
	"Dick",
	"Evan",
	"Freddie"
};




void PrintString(void *font, char *m, int msize, double x, double y, double z){
	int i;
	glColor3d(1, 1, 1);
	glRasterPos3d(x, y, z);
	for (i = 0; i < msize; i++){
		glutBitmapCharacter(font, m[i]);
	}
}

void DrawAxis(){
	glBegin(GL_LINES);
	glColor3d(1, 0, 0);
	glVertex3d(0, 0, 0.1);
	glVertex3d(5, 0, 0.1);
	glColor3d(0, 1, 0.1);
	glVertex3d(0, 0, 0.1);
	glVertex3d(0, 5, 0.1);
	glColor3d(0, 0, 1.1);
	glVertex3d(0, 0, 0.1);
	glVertex3d(0, 0, 5.1);
	glEnd();
}

void DrawGround(double filed_size){
	int i;
	double pos;

	glBegin(GL_LINES);
	{
		glColor3f(1, 1, 1);
		for (i = -filed_size / 2; i <= filed_size / 2; i += 10){
			pos = i * 1.0;
			glVertex3d(-filed_size / 2, pos, 0);
			glVertex3d(filed_size / 2, pos, 0);
			glVertex3d(pos, -filed_size / 2, 0);
			glVertex3d(pos, filed_size / 2, 0);
		}
	}
	glEnd();
}

void DrawCircle(PLAYER p){
	int i;
	double theta = 0, dt, x, y;
	int n = 10;
	glColor3d(1, 0, 0);
	dt = 2.0 * PI / n;
	glBegin(GL_LINE_LOOP);
	for (i = 0; i < n; i++){
		x = p.x.x + p.car.size * cos(theta);
		y = p.x.y + p.car.size * sin(theta);
		glVertex3d(x, y, 0);
		theta += dt;
	}
	glEnd();
}

void DrawCar(PLAYER p){
	VECTOR v;

	DrawCircle(p);
	glPushMatrix();
	glTranslatef(p.x.x, p.x.y, p.x.z);
	glRotatef(RAD2DEG(atan2(p.direct.y, p.direct.x)), 0, 0, 1);
	glScaled(p.car.size, p.car.size, p.car.size);
	glCallList(p.car.id);

	v = crossVec(trans2Vec(0, 0, 1), p.direct);
	glColor3d(1, 0, 0);
	glRotatef(90, v.x, v.y, v.z);
	glutSolidCone(0.8, 2, 10, 10);
	glPopMatrix();
}




double AHeadVelocity(PLAYER p){
	double v;
	v = dotVec(p.direct, p.v);
	if (v > 0) return v;
	else return 0;
}

void AccelerateCar(PLAYER *p){
	if (AHeadVelocity(*p) < p->car.max_speed){
		p->v = addVec(p->v, scaleVec(p->car.torque / p->car.mass, p->direct));
	}
}

void BrakeCar(PLAYER *p){
	int i;
	for (i = 0; i < DIVISION; i++){
		if (normVec(p->v) > 0) {
			p->v = subVec(p->v, scaleVec((p->car.torque / p->car.mass) * 10.0 * DELTAT, directVec(p->v)));
		}
	}
}

void TurnCar(PLAYER *p, int rot){
	if (rot == LEFT){
		p->direct.x = cos(atan2(p->direct.y, p->direct.x) + p->car.rotation);
		p->direct.y = sin(atan2(p->direct.y, p->direct.x) + p->car.rotation);
		return;
	}
	if (rot == RIGHT){
		p->direct.x = cos(atan2(p->direct.y, p->direct.x) - p->car.rotation);
		p->direct.y = sin(atan2(p->direct.y, p->direct.x) - p->car.rotation);
		return;
	}
}


void CalcCPUControl(){
	int i, j;
	int near;
	double dot, cross;
	for (i = userNum; i < playerNum; i++){
		near = 0;
		for (j = 1; j < playerNum; j++){
			if (j == i) continue;
			if (player[j].x.z < 0) continue;
			if (normVec(subVec(player[i].x, player[j].x)) < normVec(subVec(player[i].x, player[near].x))) near = j;
		}


		dot = dotVec(player[i].direct, directVec(subVec(player[near].x, player[i].x)));
		cross = crossVec(player[i].direct, directVec(subVec(player[near].x, player[i].x))).z;

		if (player[near].x.z < 0){
			player[i].input.a = FALSE;
			player[i].input.b = TRUE;
		}
		else{
			if (fabs(cross) < 0.5 && dot > 0) player[i].input.a = TRUE;
			else player[i].input.a = FALSE;
		}
		if (cross > 0.1){
			player[i].input.l = TRUE;
			player[i].input.r = FALSE;
		}
		else if (cross < -0.1){
			player[i].input.l = FALSE;
			player[i].input.r = TRUE;
		}
		else{
			player[i].input.l = FALSE;
			player[i].input.r = FALSE;
		}
	}
}


void CalcCollision(PLAYER *p1, PLAYER *p2){
	VECTOR c;
	VECTOR v1, v2;
	VECTOR s;
	if (normVec(subVec(p1->x, p2->x)) > (p1->car.size + p2->car.size)) {
		return;
	}
	//puts("collosion");

	v1 = p1->v;
	v2 = p2->v;

	c = subVec(p2->x, p1->x);
	s = scaleVec(1.0 / (p1->car.mass + p2->car.mass) * (1 + p1->car.bounce * p2->car.bounce) * dotVec(subVec(v1, v2), c), c);
	p1->v = addVec(v1, scaleVec(-p2->car.mass, s));
	p2->v = addVec(v2, scaleVec(p1->car.mass, s));
}

void UpdatePlayer(PLAYER *p, double filed_size){
	int i;

	for (i = 0; i < DIVISION; i++){
		if (fabs(p->x.x) > filed_size / 2.0 || fabs(p->x.y) > filed_size / 2.0){
			p->v.z -= GRAVITY * DELTAT;
		}else if (normVec(p->v) > 0) {
			p->v = subVec(p->v, scaleVec((0.75 * GRAVITY) * DELTAT, directVec(p->v)));
		}
		p->x = addVec(p->x, scaleVec(DELTAT, p->v));
		if (normVec(p->v) < 0.1) p->v = trans2Vec(0, 0, 0);
	}
	if (fabs(p->x.x) > filed_size / 2.0 || fabs(p->x.y) > filed_size / 2.0){
		p->input.a = p->input.b = p->input.l = p->input.r = FALSE;
	}

	if (p->input.a == TRUE) AccelerateCar(p);
	if (p->input.b == TRUE) BrakeCar(p);
	if (p->input.l == TRUE) TurnCar(p, LEFT);
	if (p->input.r == TRUE) TurnCar(p, RIGHT);

	//printf("∠:%5.1lf\tx(%6.2lf, %6.2lf, %6.2lf)\tv(%6.2lf, %6.2lf, %6.2lf)\n", RAD2DEG(atan2(p->direct.y, p->direct.x)), p->x.x, p->x.y, p->x.z, MPS2KMPH(p->v.x), MPS2KMPH(p->v.y), MPS2KMPH(p->v.z));
}




void Display(void){
	int i, j;
	char str[256] = { 0 };
	static int stage = -1;
	static double filed_size;	//[m]
	static double wait = 0;		//[sec]

	static int menu = 0;
	static int user_p = 0;
	int user_m[4] = { 1, 2, 3 };
	static int cpu_p = 0;
	int cpu_m[5] = { 1, 5, 10, 50, 0 };
	static int filed_p = 0;
	int filed_m[4] = { 50, 100, 150, 20 };
	char bracket[] = "<                                    >";

	static double angle = 0;
	static int bit_p = 0;
	int bit_m[4] = { 0, 1, 2, 4};
	static int ply_p = 0;
	static CAR ply_m[3];

	double theta = 0, dt, x, y;
	int surviver;
	static int surviver_index;

	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

	if (stage == -1){
		glMatrixMode(GL_MODELVIEW);
		glLoadIdentity();
		gluLookAt(0, -1, 1, 0, 0, 0, 0, 0, 1);

		if (spkey.enter == TRUE){
			spkey.enter = FALSE;
			stage++;
		}

		PrintString(GLUT_BITMAP_TIMES_ROMAN_24, "HIT BIT", sizeof("HIT BIT"), -6, 30, 0);
		PrintString(GLUT_BITMAP_TIMES_ROMAN_24, "<ENTER>", sizeof("<ENTER>"), -7, -20, 0);
	}

	if (stage == 0){
		glMatrixMode(GL_MODELVIEW);
		glLoadIdentity();
		gluLookAt(0, -1, 1, 0, 0, 0, 0, 0, 1);

		if (spkey.enter == TRUE){
			spkey.enter = FALSE;
			if (cpu_m[cpu_p] + user_m[user_p] > 1 && !(cpu_m[cpu_p] == 50 && filed_m[filed_p] < 100)) stage++;
		}
		if (spkey.up == TRUE){
			menu = (menu + 2) % 3;
			spkey.up = FALSE;
		}
		else if (spkey.down == TRUE){
			menu = (menu + 1) % 3;
			spkey.down = FALSE;
		}
		switch (menu){
		case 0:
			PrintString(GLUT_BITMAP_HELVETICA_18, bracket, sizeof(bracket), -10, 10, 0);
			if (spkey.left == TRUE){
				user_p = (user_p + 2) % 3;
				spkey.left = FALSE;
			}
			else if (spkey.right == TRUE){
				user_p = (user_p + 1) % 3;
				spkey.right = FALSE;
			}
			break;
		case 1:
			PrintString(GLUT_BITMAP_HELVETICA_18, bracket, sizeof(bracket), -10, 0, 0);
			if (spkey.left == TRUE){
				cpu_p = (cpu_p + 4) % 5;
				spkey.left = FALSE;
			}
			else if (spkey.right == TRUE){
				cpu_p = (cpu_p + 1) % 5;
				spkey.right = FALSE;
			}
			break;
		case 2:
			PrintString(GLUT_BITMAP_HELVETICA_18, bracket, sizeof(bracket), -10, -10, 0);
			if (spkey.left == TRUE){
				filed_p = (filed_p + 3) % 4;
				spkey.left = FALSE;
			}
			else if (spkey.right == TRUE){
				filed_p = (filed_p + 1) % 4;
				spkey.right = FALSE;
			}
			break;
		default:
			break;
		}

		PrintString(GLUT_BITMAP_TIMES_ROMAN_24, "SETTING", sizeof("SETING"), -6, 30, 0);
		sprintf(str, "PLAYER  NUM %2d\0", user_m[user_p]);
		str[strlen(str)] = '\0';
		PrintString(GLUT_BITMAP_HELVETICA_18, str, sizeof(str), -7, 10, 0);
		sprintf(str, "CPU  NUM    %2d\0", cpu_m[cpu_p]);
		str[strlen(str)] = '\0';
		PrintString(GLUT_BITMAP_HELVETICA_18, str, sizeof(str), -7, 0, 0);
		sprintf(str, "FILED  SIZE %3d\0", filed_m[filed_p]);
		str[strlen(str)] = '\0';
		PrintString(GLUT_BITMAP_HELVETICA_18, str, sizeof(str), -7, -10, 0);
	}

	else if (stage == 1){
		PLAYER model = { { 1, 0, 0 } };

		glMatrixMode(GL_MODELVIEW);
		glLoadIdentity();
		gluLookAt(0, 1, -0.2, 0, 0, 0, 0, 1, 0);
		glPushMatrix();
		glRotated(angle, 0, 0, 1);
		glScaled(10, 10, 10);

		if (spkey.left == TRUE){
			bit_p = (bit_p + 3) % 4;
			spkey.left = FALSE;
		}
		else if (spkey.right == TRUE){
			bit_p = (bit_p + 1) % 4;
			spkey.right = FALSE;
		}

		model.car = car[bit_m[bit_p]];
		DrawCar(model);
		glPopMatrix();

		sprintf(str, "PLAYER %d                ", ply_p + 1);
		str[strlen(str)] = '\0';
		PrintString(GLUT_BITMAP_TIMES_ROMAN_24, str, sizeof(str), 20, 0, 20);

		sprintf(str, "Bit Size %d              ", (int)(model.car.size * 10));
		str[strlen(str)] = '\0';
		PrintString(GLUT_BITMAP_HELVETICA_18, str, sizeof(str), 0, 0, -17);
		sprintf(str, "Weight %d                ", (int)model.car.mass);
		str[strlen(str)] = '\0';
		PrintString(GLUT_BITMAP_HELVETICA_18, str, sizeof(str), 0, 0, -19);
		sprintf(str, "Acceleration Force %d    ", (int)model.car.torque);
		str[strlen(str)] = '\0';
		PrintString(GLUT_BITMAP_HELVETICA_18, str, sizeof(str), 0, 0, -21);
		sprintf(str, "MAX Speed %d             ", (int)model.car.max_speed);
		str[strlen(str)] = '\0';
		PrintString(GLUT_BITMAP_HELVETICA_18, str, sizeof(str), 0, 0, -23);
		sprintf(str, "Rotation Performance   %d", (int)(model.car.rotation * 10));
		str[strlen(str)] = '\0';
		PrintString(GLUT_BITMAP_HELVETICA_18, str, sizeof(str), 0, 0, -25);

		if (spkey.enter == TRUE){
			spkey.enter = FALSE;
			ply_m[ply_p] = model.car;
			ply_p++;
		}
		if (ply_p >= user_m[user_p]) stage++;

		angle += 5;
	}

	else if (stage == 2){
		userNum = user_m[user_p];
		cpuNum = cpu_m[cpu_p];
		filed_size = filed_m[filed_p];
		playerNum = userNum + cpuNum;
		player = (PLAYER*)malloc(sizeof(PLAYER)*playerNum);

		for (i = 0; i < userNum; i++){
			player[i].car = ply_m[i];
		}
		for (i = userNum; i < playerNum; i++){
			player[i].car = car[3];
		}

		dt = 2.0 * PI / playerNum;
		for (i = 0; i < playerNum; i++){
			x = cos(theta);
			y = sin(theta);
			theta += dt;

			player[i].direct = trans2Vec(x, y, 0);
			player[i].x = trans2Vec(-filed_size / 4.0 * x, -filed_size / 4.0 * y, 0);
			player[i].v = trans2Vec(0, 0, 0);
			player[i].input.a = player[0].input.b = player[0].input.l = player[0].input.r = FALSE;
		}

		ortho_size = filed_size;
		glMatrixMode(GL_PROJECTION);
		glLoadIdentity();
		glOrtho(-ortho_size, ortho_size, -ortho_size, ortho_size, -ortho_size, ortho_size);
		stage++;
	}

	else if (stage == 3){
		glMatrixMode(GL_MODELVIEW);
		glLoadIdentity();
		gluLookAt(0.2, -1, 1, 0, 0, 0, 0, 0, 1);

		DrawGround(filed_size);
		for (i = 0; i < userNum; i++){
			sprintf(str, "Player%d", i + 1);
			str[strlen(str)] = '\0';
			PrintString(GLUT_BITMAP_8_BY_13, str, sizeof(str), player[i].x.x + 0.8, player[i].x.y + 0.8, player[i].x.z + 0.8);
			DrawCar(player[i]);
		}
		for (i = userNum; i < playerNum; i++){
			DrawCar(player[i]);
			PrintString(GLUT_BITMAP_8_BY_13, name[i - userNum], sizeof(name[i - userNum]), player[i].x.x + 0.5, player[i].x.y + 0.5, player[i].x.z + 0.5);
		}

		if (wait < 5) {
			sprintf(str, "%d      ", (int)(6 - wait));
			str[strlen(str)] = '\0';
		}
		else sprintf(str, "START ");
		PrintString(GLUT_BITMAP_TIMES_ROMAN_24, str, sizeof(str), 0, 0, 0);
		if (wait < 6) wait += UPDATE_RATE / 1000.0;
		else {
			wait = 0;
			stage++;
		}
	}

	else if (stage == 4){
		glMatrixMode(GL_MODELVIEW);
		glLoadIdentity();
		gluLookAt(0.2, -1, 1, 0, 0, 0, 0, 0, 1);

		DrawGround(filed_size);

		CalcCPUControl();

		for (i = 0; i < playerNum; i++){
			if (player[i].x.z < -20) continue;
			UpdatePlayer(&player[i], filed_size);
			DrawCar(player[i]);
		}
		for (i = 0; i < playerNum; i++){
			for (j = i + 1; j < playerNum; j++){
				CalcCollision(&player[i], &player[j]);
			}
		}

		surviver = 0;
		for (i = 0; i < playerNum; i++)	if (player[i].x.z > -20) surviver++;
		if (surviver == 1) {
			for (i = 0; i < playerNum; i++) if (player[i].x.z > -20) surviver_index = i;
			stage++;
		}
	}

	else if (stage == 5){
		glMatrixMode(GL_MODELVIEW);
		glLoadIdentity();
		gluLookAt(0.2, -1, 1, 0, 0, 0, 0, 0, 1);

		DrawGround(filed_size);
		for (i = 0; i < playerNum; i++) DrawCar(player[i]);
		PrintString(GLUT_BITMAP_TIMES_ROMAN_24, "FINISH", sizeof("FINISH"), 0, 0, 0);
		if (wait < 3) wait += UPDATE_RATE / 1000.0;
		else {
			wait = 0;
			ortho_size = 50;
			glMatrixMode(GL_PROJECTION);
			glLoadIdentity();
			glOrtho(-ortho_size, ortho_size, -ortho_size, ortho_size, -ortho_size, ortho_size);
			stage++;
		}
	}

	else if (stage == 6){
		glMatrixMode(GL_MODELVIEW);
		glLoadIdentity();
		gluLookAt(0, 1, -0.2, 0, 0, 0, 0, 1, 0);

		glPushMatrix();
		glRotated(angle, 0, 0, 1);
		glScaled(10, 10, 10);

		player[surviver_index].direct = trans2Vec(1, 0, 0);
		player[surviver_index].x = trans2Vec(0, 0, 0);

		DrawCar(player[surviver_index]);
		glPopMatrix();

		PrintString(GLUT_BITMAP_TIMES_ROMAN_24, "WINNER", sizeof("WINNER"), 3, 0, 20);
		if (surviver_index < userNum) sprintf(str, "player %d", surviver_index + 1);
		else sprintf(str, "cpu %s", name[surviver_index - userNum]);
		str[strlen(str)] = '\0';
		PrintString(GLUT_BITMAP_HELVETICA_18, str, sizeof(str), 0, 0, -25);

		angle += 5;
		if (spkey.enter == TRUE){
			ortho_size = 50;
			free(player);
			player = NULL;
			playerNum = 0;
			stage = -1;
			filed_size;
			wait = 0;

			menu = 0;
			user_p = 0;
			cpu_p = 0;

			filed_p = 0;
			angle = 0;
			bit_p = 0;
			ply_p = 0;

			spkey.enter = FALSE;
		}
	}

	glutSwapBuffers();
}

void Resize(int w, int h){
	glViewport(0, 0, w, h);
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	glOrtho(-ortho_size, ortho_size, -ortho_size, ortho_size, -ortho_size, ortho_size);
}

void Mouse(int button, int state, int x, int y){
	switch (button) {
	default:
		break;
	}
}

void KeyboardIn(unsigned char key, int x, int y){
	switch (key) {
	case 'a':
		if (playerNum > 0) player[0].input.l = TRUE;
		break;
	case 's':
		if (playerNum > 0) player[0].input.r = TRUE;
		break;
	case 'k':
		if (playerNum > 0) player[0].input.a = TRUE;
		break;
	case 'l':
		if (playerNum > 0) player[0].input.b = TRUE;
		break;
	case 'z':
		if (playerNum > 1) player[1].input.l = TRUE;
		break;
	case 'x':
		if (playerNum > 1) player[1].input.r = TRUE;
		break;
	case ',':
		if (playerNum > 1) player[1].input.a = TRUE;
		break;
	case '.':
		if (playerNum > 1) player[1].input.b = TRUE;
		break;
	case 'q':
		if (playerNum > 2) player[2].input.l = TRUE;
		break;
	case 'w':
		if (playerNum > 2) player[2].input.r = TRUE;
		break;
	case 'i':
		if (playerNum > 2) player[2].input.a = TRUE;
		break;
	case 'o':
		if (playerNum > 2) player[2].input.b = TRUE;
	case 13:
		spkey.enter = TRUE;
		break;
	case '\033':
		exit(EXIT_SUCCESS);
	default:
		break;
	}
}

void KeyboardOut(unsigned char key, int x, int y){
	switch (key) {
	case 'a':
		if (playerNum > 0) player[0].input.l = FALSE;
		break;
	case 's':
		if (playerNum > 0) player[0].input.r = FALSE;
		break;
	case 'k':
		if (playerNum > 0) player[0].input.a = FALSE;
		break;
	case 'l':
		if (playerNum > 0) player[0].input.b = FALSE;
		break;
	case 'z':
		if (playerNum > 1) player[1].input.l = FALSE;
		break;
	case 'x':
		if (playerNum > 1) player[1].input.r = FALSE;
		break;
	case ',':
		if (playerNum > 1) player[1].input.a = FALSE;
		break;
	case '.':
		if (playerNum > 1) player[1].input.b = FALSE;
		break;
	case 'q':
		if (playerNum > 2) player[2].input.l = FALSE;
		break;
	case 'w':
		if (playerNum > 2) player[2].input.r = FALSE;
		break;
	case 'i':
		if (playerNum > 2) player[2].input.a = FALSE;
		break;
	case 'o':
		if (playerNum > 2) player[2].input.b = FALSE;
	case 13:
		spkey.enter = FALSE;
		break;
	case '\033':
		exit(EXIT_SUCCESS);
	default:
		break;
	}
}

void KeyboardSpecial(int key, int x, int y){
	switch (key) {
	case GLUT_KEY_UP:
		spkey.up = TRUE;
		break;
	case GLUT_KEY_DOWN:
		spkey.down = TRUE;
		break;
	case GLUT_KEY_LEFT:
		spkey.left = TRUE;
		break;
	case GLUT_KEY_RIGHT:
		spkey.right = TRUE;
		break;
	}
}

static void Redisplay(int dummy){
	glutTimerFunc(UPDATE_RATE, Redisplay, 0);
	glutPostRedisplay();
}

void Initialize(void){
	glClearColor(0.0, 0.0, 0.0, 1.0);

	glEnable(GL_DEPTH_TEST);
	glEnable(GL_CULL_FACE);

	glNewList(ID_BIT1, GL_COMPILE);
	{
		glColor3f(0, 1, 0);
		glPushMatrix();
		glScaled(1.5, 1, 1);
		glutSolidCube(1);
		glPopMatrix();
	}
	glEndList();

	glNewList(ID_BIT2, GL_COMPILE);
	{
		glColor3f(0, 1, 1);
		glPushMatrix();
		glScaled(1.5, 1, 1);
		glutSolidCube(1);
		glPopMatrix();
	}
	glEndList();

	glNewList(ID_BIT3, GL_COMPILE);
	{
		glColor3f(1, 1, 0);
		glPushMatrix();
		glScaled(1.5, 1, 1);
		glutSolidCube(1);
		glPopMatrix();
	}
	glEndList();

	glNewList(ID_BIT4, GL_COMPILE);
	{
		glColor3f(0, 0, 1);
		glPushMatrix();
		glScaled(1.5, 1, 1);
		glutSolidCube(1);
		glPopMatrix();
	}
	glEndList();

	glNewList(ID_BIT5, GL_COMPILE);
	{
		glColor3f(1, 1, 1);
		glPushMatrix();
		glScaled(1.5, 1, 1);
		glutSolidCube(1);
		glPopMatrix();
	}
	glEndList();

	printf("[ key info ]\n");
	printf("\tenter\t\t: goto next\n");
	printf("\tup, down\t: select menu\n");
	printf("\tleft, right\t: select value\n");
	putchar('\n');
	printf("\ta : player1 rotate left\n");
	printf("\ts : player1 rotate right\n");
	printf("\tk : player1 accelerate\n");
	printf("\tl : player1 brake\n");
	putchar('\n');
	printf("\tz : player2 rotate left\n");
	printf("\tx : player2 rotate right\n");
	printf("\t, : player2 accelerate\n");
	printf("\t. : player2 brake\n");
	putchar('\n');
	printf("\tq : player3 rotate left\n");
	printf("\tw : player3 rotate right\n");
	printf("\ti : player3 accelerate\n");
	printf("\to : player3 brake\n");
}

int main(int argc, char *argv[]){
	glutInitWindowPosition(0, 0);
	glutInitWindowSize(1080, 1080);
	glutInit(&argc, argv);
	glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH);
	glutCreateWindow(argv[0]);
	glutDisplayFunc(Display);
	glutReshapeFunc(Resize);
	glutMouseFunc(Mouse);
	glutKeyboardFunc(KeyboardIn);
	glutKeyboardUpFunc(KeyboardOut);
	glutSpecialFunc(KeyboardSpecial);
	Initialize();
	Redisplay(0);
	glutMainLoop();
	return 0;
}