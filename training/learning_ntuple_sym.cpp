#include <cstdio>
#include <cstdlib>
#include <cfloat>
#include <ctime>
#include <random>
using namespace std;

#include "Game2048_3_3.h"
// #define NT4A  // Uncomment this line to use 4-tuples instead of 6-tuples
// prev:
// #ifdef NT4A
// #include "4tuples_sym.h"
// #else
// #include "6tuples_sym.h"
// #endif
#if defined(USE_4TUPLE)
#include "4tuples_sym.h"
#else
#include "6tuples_sym.h"
#endif

#ifndef STORAGE_FREQUENCY
#define STORAGE_FREQUENCY (5*10000000)
#endif
#ifndef STORAGE_COUNT
#define STORAGE_COUNT 10
#endif
#ifndef MAX_GAMES
#define MAX_GAMES 1000000000 //100000//
#endif
#ifndef ENABLE_CSV_LOG
#define ENABLE_CSV_LOG 0
#endif
#ifndef ENABLE_BOARD_LOG
#define ENABLE_BOARD_LOG 0
#endif

int storage_c = 0;
int global_seed = 0;
FILE *csv_fp = nullptr;
FILE *board_log_fp = nullptr;

// 特定のタプルの特定の盤面状態を記録する設定
#define TRACKED_TUPLE_ID 0  // 追跡するタプルID

// 固定盤面状態を指定（9要素の配列）
// 0: タイルがない、1-10: タイル値（2^1から2^10）
// 例：すべて0の初期状態
static const int FIXED_BOARD[9] = { 0 ,1, 2 ,0 ,0 , 1 , 0 ,0 ,0  };
// 別の例：{1, 1, 1, 1, 0, 0, 0, 0, 0}  // 左上4個が2のタイル

void openBoardLog()
{
#if !ENABLE_BOARD_LOG
  return;
#endif
  board_log_fp = fopen("board_log.csv", "w");
  if (!board_log_fp) {
    fprintf(stderr, "Failed to open board_log.csv\n");
    return;
  }
  // CSVヘッダー出力
  fprintf(board_log_fp, "game_id,turn,score,tile0,tile1,tile2,tile3,tile4,tile5,tile6,tile7,tile8\n");
  fflush(board_log_fp);
}

void closeBoardLog()
{
  if (board_log_fp) {
    fclose(board_log_fp);
  }
}

void logBoard(int game_id, int turn, int score, const int* board)
{
  if (!board_log_fp) return;
  fprintf(board_log_fp, "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d\n",
          game_id, turn, score, board[0], board[1], board[2], board[3], board[4], 
          board[5], board[6], board[7], board[8]);
  fflush(board_log_fp);
}

void openCsvLog()
{
#if !ENABLE_CSV_LOG
  return;
#endif
  // 現在時刻を取得して15分単位に切り捨て
  time_t now = time(nullptr);
  struct tm* t = localtime(&now);
  int rounded_min = (t->tm_min / 15) * 15;
  
  char filename[256];
  sprintf(filename, "tuple_learning_rate_log_seed%d_%04d%02d%02d%02d%02d.csv",
          global_seed, t->tm_year + 1900, t->tm_mon + 1, t->tm_mday, t->tm_hour, rounded_min);
  
  csv_fp = fopen(filename, "w");
  if (!csv_fp) {
    fprintf(stderr, "Failed to open %s\n", filename);
    return;
  }
  printf("CSV log: %s\n", filename);
  // CSVヘッダー出力
  fprintf(csv_fp, "game_id,score,total_turns,tuple_id,stage,board_index,aerr,err,updatecounts\n");
  // fflush(csv_fp);  // Removed for performance - OS buffering is sufficient
}

void closeCsvLog()
{
  if (csv_fp) {
    fclose(csv_fp);
  }
}

void logTupleStats(int game_id, int score, int total_turns, const int* board)
{
  if (!csv_fp) return;
  
  // ステージ判定（固定盤面から判定）
  int s = 0;
  for (int i = 0; i < 9; i++) {
    if (FIXED_BOARD[i] >= 9) s = 1;
  }
  
  // 追跡するタプルの盤面インデックスを計算（固定盤面を使用、対称性考慮）
  double avg_aerr = 0.0;
  double avg_err = 0.0;
  int avg_updatecounts = 0;
  
  // 8方向の対称性を考慮して平均値を計算
  for (int j = 0; j < 8; j++) {
    int index = 0;
    for (int k = 0; k < TUPLE_SIZE; k++) {
      index = index * VARIATION_TILE + FIXED_BOARD[sympos[j][pos[TRACKED_TUPLE_ID][k]]];
    }
    avg_aerr += aerrs[s][TRACKED_TUPLE_ID][index];
    avg_err += errs[s][TRACKED_TUPLE_ID][index];
    avg_updatecounts += updatecounts[s][TRACKED_TUPLE_ID][index];
  }
  
  avg_aerr /= 8.0;
  avg_err /= 8.0;
  avg_updatecounts /= 8.0;
  
  // 最初の方向のインデックス計算用
  int index = 0;
  for (int k = 0; k < TUPLE_SIZE; k++) {
    index = index * VARIATION_TILE + FIXED_BOARD[sympos[0][pos[TRACKED_TUPLE_ID][k]]];
  }
  
  fprintf(csv_fp, "%d,%d,%d,%d,%d,%d,%.6f,%.6f,%d\n",
          game_id, score, total_turns, TRACKED_TUPLE_ID, s, index, avg_aerr, avg_err, avg_updatecounts);
  // fflush(csv_fp);  // Removed for performance - buffered I/O is faster
}

void saveEvs()
{
  char filename[1024];
#if defined(USE_4TUPLE) || defined(NT4A)
  sprintf(filename, "4tuple_sym_data_%d_%d.dat", global_seed, storage_c++);
#else
  sprintf(filename, "6tuple_sym_data_%d_%d.dat", global_seed, storage_c++);
#endif
  FILE *fp = fopen(filename, "wb");
  if (!fp) {
    fprintf(stderr, "file %s open failed.\n", filename);
  }
  writeEvs(fp);
  fclose(fp);
  printf("stored %s\n", filename);
  if (storage_c == STORAGE_COUNT) exit(0);
}

int main(int argc, char* argv[])
{
  if (argc < 1+1) {
    fprintf(stderr, "Usage: learning_ntuple <seed>\n");
    exit(1);
  }
  global_seed = atoi(argv[1]);
  srand(global_seed);

  initEvs(0);
  openCsvLog();
  openBoardLog();

  int traincount = 0;
  for (int gid = 0; gid < MAX_GAMES; gid++) {
    state_t state = initGame();
    int turn = 0;
    int lastboard[9] = {0};
    while (true) { // ゲームのループ
      turn++;
      state_t copy;
      double max_ev_r = -DBL_MAX;
      int selected = -1;
      for (int d = 0; d < 4; d++) {
	if (play(d, state, &copy)) {
	  double ev_r = calcEv(copy.board) + (copy.score - state.score);
	  if (ev_r > max_ev_r) {
	    max_ev_r = ev_r;
	    selected = d;
	  }
	  // printf("d=%d, ev_r=%f, max_ev_r=%f\n",
	  // 	 d, ev_r, max_ev_r);
	}
      }
      // state.print();
      // printf("selected = %d\n", selected);
      if (selected == -1) {
	fprintf(stderr, "Something wrong. No direction played.\n");
      }
      play(selected, state, &state);
      if (turn > 1) {
	update(lastboard, max_ev_r - calcEv(lastboard));
	traincount++;
	if (traincount % STORAGE_FREQUENCY == 0) saveEvs();
      }
      for (int i = 0; i < 9; i++) {
	lastboard[i] = state.board[i];
      }
      // 新しいタイル追加前の盤面を記録
     // logBoard(gid+1, turn, state.score, state.board);
      putNewTile(&state);
      
      if (gameOver(state)) {
	update(lastboard, 0 - calcEv(lastboard));
	traincount++;
	if (traincount % STORAGE_FREQUENCY == 0) saveEvs();
	printf("game %d finished with score %d\n", gid+1, state.score);
	// ゲーム終了時に学習率を記録
	logTupleStats(gid+1, state.score, turn, lastboard);
	break;
      }
    }
  }

  closeCsvLog();
  closeBoardLog();
  fprintf(stderr, "Training finished before saving %d data\n", STORAGE_COUNT);
  return 0;
}
