#include "perfect_play.h"

#include <cstdio>
using namespace std;
#include "../common/Game2048_3_3.h"
#include "../common/util.h"

double db[DBSIZE];

void readDB()
{
  FILE *fp = fopen("db.out", "rb");
  if (fp == NULL) {
    fprintf(stderr, "error opening file: db.out\n");
    exit(1);
  }
  size_t nread = fread(db, sizeof(double), DBSIZE, fp);
  // size_t nread = fread(db, sizeof(double), sizeof(db), fp);
  if (nread != DBSIZE) {
    fprintf(stderr, "error reading DB: size mismatch %ld != %ld\n", nread, DBSIZE);
    exit(1);
  }
  fclose(fp);
}

void readDB2()
{
  FILE *fp = fopen("db2.out", "rb");
  if (fp == NULL) {
    fprintf(stderr, "error opening file: db2.out\n");
    exit(1);
  }
  int count; size_t nread = fread(&count, sizeof(int), 1, fp);
  if (nread != 1) {
    fprintf(stderr, "error reading DB: size mismatch %ld != %ld\n", nread, 1L);
    exit(1);
  }
  int *ids = new int[count]; nread = fread(ids, sizeof(int), count, fp);
  if (nread != (size_t)count) {
    fprintf(stderr, "error reading DB: size mismatch %ld != %d\n", nread, count);
    exit(1);
  }
  double *evs = new double[count]; nread = fread(evs, sizeof(double), count, fp);
  if (nread != (size_t)count) {
    fprintf(stderr, "error reading DB: size mismatch %ld != %d\n", nread, count);
    exit(1);
  }
  for (int i = 0; i < count; i++) {
    db[ids[i]] = evs[i];
  }
  delete[] ids;
  delete[] evs;
  fclose(fp);
}

void eval_afterstates(const state_t& state, double ret[4])
{
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

double eval_afterstate(int board[9])
{
  return db[to_index(board)];
}

