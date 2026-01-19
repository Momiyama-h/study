#pragma once
#include <cstdio>
using namespace std;
#include "Game2048_3_3.h"

const size_t DBSIZE = 619996139 + 1;
extern double db[DBSIZE];

void readDB();
void readDB2();
void eval_afterstates(const state_t& state, double ret[4]);
double eval_afterstate(int board[9]);
