// g++ Play_perfect_player.cevals -std=c++20 -mcmodel=large -O2
#include <array>
#include <cfloat>
#include <climits>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <list>
#include <unordered_map>

namespace fs = std::filesystem;
using namespace std;

#include "4tuples_sym.h"
#include "4tuples_nosym.h"
#include "6tuples_sym.h"
#include "6tuples_notsym.h"
#include "Game2048_3_3.h"
#include "fread.h"
#include "play_table.h"

class GameOver {
 public:
  int gameover_turn;
  int game;
  int progress;
  int score;
  GameOver(int gameover_turn_init, int game_init, int progress_init,
           int score_init)
      : gameover_turn(gameover_turn_init),
        game(game_init),
        progress(progress_init),
        score(score_init) {}
};
int progress_calculation(int board[9]) {
  int sum = 0;
  for (int i = 0; i < 9; i++) {
    if (board[i] != 0) {
      sum += 1 << board[i];
    }
  }
  return sum / 2;
}
int main(int argc, char** argv) {
  if (argc < 2 + 1) {
    fprintf(stderr, "Usage: playgreedy <seed> <game_counts> <evfile> [sym|notsym] [4|6]\n");
    exit(1);
  }
  int seed = atoi(argv[1]);
  int game_count = atoi(argv[2]);
  char* evfile = argv[3];
  string evfile_name(evfile);
  string basename = fs::path(evfile_name).filename().string();
  // prev:
  // string number(1, evfile[0]);
  // string symmetry = "sym";
  // if (argc > 4) {
  //   symmetry = argv[4];
  //   if (symmetry != "sym" && symmetry != "notsym") { ... }
  // } else {
  //   if (evfile_name.find("notsym") != string::npos) { symmetry = "notsym"; }
  // }
  string number;
  bool number_set = false;
  bool symmetry_set = false;
  string symmetry = "sym";
  for (int i = 4; i < argc; i++) {
    string opt = argv[i];
    if (opt == "sym" || opt == "notsym") {
      symmetry = opt;
      symmetry_set = true;
    } else if (opt == "4" || opt == "6") {
      number = opt;
      number_set = true;
    } else {
      fprintf(stderr, "Error: unknown option: %s\n", opt.c_str());
      exit(1);
    }
  }
  if (!symmetry_set) {
    if (basename.find("notsym") != string::npos || basename.find("nosym") != string::npos) {
      symmetry = "notsym";
    }
  }
  if (!number_set) {
    if (!basename.empty() && (basename[0] == '4' || basename[0] == '6')) {
      number = string(1, basename[0]);
    } else {
      fprintf(stderr, "Error: evfile must start with '4' or '6': %s\n", basename.c_str());
      exit(1);
    }
  }

  // prev:
  // fs::create_directory("../board_data");
  // string dir = "../board_data/NT" + number + "_" + symmetry + "/";
  string base_root = "../board_data";
  const char* base_env = getenv("BOARD_DATA_ROOT");
  if (base_env && *base_env) {
    base_root = base_env;
  }
  fs::create_directories(base_root);
  string dir = base_root + "/NT" + number + "_" + symmetry + "/";
  fs::create_directories(dir);

  double average = 0;
  FILE* fp = fopen(evfile, "rb");
  if (fp == NULL) {
    fprintf(stderr, "cannot open file: %s\n", evfile);
    exit(1);
  }
  if (number == "4") {
    if (symmetry == "sym") {
      NT4::readEvs(fp);
    } else {
      NT4_notsym::readEvs(fp);
    }
  } else {
    if (symmetry == "sym") {
      NT6::readEvs(fp);
    } else {
      NT6_notsym::readEvs(fp);
    }
  }
  fclose(fp);
  srand(seed);
  list<array<int, 9>> state_list;
  list<array<int, 9>> after_state_list;
  const int eval_length = 5;
  list<array<double, eval_length>> eval_list;
  list<GameOver> GameOver_list;
  double score_sum = 0;
  for (int gid = 1; gid <= game_count; gid++) {
    state_t state = initGame();
    int turn = 0;
    while (true) {
      turn++;
      state_t copy;
      double max_evr = -DBL_MAX;
      int selected = -1;
      const int n = 5;
      double evals[n];
      for (int i = 0; i < n; i++) {
        evals[i] = -1.0e10;
      }
      for (int d = 0; d < 4; d++) {
        if (play(d, state, &copy)) {
          // int index = to_index(copy.board);
          if (number == "4") {
            if (symmetry == "sym") {
              evals[d] = NT4::calcEv(copy.board);
            } else {
              evals[d] = NT4_notsym::calcEv(copy.board);
            }
          } else {
            if (symmetry == "sym") {
              evals[d] = NT6::calcEv(copy.board);
            } else {
              evals[d] = NT6_notsym::calcEv(copy.board);
            }
          }
          // printf("%f ",evals[d]);
          if (max_evr == evals[d]) {
          }
          if (max_evr < evals[d]) {
            max_evr = evals[d];
            selected = d;
          }
        }
      }
      // printf("\n");
      state_list.push_back(
          array<int, 9>{state.board[0], state.board[1], state.board[2],
                        state.board[3], state.board[4], state.board[5],
                        state.board[6], state.board[7], state.board[8]});
      play(selected, state, &state);
      after_state_list.push_back(
          array<int, 9>{state.board[0], state.board[1], state.board[2],
                        state.board[3], state.board[4], state.board[5],
                        state.board[6], state.board[7], state.board[8]});
      // const int index = eval_length+1;
      eval_list.push_back(array<double, eval_length>{
          evals[0], evals[1], evals[2], evals[3],
          (double)progress_calculation(state.board)});
      putNewTile(&state);

      if (gameOver(state)) {
        GameOver_list.push_back(GameOver(
            turn, gid, progress_calculation(state.board), state.score));
        score_sum += state.score;
        // printf("gameover : %d\n", state.score);
        break;
      }
    }
  }
  // printf("average = %f\n", score_sum / game_count);
  string file;
  string fullPath;
  const char* filename;
  // FILE* fp;
  int i;
  auto trun_itr = GameOver_list.begin();
  file = "state.txt";
  fullPath = dir + file;
  filename = fullPath.c_str();
  fp = fopen(filename, "w+");
  i = 0;
  trun_itr = GameOver_list.begin();
  for (auto itr = state_list.begin(); itr != state_list.end(); itr++) {
    i++;
    if ((trun_itr)->gameover_turn == i) {
      i = 0;
      fprintf(fp, "gameover_turn: %d; game: %d; progress: %d; score: %d\n",
              (trun_itr)->gameover_turn, (trun_itr)->game, (trun_itr)->progress,
              (trun_itr)->score);
      trun_itr++;
    } else {
      for (int j = 0; j < 9; j++) {
        fprintf(fp, "%d ", (*itr)[j]);
      }
      fprintf(fp, "\n");
    }
  }
  fclose(fp);
  file = "after-state.txt";
  fullPath = dir + file;
  filename = fullPath.c_str();
  fp = fopen(filename, "w+");
  i = 0;
  trun_itr = GameOver_list.begin();
  for (auto itr = after_state_list.begin(); itr != after_state_list.end();
       itr++) {
    i++;
    if ((trun_itr)->gameover_turn == i) {
      i = 0;
      fprintf(fp, "gameover_turn: %d; game: %d; progress: %d; score: %d\n",
              (trun_itr)->gameover_turn, (trun_itr)->game, (trun_itr)->progress,
              (trun_itr)->score);
      trun_itr++;
    } else {
      for (int j = 0; j < 9; j++) {
        fprintf(fp, "%d ", (*itr)[j]);
      }
      fprintf(fp, "\n");
    }
  }
  fclose(fp);
  file = "eval.txt";
  fullPath = dir + file;
  filename = fullPath.c_str();
  fp = fopen(filename, "w+");
  i = 0;
  trun_itr = GameOver_list.begin();
  for (auto itr = eval_list.begin(); itr != eval_list.end(); itr++) {
    i++;
    if ((trun_itr)->gameover_turn == i) {
      i = 0;
      fprintf(fp, "gameover_turn: %d; game: %d; progress: %d; score: %d\n",
              (trun_itr)->gameover_turn, (trun_itr)->game, (trun_itr)->progress,
              (trun_itr)->score);
      trun_itr++;
    } else {
      for (int j = 0; j < eval_length; j++) {
        if (j + 1 >= eval_length) {
          fprintf(fp, "%d ", (int)(*itr)[j]);
        } else {
          fprintf(fp, "%f ", (*itr)[j]);
        }
      }
      fprintf(fp, "\n");
    }
  }
  fclose(fp);
}
