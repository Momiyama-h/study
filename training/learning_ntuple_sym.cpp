#include <cstdio>
#include <cstdlib>
#include <cfloat>
#include <climits>
#include <cmath>
#include <ctime>
#include <time.h>
#include <unistd.h>
#include <chrono>
#include <random>
#include <filesystem>
#include <string>
using namespace std;
namespace fs = std::filesystem;

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
#define STORAGE_FREQUENCY (5*10000000LL)
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
#ifndef ENABLE_SCORE_LOG
#define ENABLE_SCORE_LOG 1
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
FILE *score_log_fp = nullptr;
static uint64_t process_cpu_start_ns = 0;
static uint64_t block_cpu_start_ns = 0;
static uint64_t cpu_ns_eval_block = 0;
static uint64_t cpu_ns_update_block = 0;
static std::chrono::steady_clock::time_point process_wall_start;
static std::chrono::steady_clock::time_point block_wall_start;

static inline uint64_t now_cpu_ns_process()
{
  timespec ts{};
  clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &ts);
  return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

struct CpuAccum {
  uint64_t &acc;
  uint64_t st;
  explicit CpuAccum(uint64_t &a) : acc(a), st(now_cpu_ns_process()) {}
  ~CpuAccum() { acc += (now_cpu_ns_process() - st); }
};
static fs::path output_dir;
static string run_name;

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

void openScoreLog(const char* condition)
{
#if !ENABLE_SCORE_LOG
  return;
#endif
  const int pid = (int)getpid();
  char fname[256];
  snprintf(fname, sizeof(fname), "log_score_%s_seed%d_pid%d.csv",
           condition, global_seed, pid);
  fs::path score_path = output_dir / fname;
  score_log_fp = fopen(score_path.string().c_str(), "w");
  if (!score_log_fp) {
    fprintf(stderr, "Failed to open %s\n", score_path.string().c_str());
    return;
  }
  fprintf(score_log_fp,
          "condition,seed,pid,games_total,block_games,traincount_total,"
          "score_mean,score_sd,score_min,score_max,"
          "cpu_sec_total,cpu_sec_block,cpu_sec_eval,cpu_sec_update,cpu_sec_other,share_update,"
          "wall_sec_total,wall_sec_block\n");
}

void closeScoreLog()
{
  if (score_log_fp) {
    fclose(score_log_fp);
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
  sprintf(filename, "tuple_learning_rate_log_seed%d_%04d%02d%02d%02d%02d%s.csv",
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
  fs::path dat_path = output_dir / filename;
  FILE *fp = fopen(dat_path.string().c_str(), "wb");
  if (!fp) {
    fprintf(stderr, "file %s open failed.\n", dat_path.string().c_str());
  }
  writeEvs(fp);
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

  const char* base = getenv("NTUPLE_DAT_ROOT");
  if (!base || !*base) {
    base = "/HDD/momiyama2/data/study/ntuple_dat";
  }
#if defined(USE_4TUPLE) || defined(NT4A)
  const char* tuple_dir = "NT4_sym";
#else
  const char* tuple_dir = "NT6_sym";
#endif
  output_dir =
      fs::path(base) / run_name / ("seed" + to_string(global_seed)) / tuple_dir;
  fs::create_directories(output_dir);

  initEvs(init_ev);
  openCsvLog();
  openBoardLog();
  const char* condition =
#if defined(USE_4TUPLE) || defined(NT4A)
      "nt4_sym";
#else
      "nt6_sym";
#endif
  openScoreLog(condition);
  process_cpu_start_ns = now_cpu_ns_process();
  block_cpu_start_ns = process_cpu_start_ns;
  process_wall_start = std::chrono::steady_clock::now();
  block_wall_start = process_wall_start;
  cpu_ns_eval_block = 0;
  cpu_ns_update_block = 0;

  int traincount = 0;
  long long score_sum = 0;
  long long score_sumsq = 0;
  int score_min = INT_MAX;
  int score_max = INT_MIN;
  int block_games = 0;
  int total_games = 0;
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
	  double ev_r = 0.0;
	  {
	    CpuAccum acc(cpu_ns_eval_block);
	    ev_r = calcEv(copy.board) + (copy.score - state.score);
	  }
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
	{
	  CpuAccum acc(cpu_ns_update_block);
	  double target = 0.0;
	  {
	    CpuAccum acc_eval(cpu_ns_eval_block);
	    target = max_ev_r - calcEv(lastboard);
	  }
	  update(lastboard, target);
	}
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
	{
	  CpuAccum acc(cpu_ns_update_block);
	  double target = 0.0;
	  {
	    CpuAccum acc_eval(cpu_ns_eval_block);
	    target = 0 - calcEv(lastboard);
	  }
	  update(lastboard, target);
	}
	traincount++;
	if (traincount % STORAGE_FREQUENCY == 0) saveEvs();
	STDOUT_LOG("game %d finished with score %d\n", gid+1, state.score);
	// ゲーム終了時に学習率を記録
	logTupleStats(gid+1, state.score, turn, lastboard);
        score_sum += state.score;
        score_sumsq += 1LL * state.score * state.score;
        if (state.score < score_min) score_min = state.score;
        if (state.score > score_max) score_max = state.score;
        block_games++;
        total_games++;
        if (block_games == 10000 && score_log_fp) {
          const double n = (double)block_games;
          const double mean = n > 0 ? (double)score_sum / n : 0.0;
          double var = 0.0;
          if (block_games >= 2) {
            var = ((double)score_sumsq - (double)score_sum * (double)score_sum / n) / (n - 1.0);
            if (var < 0.0) var = 0.0;
          }
          const double sd = sqrt(var);

          const uint64_t block_cpu_end = now_cpu_ns_process();
          const double cpu_sec_total =
              (double)(block_cpu_end - process_cpu_start_ns) / 1e9;
          const double cpu_sec_block =
              (double)(block_cpu_end - block_cpu_start_ns) / 1e9;
          const double cpu_sec_eval = (double)cpu_ns_eval_block / 1e9;
          const double cpu_sec_update = (double)cpu_ns_update_block / 1e9;
          double cpu_sec_other = cpu_sec_block - cpu_sec_eval - cpu_sec_update;
          if (cpu_sec_other < 0.0) cpu_sec_other = 0.0;
          const double share_update =
              (cpu_sec_block > 0.0) ? (cpu_sec_update / cpu_sec_block) : 0.0;

          const auto wall_now = std::chrono::steady_clock::now();
          const double wall_sec_total =
              std::chrono::duration<double>(wall_now - process_wall_start).count();
          const double wall_sec_block =
              std::chrono::duration<double>(wall_now - block_wall_start).count();

          fprintf(score_log_fp,
                  "%s,%d,%d,%d,%d,%d,%.6f,%.6f,%d,%d,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f\n",
                  condition, global_seed, (int)getpid(),
                  total_games, block_games, traincount,
                  mean, sd, score_min, score_max,
                  cpu_sec_total, cpu_sec_block, cpu_sec_eval, cpu_sec_update,
                  cpu_sec_other, share_update, wall_sec_total, wall_sec_block);

          score_sum = 0;
          score_sumsq = 0;
          score_min = INT_MAX;
          score_max = INT_MIN;
          block_games = 0;
          cpu_ns_eval_block = 0;
          cpu_ns_update_block = 0;
          block_cpu_start_ns = now_cpu_ns_process();
          block_wall_start = std::chrono::steady_clock::now();
        }
	break;
      }
    }
  }

  closeCsvLog();
  closeBoardLog();
  closeScoreLog();
  fprintf(stderr, "Training finished before saving %d data\n", STORAGE_COUNT);
  return 0;
}
