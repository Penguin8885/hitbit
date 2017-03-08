#ifndef VECTOR_H
#define VECTOR_H

typedef struct VECTOR {
	double x;
	double y;
	double z;
} VECTOR;

VECTOR addVec(VECTOR v1, VECTOR v2);
VECTOR subVec(VECTOR v1, VECTOR v2);
VECTOR scaleVec(double s, VECTOR v);
double dotVec(VECTOR v1, VECTOR v2);
VECTOR crossVec(VECTOR v1, VECTOR v2);
double normVec(VECTOR v);

VECTOR directVec(VECTOR v);
VECTOR trans2Vec(double x, double y, double z);

#endif