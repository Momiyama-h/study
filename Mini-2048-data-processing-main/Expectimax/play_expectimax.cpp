#include <algorithm>
#include <cfloat>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <list>
#include <numeric>
#include <string>
#include <unordered_map>
#include <vector>
using namespace std;

// #include "../common/util.h"
// #include "util.h"
#include "Game2048_3_3.h"
// #define NT4A
// #include "4tuples_sym.h"

#ifdef NT4
#include "4tuples_sym.h"
string NT = "NT4";
#else
#include "6tuples_sym.h"
string NT = "NT6";
#endif

#include "expmax.h"
// #define OUTPUT_AFTERSTATES

int main(int argc, char *argv[]) {
  if (argc < 4 + 1) {
    fprintf(stderr,
            "Usage: play_expectimax <seed> <num_games> <depth> <EV-file>");
    exit(1);
  }

  int seed = atoi(argv[1]);
  int game_count = atoi(argv[2]);
  int number_of_depth = atoi(argv[3]);
  char *evfile = argv[4];

  srand(seed);
  FILE *fp = fopen(evfile, "rb");
  if (fp == NULL) {
    fprintf(stderr, "cannot open file: %s\n", evfile);
    exit(1);
  }
  readEvs(fp);
  fclose(fp);

  for (int gid = 0; gid < game_count; gid++) {
    exp_count = 0;
    state_t state = initGame();
    int turn = 0;
    while (true) {
      turn++;
      int selected = expectimax(state, number_of_depth);
      printf("exp_count : %d\n", exp_count);
      exp_count = 0;
      if (selected == -1) {
        fprintf(stderr, "Something wrong. No direction played.\n");
      }
      play(selected, state, &state);
#ifdef OUTPUT_AFTERSTATES
      for (int i = 0; i < 9; i++) {
        printf("%d ", state.board[i]);
      }
      printf("\n");
#endif
      putNewTile(&state);

      if (gameOver(state)) {
#ifndef OUTPUT_AFTERSTATES
        // printf("game %d finished with score %d\n", gid + 1, state.score);
        printf("score : %d\n", state.score);
#endif
        break;
      }
    }
  }
  return 0;
}
