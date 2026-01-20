#include <cstdio>
#include <cstdlib>
// #include <iostream>
// #include <string>
// #include <vector>
// #include <numeric>
// #include <fstream>
#include <cfloat>
#include <random>
using namespace std;

#include "Game2048_3_3.h"
// #define NT4A
#include "6tuples_sym.h"

int main(int argc, char** argv) {
  if (argc < 1 + 1) {
    fprintf(stderr, "Usage: play_evalafterstates <EV-file>\n");
    exit(1);
  }

  char* evfile = argv[1];
  FILE* fp = fopen(evfile, "rb");
  if (fp == NULL) {
    fprintf(stderr, "cannot open file: %s\n", evfile);
    exit(1);
  }
  readEvs(fp);
  fclose(fp);

  while (1) {
    state_t state;
    for (int i = 0; i < 9; i++) {
      int c = scanf("%d", state.board + i);
      if (c == EOF) return 0;
      if (c == 0) return 0;
    }

    double ev = calcEv(state.board);
    double err = calcErr(state.board);
    double aerr = calcAErr(state.board);
    int mincount = calcMinCount(state.board);

    printf("{'board':[");
    for (int i = 0; i < 9; i++) {
      printf("%d,", state.board[i]);
    };
    printf("], 'eval':%f, 'err':%f, 'aerr':%f, 'mincount':%d}\n", ev, err, aerr,
           mincount);
  }
  return 0;
}
