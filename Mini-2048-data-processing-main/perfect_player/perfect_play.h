#pragma once
#include <algorithm>
#include <array>
#include <cstdio>
using namespace std;
// #include "Game2048_3_3.h"

const size_t DBSIZE = 619996139 + 1;
extern double db[DBSIZE];

// #include "perfect_play.h"
using namespace std;
#include "Game2048_3_3.h"
int to_index(const int board[9]) {
  const static int rotate3[8][9] = {
      {0, 1, 2, 3, 4, 5, 6, 7, 8}, {2, 1, 0, 5, 4, 3, 8, 7, 6},
      {2, 5, 8, 1, 4, 7, 0, 3, 6}, {0, 3, 6, 1, 4, 7, 2, 5, 8},
      {8, 7, 6, 5, 4, 3, 2, 1, 0}, {6, 7, 8, 3, 4, 5, 0, 1, 2},
      {6, 3, 0, 7, 4, 1, 8, 5, 2}, {8, 5, 2, 7, 4, 1, 6, 3, 0}};
  const static long long pow11[9] = {1LL,       11LL,       121LL,
                                     1331LL,    14641LL,    161051LL,
                                     1771561LL, 19487171LL, 214358881LL};
  int index = INT_MAX;
  long long sindex0 = 0;
  for (int i = 0; i < 9; i++) {
    int j = rotate3[0][i];
    sindex0 += board[j] * pow11[i];
  }
  long long sindex1 = 0;
  for (int i = 0; i < 9; i++) {
    int j = rotate3[1][i];
    sindex1 += board[j] * pow11[i];
  }
  long long sindex2 = 0;
  for (int i = 0; i < 9; i++) {
    int j = rotate3[2][i];
    sindex2 += board[j] * pow11[i];
  }
  long long sindex3 = 0;
  for (int i = 0; i < 9; i++) {
    int j = rotate3[3][i];
    sindex3 += board[j] * pow11[i];
  }
  long long sindex4 = 0;
  for (int i = 0; i < 9; i++) {
    int j = rotate3[4][i];
    sindex4 += board[j] * pow11[i];
  }
  long long sindex5 = 0;
  for (int i = 0; i < 9; i++) {
    int j = rotate3[5][i];
    sindex5 += board[j] * pow11[i];
  }
  long long sindex6 = 0;
  for (int i = 0; i < 9; i++) {
    int j = rotate3[6][i];
    sindex6 += board[j] * pow11[i];
  }
  long long sindex7 = 0;
  for (int i = 0; i < 9; i++) {
    int j = rotate3[7][i];
    sindex7 += board[j] * pow11[i];
  }
  std::array<long long, 8> indices = {sindex0, sindex1, sindex2, sindex3,
                                      sindex4, sindex5, sindex6, sindex7};
  return *std::min_element(indices.begin(), indices.end());
}
double db[DBSIZE];

void readDB() {
  FILE *fp = fopen("db.out", "rb");
  if (fp == NULL) {
    fprintf(stderr, "error opening file: db.out\n");
    exit(1);
  }
  size_t nread = fread(db, sizeof(double), DBSIZE, fp);
  // size_t nread = fread(db, sizeof(double), sizeof(db), fp);
  if (nread != DBSIZE) {
    fprintf(stderr, "error reading DB: size mismatch %ld != %ld\n", nread,
            DBSIZE);
    exit(1);
  }
  fclose(fp);
}

void readDB2() {
  FILE *fp = fopen("db2.out", "rb");
  if (fp == NULL) {
    fprintf(stderr, "error opening file: db2.out\n");
    exit(1);
  }
  int count;
  size_t nread = fread(&count, sizeof(int), 1, fp);
  if (nread != 1) {
    fprintf(stderr, "error reading DB: size mismatch %ld != %ld\n", nread, 1L);
    exit(1);
  }
  int *ids = new int[count];
  nread = fread(ids, sizeof(int), count, fp);
  if (nread != (size_t)count) {
    fprintf(stderr, "error reading DB: size mismatch %ld != %d\n", nread,
            count);
    exit(1);
  }
  double *evs = new double[count];
  nread = fread(evs, sizeof(double), count, fp);
  if (nread != (size_t)count) {
    fprintf(stderr, "error reading DB: size mismatch %ld != %d\n", nread,
            count);
    exit(1);
  }
  for (int i = 0; i < count; i++) {
    db[ids[i]] = evs[i];
  }
  delete[] ids;
  delete[] evs;
  fclose(fp);
}

void eval_afterstates(const state_t &state, double ret[4]) {
  state_t next;
  for (int d = 0; d < 4; d++) {
    bool canMove = play(d, state, &next);
    if (canMove) {
      ret[d] = db[to_index(next.board)] + next.score - state.score;
      // ret[d] = db[to_index(next.board)];
    } else {
      ret[d] = -100000;
    }
  }
}

double eval_afterstate(int board[9]) { return db[to_index(board)]; }