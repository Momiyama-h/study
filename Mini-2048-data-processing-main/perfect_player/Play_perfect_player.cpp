// g++ Play_perfect_player.cpp -std=c++20 -mcmodel=large -O2
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

#include "Game2048_3_3.h"
#include "perfect_play.h"

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
    fprintf(stderr, "Usage: playgreedy <seed> <game_counts>\n");
    exit(1);
  }
  int seed = atoi(argv[1]);
  int game_count = atoi(argv[2]);
  fs::create_directory("../board_data");
  string dir = "../board_data/PP/";
  fs::create_directory(dir);
  readDB2();
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
      double pp[n];
      for (int i = 0; i < n; i++) {
        pp[i] = -1.0e10;
      }
      for (int d = 0; d < 4; d++) {
        if (play(d, state, &copy)) {
          // int index = to_index(copy.board);
          pp[d] = eval_afterstate(copy.board);
          // printf("%f ",pp[d]);
          if (max_evr == pp[d]) {
          }
          if (max_evr < pp[d]) {
            max_evr = pp[d];
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
          pp[0], pp[1], pp[2], pp[3],
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
  FILE* fp;
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