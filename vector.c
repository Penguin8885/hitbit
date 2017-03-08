#include <math.h>
#include "vector.h"

VECTOR addVec(VECTOR v1, VECTOR v2){
	VECTOR v3;
	v3.x = v1.x + v2.x;
	v3.y = v1.y + v2.y;
	v3.z = v1.z + v2.z;
	return v3;
}

VECTOR subVec(VECTOR v1, VECTOR v2){
	VECTOR v3;
	v3.x = v1.x - v2.x;
	v3.y = v1.y - v2.y;
	v3.z = v1.z - v2.z;
	return v3;
}

VECTOR scaleVec(double s, VECTOR v){
	VECTOR v0;
	v0.x = v.x * s;
	v0.y = v.y * s;
	v0.z = v.z * s;
	return v0;
}

double dotVec(VECTOR v1, VECTOR v2){
	return (v1.x*v2.x + v1.y*v2.y + v1.z*v2.z);
}

VECTOR crossVec(VECTOR v1, VECTOR v2){
	VECTOR v3;
	v3.x = v1.y*v2.z - v1.z*v2.y;
	v3.y = v1.z*v2.x - v1.x*v2.z;
	v3.z = v1.x*v2.y - v1.y*v2.x;
	return v3;
}

double normVec(VECTOR v){
	return sqrt(v.x*v.x + v.y*v.y + v.z*v.z);
}

VECTOR directVec(VECTOR v){
	return scaleVec(1.0 / normVec(v), v);
}

VECTOR trans2Vec(double x, double y, double z){
	VECTOR v;
	v.x = x;
	v.y = y;
	v.z = z;
	return v;
}
