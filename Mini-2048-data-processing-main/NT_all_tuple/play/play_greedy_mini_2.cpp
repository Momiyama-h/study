// g++ Play_perfect_player.cevals -std=c++20 -mcmodel=large -O2
#include <zlib.h>

#include <array>
#include <cfloat>
#include <climits>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <list>
#include <random>
#include <unordered_map>

namespace fs = std::filesystem;
using namespace std;

#include "../head/Game2048_3_3.h"
// // #define NT4A
// #if defined(T1)
// #include "../head/1tuples_sym.h"
// using namespace NT1;
// int nt = 1;
// #elif defined(T2)
// #include "../head/2tuples_sym.h"
// using namespace NT2;
// int nt = 2;
// #elif defined(T3)
// #include "../head/3tuples_sym.h"
// using namespace NT3;
// int nt = 3;
// #elif defined(T4)
// #include "../head/4tuples_sym.h"
// using namespace NT4;
// int nt = 4;
// #elif defined(T5)
// #include "../head/5tuples_sym.h"
// using namespace NT5;
// int nt = 5;
// #elif defined(T6)
// #include "../head/6tuples_sym.h"
// using namespace NT6;
// int nt = 6;
// #elif defined(T7)
// #include "../head/7tuples_sym.h"
// using namespace NT7;
// int nt = 7;
// #elif defined(T8)
// #include "../head/8tuples_sym.h"
// using namespace NT8;
// int nt = 8;
// #elif defined(T9)
// #include "../head/9tuples_sym.h"
// using namespace NT9;
// int nt = 9;
// #else
// デフォルトを NT6 に設定
#include "../head/6tuples_mini_2.h"
using namespace NT6;
int nt = 1;
// #endif

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

// ファイル名からパラメータを抽出する構造体と関数を追加
struct FileParams {
  int NT;
  int tupleNumber;
  int multiStaging;
  int oi;
  int seed;
  int c;
  int mini;
};

FileParams parseFileName(const char* filename) {
  FileParams params = {0, 0, 0, 0, 0, 0, 0};
  char basename[256];
  strcpy(basename, filename);

  // ファイルパスから最後の'/'以降を取得
  char* last_slash = strrchr(basename, '/');
  char* actual_name = last_slash ? last_slash + 1 : basename;

  // 最初の数字を取得してNTに設定
  params.NT = atoi(actual_name);

  // .zip 拡張子を削除
  char* ext = strstr(basename, ".zip");
  if (ext) *ext = '\0';

  // .dat 拡張子を削除
  ext = strstr(basename, ".dat");
  if (ext) *ext = '\0';

  char* token = strtok(basename, "_");
  while (token != NULL) {
    if (strncmp(token, "TupleNumber", 11) == 0)
      params.tupleNumber = atoi(token + 11);
    else if (strncmp(token, "Multistaging", 12) == 0)
      params.multiStaging = atoi(token + 12);
    else if (strncmp(token, "OI", 2) == 0)
      params.oi = atoi(token + 2);
    else if (strncmp(token, "seed", 4) == 0)
      params.seed = atoi(token + 4);
    else if (strncmp(token, "c", 1) == 0)
      params.c = atoi(token + 1);
    else if (strncmp(token, "mini", 4) == 0)
      params.mini = atoi(token + 4);

    token = strtok(NULL, "_");
  }
  return params;
}

bool loadCompressedEvs(const char* filename) {
  FileParams params = parseFileName(filename);
  init(params.tupleNumber, params.multiStaging);

  gzFile gz_fp = gzopen(filename, "rb");
  if (!gz_fp) {
    fprintf(stderr, "Error opening compressed file\n");
    return false;
  }

  FILE* temp_fp = tmpfile();
  if (!temp_fp) {
    fprintf(stderr, "Error creating temporary file\n");
    gzclose(gz_fp);
    return false;
  }

  char buffer[8192];
  int bytes_read;
  size_t total_bytes = 0;

  while ((bytes_read = gzread(gz_fp, buffer, sizeof(buffer))) > 0) {
    size_t written = fwrite(buffer, 1, bytes_read, temp_fp);
    if (written != (size_t)bytes_read) {
      fprintf(stderr,
              "Error writing to temporary file: expected %d, wrote %zu\n",
              bytes_read, written);
      fclose(temp_fp);
      gzclose(gz_fp);
      return false;
    }
    total_bytes += written;
  }

  if (bytes_read < 0) {
    int errnum;
    fprintf(stderr, "Error during decompression: %s\n",
            gzerror(gz_fp, &errnum));
    fclose(temp_fp);
    gzclose(gz_fp);
    return false;
  }

  rewind(temp_fp);

  // データを読み込む
  readEvs(temp_fp);

  // クリーンアップ
  fclose(temp_fp);
  gzclose(gz_fp);

  return true;
}

int main(int argc, char** argv) {
  if (argc < 2 + 1) {
    fprintf(stderr, "Usage: playgreedy <seed> <game_counts> <evfile>\n");
    exit(1);
  }
  int seed = atoi(argv[1]);
  int game_count = atoi(argv[2]);
  char* evfile = argv[3];
  // string number(1, evfile[12]);
  FileParams params = parseFileName(evfile);
  fs::create_directory("../board_data");
  string dir = "../board_data/NT" + to_string(params.NT) + "_TN" +
               to_string(params.tupleNumber) + "_OI" + to_string(params.oi) +
               "_seed" + to_string(params.seed) + "_mini" + to_string(params.mini) + "/";
  fs::create_directory(dir);
  fs::path abs_path = fs::absolute(dir);

  double average = 0;
  // FILE* fp = fopen(evfile, "rb");
  FILE* test_fp = fopen(evfile, "rb");
  if (!test_fp) {
    fprintf(stderr, "Error: Cannot open file %s\n", evfile);
    exit(1);
  }
  fclose(test_fp);

  if (!loadCompressedEvs(evfile)) {
    // fprintf(stderr, "Failed to load compressed file: %s\n", evfile);
    exit(1);
  }
  // FILE* fp = fopen(evfile, "rb");
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
          evals[d] = calcEv(copy.board);
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