#include <cstdio>
#include <cstdlib>
#include <cfloat>
#include <ctime>
#include<cmath>
#include <random>
#include <filesystem>
#include <string>
using namespace std;
namespace fs = std::filesystem;

#include "Game2048_3_3.h"
// #define NT4A  // Uncomment this line to use 4-tuples instead of 6-tuples
// prev:
// #ifdef NT4A
// #include "4tuples_nosym.h"
// #else
// #include "6tuples_notsym.h"
// #endif
#if defined(USE_4TUPLE)
#include "4tuples_nosym.h"
#else
#include "6tuples_notsym.h"
#endif

#ifndef STORAGE_FREQUENCY
#define STORAGE_FREQUENCY (5*100000000)
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
#ifndef ENABLE_STDOUT_LOG
#define ENABLE_STDOUT_LOG 1
#endif

#if ENABLE_STDOUT_LOG
#define STDOUT_LOG(...) printf(__VA_ARGS__)
#else
#define STDOUT_LOG(...) \
  do {                 \
  } while (0)
#endif

int storage_c = 0;
int global_seed = 0;
FILE *csv_fp = nullptr;
FILE *board_log_fp = nullptr;
static fs::path output_dir;
static string run_name;

// 追跡するタプルIDを指定（必要に応じて変更）
#if defined(USE_4TUPLE) || defined(NT4A)
static constexpr int TRACKED_TUPLE_ID[] = {0, 3, 6, 9, 12, 15, 18, 21};
#else
// 6tuple(notsym)はNUM_TUPLE=16なので、0..7を追跡
static constexpr int TRACKED_TUPLE_ID[] = {0, 1, 2, 3, 4, 5, 6, 7};
#endif
static constexpr int TRACKED_TUPLE_COUNT =
    sizeof(TRACKED_TUPLE_ID) / sizeof(TRACKED_TUPLE_ID[0]);

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
  board_log_fp = fopen("board_log_notsym.csv", "w");
  if (!board_log_fp) {
    fprintf(stderr, "Failed to open board_log_notsym.csv\n");
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
  const char* tag = getenv("CSV_LOG_TAG");
  char suffix[64] = "";
  if (tag && *tag) {
    snprintf(suffix, sizeof(suffix), "__%s", tag);
  }
  // 現在時刻を取得して15分単位に切り捨て
  time_t now = time(nullptr);
  struct tm* t = localtime(&now);
  int rounded_min = (t->tm_min / 15) * 15;
  
  char filename[256];
  sprintf(filename, "tuple_learning_rate_log_notsym_seed%d_%04d%02d%02d%02d%02d%s.csv",
          global_seed, t->tm_year + 1900, t->tm_mon + 1, t->tm_mday,
          t->tm_hour, rounded_min, suffix);

  fs::path csv_path = output_dir / filename;
  csv_fp = fopen(csv_path.string().c_str(), "w");
  if (!csv_fp) {
    fprintf(stderr, "Failed to open %s\n", csv_path.string().c_str());
    return;
  }
  STDOUT_LOG("CSV log: %s\n", csv_path.string().c_str());
  // CSVヘッダー出力
  fprintf(csv_fp, "game_id,score,total_turns,stage,board_index,"
          "aerr_avg,aerr_std,err_avg,err_std,"
          "uc_avg,uc_std,uc_sum,"
          "uc0,uc1,uc2,uc3,uc4,uc5,uc6,uc7,"
          "ratio0,ratio1,ratio2,ratio3,ratio4,ratio5,ratio6,ratio7\n");
  // fflush(csv_fp);  // Removed for performance - OS buffering is sufficient
}

void closeCsvLog()
{
  if (csv_fp) {
    fclose(csv_fp);
  }
}

// ゲーム終了時に特定タプル・盤面の学習状態を記録
void logTupleStats(int game_id, int score, int total_turns, const int* board)
{
  if (!csv_fp) return;

  const int NUM_TRACKED = TRACKED_TUPLE_COUNT;
  
  // ステージ判定（固定盤面から判定）
  int s = 0;
  for (int i = 0; i < 9; i++) {
    if (FIXED_BOARD[i] >= 9) s = 1;
  }

  // 盤面インデックス計算（固定盤面を使用）
  int index = 0;
#if defined(USE_4TUPLE) || defined(NT4A)
  for (int k = 0; k < TUPLE_SIZE; k++) {
    index = index * VARIATION_TILE + FIXED_BOARD[pos[TRACKED_TUPLE_ID[0]][k]];
  }
#else
  for (int k = 0; k < NT6_notsym::TUPLE_SIZE; k++) {
    index = index * NT6_notsym::VARIATION_TILE +
            FIXED_BOARD[NT6_notsym::pos[TRACKED_TUPLE_ID[0]][k]];
  }
#endif

  // 各タプルの値を収集
  double aerr_vals[NUM_TRACKED];
  double err_vals[NUM_TRACKED];
  int uc_vals[NUM_TRACKED];
  double ratio_vals[NUM_TRACKED];
  
  double aerr_sum = 0.0, err_sum = 0.0, uc_sum = 0.0, ratio_sum = 0.0;
  
  for (int i = 0; i < NUM_TRACKED; i++) {
    const int tuple_id = TRACKED_TUPLE_ID[i];
    int tindex = 0;
#if defined(USE_4TUPLE) || defined(NT4A)
    for (int k = 0; k < TUPLE_SIZE; k++) {
      tindex = tindex * VARIATION_TILE + FIXED_BOARD[pos[tuple_id][k]];
    }
    aerr_vals[i] = aerrs[s][tuple_id][tindex];
    err_vals[i] = errs[s][tuple_id][tindex];
    uc_vals[i] = updatecounts[s][tuple_id][tindex];
#else
    for (int k = 0; k < NT6_notsym::TUPLE_SIZE; k++) {
      tindex = tindex * NT6_notsym::VARIATION_TILE +
               FIXED_BOARD[NT6_notsym::pos[tuple_id][k]];
    }
    aerr_vals[i] = NT6_notsym::aerrs[s][tuple_id][tindex];
    err_vals[i] = NT6_notsym::errs[s][tuple_id][tindex];
    uc_vals[i] = NT6_notsym::updatecounts[s][tuple_id][tindex];
#endif
    ratio_vals[i] = (aerr_vals[i] != 0) ? err_vals[i] / aerr_vals[i] : 0.0;
    
    aerr_sum += aerr_vals[i];
    err_sum += err_vals[i];
    uc_sum += uc_vals[i];
    ratio_sum += ratio_vals[i];
  }
  
  // 平均
  double aerr_avg = aerr_sum / NUM_TRACKED;
  double err_avg = err_sum / NUM_TRACKED;
  double uc_avg = uc_sum / NUM_TRACKED;
  double ratio_avg = ratio_sum / NUM_TRACKED;
  
  // 標準偏差
  double aerr_var = 0.0, err_var = 0.0, uc_var = 0.0, ratio_var = 0.0;
  for (int i = 0; i < NUM_TRACKED; i++) {
    aerr_var += (aerr_vals[i] - aerr_avg) * (aerr_vals[i] - aerr_avg);
    err_var += (err_vals[i] - err_avg) * (err_vals[i] - err_avg);
    uc_var += (uc_vals[i] - uc_avg) * (uc_vals[i] - uc_avg);
    ratio_var += (ratio_vals[i] - ratio_avg) * (ratio_vals[i] - ratio_avg);
  }
  double aerr_std = sqrt(aerr_var / NUM_TRACKED);
  double err_std = sqrt(err_var / NUM_TRACKED);
  double uc_std = sqrt(uc_var / NUM_TRACKED);
  double ratio_std = sqrt(ratio_var / NUM_TRACKED);
  
  // CSV出力
  fprintf(csv_fp, "%d,%d,%d,%d,%d,"
          "%.6f,%.6f,%.6f,%.6f,"
          "%.2f,%.2f,%6f,"
          "%d,%d,%d,%d,%d,%d,%d,%d,"
          "%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f\n",
          game_id, score, total_turns, s, index,
          aerr_avg, aerr_std, err_avg, err_std,
          uc_avg, uc_std,uc_sum,
          uc_vals[0], uc_vals[1], uc_vals[2], uc_vals[3],
          uc_vals[4], uc_vals[5], uc_vals[6], uc_vals[7],
          ratio_vals[0], ratio_vals[1], ratio_vals[2], ratio_vals[3],
          ratio_vals[4], ratio_vals[5], ratio_vals[6], ratio_vals[7]);
  // fflush(csv_fp);  // Removed for performance - buffered I/O is faster
}

void saveEvs()
{
  char filename[1024];
#if defined(USE_4TUPLE) || defined(NT4A)
  sprintf(filename, "4tuple_notsym_data_%d_%d.dat", global_seed, storage_c++);
#else
  sprintf(filename, "6tuple_notsym_data_%d_%d.dat", global_seed, storage_c++);
#endif
  fs::path dat_path = output_dir / filename;
  FILE *fp = fopen(dat_path.string().c_str(), "wb");
  if (!fp) {
    fprintf(stderr, "file %s open failed.\n", dat_path.string().c_str());
  }
#if defined(USE_4TUPLE) || defined(NT4A)
  writeEvs(fp);
#else
  NT6_notsym::writeEvs(fp);
#endif
  fclose(fp);
  STDOUT_LOG("stored %s\n", dat_path.string().c_str());
  if (storage_c == STORAGE_COUNT) exit(0);
}

int main(int argc, char* argv[])
{
  if (argc < 1+2) {
    fprintf(stderr, "Usage: learning_ntuple <seed> <run_name>\n");
    exit(1);
  }
  global_seed = atoi(argv[1]);
  run_name = argv[2];
  srand(global_seed);

  double init_ev = 0.0;
  if (const char* ev = getenv("INIT_EV"); ev && *ev) {
    init_ev = atof(ev);
  }

#if defined(USE_4TUPLE) || defined(NT4A)
  initEvs(init_ev);
#else
  NT6_notsym::initEvs(init_ev);
#endif

  const char* base = getenv("NTUPLE_DAT_ROOT");
  if (!base || !*base) {
    base = "/HDD/momiyama2/data/study/ntuple_dat";
  }
#if defined(USE_4TUPLE) || defined(NT4A)
  const char* tuple_dir = "NT4_notsym";
#else
  const char* tuple_dir = "NT6_notsym";
#endif
  output_dir =
      fs::path(base) / run_name / ("seed" + to_string(global_seed)) / tuple_dir;
  fs::create_directories(output_dir);

  openCsvLog();
  openBoardLog();

  // タプル情報の出力
  STDOUT_LOG("=== Loaded Tuples Information ===\n");
#if defined(USE_4TUPLE) || defined(NT4A)
  STDOUT_LOG("Number of tuples: %d\n", NUM_TUPLE);
  STDOUT_LOG("Tuple size: %d\n", TUPLE_SIZE);
  STDOUT_LOG("Number of stages: %d\n", NUM_STAGES);
  for (int i = 0; i < NUM_TUPLE; i++) {
    STDOUT_LOG("Tuple %d: [", i);
    for (int j = 0; j < TUPLE_SIZE; j++) {
      STDOUT_LOG("%d", pos[i][j]);
      if (j < TUPLE_SIZE - 1) STDOUT_LOG(", ");
#else
  STDOUT_LOG("Number of tuples: %d\n", NT6_notsym::NUM_TUPLE);
  STDOUT_LOG("Tuple size: %d\n", NT6_notsym::TUPLE_SIZE);
  STDOUT_LOG("Number of stages: %d\n", NT6_notsym::NUM_STAGES);
  for (int i = 0; i < NT6_notsym::NUM_TUPLE; i++) {
    STDOUT_LOG("Tuple %d: [", i);
    for (int j = 0; j < NT6_notsym::TUPLE_SIZE; j++) {
      STDOUT_LOG("%d", NT6_notsym::pos[i][j]);
      if (j < NT6_notsym::TUPLE_SIZE - 1) STDOUT_LOG(", ");
#endif
    }
    STDOUT_LOG("]\n");
  }
  STDOUT_LOG("=================================\n");
  // prev: printf("CSV log: tuple_learning_rate_log_notsym.csv\n\n");

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
#if defined(USE_4TUPLE) || defined(NT4A)
	  double ev_r = calcEv(copy.board) + (copy.score - state.score);
#else
	  double ev_r = NT6_notsym::calcEv(copy.board) + (copy.score - state.score);
#endif
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
#if defined(USE_4TUPLE) || defined(NT4A)
          update(lastboard, max_ev_r - calcEv(lastboard));
#else
          NT6_notsym::update(lastboard, max_ev_r - NT6_notsym::calcEv(lastboard));
#endif
	traincount++;
	if (traincount % STORAGE_FREQUENCY == 0) saveEvs();
      }
      for (int i = 0; i < 9; i++) {
	lastboard[i] = state.board[i];
      } 
    // 新しいタイル追加前の盤面を記録
    logBoard(gid+1, turn, state.score, state.board);
      putNewTile(&state);
     

      if (gameOver(state)) {
#if defined(USE_4TUPLE) || defined(NT4A)
          update(lastboard, 0 - calcEv(lastboard));
#else
          NT6_notsym::update(lastboard, 0 - NT6_notsym::calcEv(lastboard));
#endif
	traincount++;
	if (traincount % STORAGE_FREQUENCY == 0) saveEvs();
	STDOUT_LOG("game %d finished with score %d\n", gid+1, state.score);
          // ゲーム終了時に特定タプルの学習状態を記録
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
