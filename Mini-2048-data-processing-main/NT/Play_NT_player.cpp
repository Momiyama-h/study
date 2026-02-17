// g++ Play_perfect_player.cevals -std=c++20 -mcmodel=large -O2
#include <array>
#include <cfloat>
#include <climits>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <iostream>
#include <list>
#include <unordered_map>
#include <vector>

namespace fs = std::filesystem;
using namespace std;

#include "4tuples_sym.h"
#include "4tuples_nosym.h"
#include "5tuples_sym.h"
#include "5tuples_notsym.h"
#include "6tuples_sym.h"
#include "6tuples_notsym.h"
#include "Game2048_3_3.h"
#include "fread.h"
#include "play_table.h"
#include "search_policy.h"

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

static constexpr int kSymPos[8][9] = {
    {0, 1, 2, 3, 4, 5, 6, 7, 8},
    {0, 3, 6, 1, 4, 7, 2, 5, 8},
    {2, 1, 0, 5, 4, 3, 8, 7, 6},
    {2, 5, 8, 1, 4, 7, 0, 3, 6},
    {6, 7, 8, 3, 4, 5, 0, 1, 2},
    {6, 3, 0, 7, 4, 1, 8, 5, 2},
    {8, 7, 6, 5, 4, 3, 2, 1, 0},
    {8, 5, 2, 7, 4, 1, 6, 3, 0},
};

static constexpr int kSymIdxIdentity[1] = {0};
static constexpr int kSymIdxDiag[2] = {0, 1};
static constexpr int kSymIdxRot180[2] = {0, 6};

static constexpr int kPosRot180Notsym4[] = {
    0, 1, 3, 4, 8, 7, 5, 4, 0, 3, 6, 7,
    8, 5, 2, 1, 1, 4, 7, 8, 7, 4, 1, 0,
};
static constexpr int kPosRotateNotsym4[] = {
    0, 1, 3, 4, 2, 5, 1, 4, 8, 7, 5, 4, 6, 3, 7, 4,
    0, 3, 6, 7, 2, 1, 0, 3, 8, 5, 2, 1, 6, 7, 8, 5,
    1, 4, 7, 8, 5, 4, 3, 6, 7, 4, 1, 0, 3, 4, 5, 2,
};
static constexpr int kPosRot180Notsym5[] = {
    0, 1, 2, 3, 4, 8, 7, 6, 5, 4, 0, 1, 3, 4, 5,
    8, 7, 5, 4, 3, 0, 1, 2, 3, 6, 8, 7, 6, 5, 2,
};
static constexpr int kPosRotateNotsym5[] = {
    0, 1, 2, 3, 4, 2, 5, 8, 1, 4, 8, 7, 6, 5, 4, 6, 3, 0, 7, 4,
    0, 1, 3, 4, 5, 2, 5, 1, 4, 7, 8, 7, 5, 4, 3, 6, 3, 7, 4, 1,
    0, 1, 2, 3, 6, 2, 5, 8, 1, 0, 8, 7, 6, 5, 2, 6, 3, 0, 7, 8,
};
static constexpr int kPosRot180Notsym6[] = {
    0, 1, 2, 3, 4, 5, 8, 7, 6, 5, 4, 3,
    0, 3, 4, 6, 7, 8, 8, 5, 4, 2, 1, 0,
};
static constexpr int kPosRotateNotsym6[] = {
    0, 1, 2, 3, 4, 5, 2, 5, 8, 1, 4, 7, 8, 7, 6, 5, 4, 3,
    6, 3, 0, 7, 4, 1, 0, 3, 4, 6, 7, 8, 2, 1, 4, 0, 3, 6,
    8, 5, 4, 2, 1, 0, 6, 7, 4, 8, 5, 2,
};

static constexpr int kPosDiagNotsym4[] = {
    0, 1, 3, 4, 0, 3, 1, 4, 0, 3, 6, 7,
    0, 1, 2, 5, 1, 4, 7, 8, 3, 4, 5, 8,
};
static constexpr int kPosDiagNotsym5[] = {
    0, 1, 2, 3, 4, 0, 3, 6, 1, 4, 0, 1, 3, 4, 5,
    0, 3, 1, 4, 7, 0, 1, 2, 3, 6, 0, 3, 6, 1, 2,
};
static constexpr int kPosDiagNotsym6[] = {
    0, 1, 2, 3, 4, 5, 0, 3, 6, 1, 4, 7,
    0, 3, 4, 6, 7, 8, 0, 1, 4, 2, 5, 8,
};

struct DynamicEval {
  int tuple_size = 0;
  int num_tuple = 0;
  int array_length = 0;
  const int* pos_flat = nullptr;
  const int* sym_indices = nullptr;
  int sym_count = 1;
  std::vector<double> evs;
  bool loaded = false;

  double eval(const int* board, bool force_stage0) const {
    if (!loaded) return 0.0;
    int s = 0;
#ifndef SINGLE_STAGE
    if (!force_stage0) {
      for (int i = 0; i < 9; i++) {
        if (board[i] >= 9) {
          s = 1;
          break;
        }
      }
    }
#endif
    const size_t stage_offset =
        static_cast<size_t>(s) * static_cast<size_t>(num_tuple) *
        static_cast<size_t>(array_length);
    double ev = 0.0;
    for (int i = 0; i < num_tuple; i++) {
      const int* tuple_pos = pos_flat + (i * tuple_size);
      for (int r = 0; r < sym_count; r++) {
        const int sym = sym_indices[r];
        int index = 0;
        for (int k = 0; k < tuple_size; k++) {
          index = index * 11 + board[kSymPos[sym][tuple_pos[k]]];
        }
        ev += evs[stage_offset + static_cast<size_t>(i) *
                                static_cast<size_t>(array_length) +
                  static_cast<size_t>(index)];
      }
    }
    return ev;
  }
};

static DynamicEval g_dynamic_eval;

static bool load_dynamic_evs(FILE* fp, int tuple_size, int num_tuple,
                             const int* pos_flat, const int* sym_indices,
                             int sym_count) {
  DynamicEval next;
  next.tuple_size = tuple_size;
  next.num_tuple = num_tuple;
  next.pos_flat = pos_flat;
  next.sym_indices = sym_indices;
  next.sym_count = sym_count;
  next.array_length = 1;
  for (int i = 0; i < tuple_size; i++) {
    next.array_length *= 11;
  }
  const size_t total =
      static_cast<size_t>(2) * static_cast<size_t>(num_tuple) *
      static_cast<size_t>(next.array_length);
  next.evs.resize(total);
  const size_t count = fread(next.evs.data(), sizeof(double), total, fp);
  if (count != total) {
    fprintf(stderr,
            "Error: failed to read dynamic ev table (read=%zu, expect=%zu)\n",
            count, total);
    return false;
  }
  next.loaded = true;
  g_dynamic_eval = std::move(next);
  return true;
}

static double calcEv_dynamic(const int* board) {
  return g_dynamic_eval.eval(board, false);
}

static double calcEv_dynamic_stage0(const int* board) {
  return g_dynamic_eval.eval(board, true);
}

static double calcEv_stage0_nt4_sym(const int* board) {
  const int s = 0;
  double ev = 0;
  for (int i = 0; i < NT4::NUM_TUPLE; i++) {
    for (int j = 0; j < 8; j++) {
      int index = 0;
      for (int k = 0; k < NT4::TUPLE_SIZE; k++) {
        index = index * NT4::VARIATION_TILE +
                board[NT4::sympos[j][NT4::pos[i][k]]];
      }
      ev += NT4::evs[s][i][index];
    }
  }
  return ev;
}

static double calcEv_stage0_nt5_sym(const int* board) {
  const int s = 0;
  double ev = 0;
  for (int i = 0; i < NT5::NUM_TUPLE; i++) {
    for (int j = 0; j < 8; j++) {
      int index = 0;
      for (int k = 0; k < NT5::TUPLE_SIZE; k++) {
        index = index * NT5::VARIATION_TILE +
                board[NT5::sympos[j][NT5::pos[i][k]]];
      }
      ev += NT5::evs[s][i][index];
    }
  }
  return ev;
}

static double calcEv_stage0_nt6_sym(const int* board) {
  const int s = 0;
  double ev = 0;
  for (int i = 0; i < NT6::NUM_TUPLE; i++) {
    for (int j = 0; j < 8; j++) {
      int index = 0;
      for (int k = 0; k < NT6::TUPLE_SIZE; k++) {
        index = index * NT6::VARIATION_TILE +
                board[NT6::sympos[j][NT6::pos[i][k]]];
      }
      ev += NT6::evs[s][i][index];
    }
  }
  return ev;
}

static double calcEv_stage0_nt4_notsym(const int* board) {
  const int s = 0;
  double ev = 0;
  for (int i = 0; i < NT4_notsym::NUM_TUPLE; i++) {
    const int j = 0;
    int index = 0;
    for (int k = 0; k < NT4_notsym::TUPLE_SIZE; k++) {
      index = index * NT4_notsym::VARIATION_TILE +
              board[NT4_notsym::sympos[j][NT4_notsym::pos[i][k]]];
    }
    ev += NT4_notsym::evs[s][i][index];
  }
  return ev;
}

static double calcEv_stage0_nt5_notsym(const int* board) {
  const int s = 0;
  double ev = 0;
  for (int i = 0; i < NT5_notsym::NUM_TUPLE; i++) {
    int index = 0;
    for (int k = 0; k < NT5_notsym::TUPLE_SIZE; k++) {
      index = index * NT5_notsym::VARIATION_TILE +
              board[NT5_notsym::sympos[0][NT5_notsym::pos[i][k]]];
    }
    ev += NT5_notsym::evs[s][i][index];
  }
  return ev;
}

static double calcEv_stage0_nt6_notsym(const int* board) {
  const int s = 0;
  double ev = 0;
  for (int i = 0; i < NT6_notsym::NUM_TUPLE; i++) {
    int index = 0;
    for (int k = 0; k < NT6_notsym::TUPLE_SIZE; k++) {
      index = index * NT6_notsym::VARIATION_TILE +
              board[NT6_notsym::pos[i][k]];
    }
    ev += NT6_notsym::evs[s][i][index];
  }
  return ev;
}
int main(int argc, char** argv) {
  if (argc < 2 + 1) {
    fprintf(stderr, "Usage: playgreedy <seed> <game_counts> <evfile> [sym|notsym|rot180|rot180_notsym|diag|diag_notsym] [4|5|6] [--run-name NAME] [--board-root PATH] [--eval-seed N] [--single-stage|--nostage]\n");
    exit(1);
  }
  int seed = atoi(argv[1]);
  int eval_seed = seed;
  bool eval_seed_set = false;
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
  string run_name;
  string board_root;
  bool single_stage = false;
  for (int i = 4; i < argc; i++) {
    string opt = argv[i];
    if (opt == "sym" || opt == "notsym" || opt == "rotate" ||
        opt == "rot180" || opt == "diag" || opt == "rotate_notsym" ||
        opt == "rot180_notsym" || opt == "diag_notsym") {
      symmetry = opt;
      symmetry_set = true;
    } else if (opt == "4" || opt == "5" || opt == "6") {
      number = opt;
      number_set = true;
    } else if (opt == "--run-name") {
      if (i + 1 >= argc) {
        fprintf(stderr, "Error: --run-name requires a value\n");
        exit(1);
      }
      run_name = argv[++i];
    } else if (opt.rfind("--run-name=", 0) == 0) {
      run_name = opt.substr(strlen("--run-name="));
    } else if (opt == "--board-root") {
      if (i + 1 >= argc) {
        fprintf(stderr, "Error: --board-root requires a value\n");
        exit(1);
      }
      board_root = argv[++i];
    } else if (opt.rfind("--board-root=", 0) == 0) {
      board_root = opt.substr(strlen("--board-root="));
    } else if (opt == "--eval-seed") {
      if (i + 1 >= argc) {
        fprintf(stderr, "Error: --eval-seed requires a value\n");
        exit(1);
      }
      eval_seed = atoi(argv[++i]);
      eval_seed_set = true;
    } else if (opt.rfind("--eval-seed=", 0) == 0) {
      eval_seed = atoi(opt.substr(strlen("--eval-seed=")).c_str());
      eval_seed_set = true;
    } else if (opt == "--single-stage" || opt == "--nostage") {
      single_stage = true;
    } else {
      fprintf(stderr, "Error: unknown option: %s\n", opt.c_str());
      exit(1);
    }
  }
  if (!single_stage && !run_name.empty()) {
    if (run_name.find("nostage") != string::npos) {
      single_stage = true;
    }
  }
  if (!symmetry_set) {
    if (basename.find("rot180_notsym") != string::npos) {
      symmetry = "rot180_notsym";
    } else if (basename.find("diag_notsym") != string::npos) {
      symmetry = "diag_notsym";
    } else if (basename.find("rotate_notsym") != string::npos) {
      symmetry = "rotate_notsym";
    } else if (basename.find("rot180") != string::npos) {
      symmetry = "rot180";
    } else if (basename.find("diag") != string::npos) {
      symmetry = "diag";
    } else if (basename.find("rotate") != string::npos) {
      symmetry = "rotate";
    } else if (basename.find("notsym") != string::npos ||
               basename.find("nosym") != string::npos) {
      symmetry = "notsym";
    }
  }
  if (!number_set) {
    if (!basename.empty() && (basename[0] == '4' || basename[0] == '5' || basename[0] == '6')) {
      number = string(1, basename[0]);
    } else {
      fprintf(stderr, "Error: evfile must start with '4', '5' or '6': %s\n", basename.c_str());
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
  } else if (!board_root.empty()) {
    base_root = board_root;
  }
  if (!run_name.empty() && (base_env == nullptr || !*base_env)) {
    base_root = base_root + "/" + run_name + "/seed" + to_string(seed);
  }
  fs::create_directories(base_root);
  string dir = base_root + "/NT" + number + "_" + symmetry + "/";
  if (eval_seed_set) {
    dir += "eval_seed" + to_string(eval_seed) + "/";
  }
  fs::create_directories(dir);

  double average = 0;
  FILE* fp = fopen(evfile, "rb");
  if (fp == NULL) {
    fprintf(stderr, "cannot open file: %s\n", evfile);
    exit(1);
  }
  bool use_dynamic_eval = false;
  if (number == "4") {
    if (symmetry == "sym") {
      NT4::readEvs(fp);
    } else if (symmetry == "notsym") {
      NT4_notsym::readEvs(fp);
    } else if (symmetry == "rot180" || symmetry == "rotate") {
      use_dynamic_eval = load_dynamic_evs(fp, NT4::TUPLE_SIZE, NT4::NUM_TUPLE,
                                          &NT4::pos[0][0], kSymIdxRot180, 2);
    } else if (symmetry == "diag") {
      use_dynamic_eval = load_dynamic_evs(fp, NT4::TUPLE_SIZE, NT4::NUM_TUPLE,
                                          &NT4::pos[0][0], kSymIdxDiag, 2);
    } else if (symmetry == "rotate_notsym") {
      use_dynamic_eval = load_dynamic_evs(fp, 4, 12, kPosRotateNotsym4,
                                          kSymIdxIdentity, 1);
    } else if (symmetry == "rot180_notsym") {
      use_dynamic_eval = load_dynamic_evs(fp, 4, 6, kPosRot180Notsym4,
                                          kSymIdxIdentity, 1);
    } else if (symmetry == "diag_notsym") {
      use_dynamic_eval = load_dynamic_evs(fp, 4, 6, kPosDiagNotsym4,
                                          kSymIdxIdentity, 1);
    }
  } else if (number == "5") {
    if (symmetry == "sym") {
      NT5::readEvs(fp);
    } else if (symmetry == "notsym") {
      NT5_notsym::readEvs(fp);
    } else if (symmetry == "rot180" || symmetry == "rotate") {
      use_dynamic_eval = load_dynamic_evs(fp, NT5::TUPLE_SIZE, NT5::NUM_TUPLE,
                                          &NT5::pos[0][0], kSymIdxRot180, 2);
    } else if (symmetry == "diag") {
      use_dynamic_eval = load_dynamic_evs(fp, NT5::TUPLE_SIZE, NT5::NUM_TUPLE,
                                          &NT5::pos[0][0], kSymIdxDiag, 2);
    } else if (symmetry == "rotate_notsym") {
      use_dynamic_eval = load_dynamic_evs(fp, 5, 12, kPosRotateNotsym5,
                                          kSymIdxIdentity, 1);
    } else if (symmetry == "rot180_notsym") {
      use_dynamic_eval = load_dynamic_evs(fp, 5, 6, kPosRot180Notsym5,
                                          kSymIdxIdentity, 1);
    } else if (symmetry == "diag_notsym") {
      use_dynamic_eval = load_dynamic_evs(fp, 5, 6, kPosDiagNotsym5,
                                          kSymIdxIdentity, 1);
    }
  } else {
    if (symmetry == "sym") {
      NT6::readEvs(fp);
    } else if (symmetry == "notsym") {
      NT6_notsym::readEvs(fp);
    } else if (symmetry == "rot180" || symmetry == "rotate") {
      use_dynamic_eval = load_dynamic_evs(fp, NT6::TUPLE_SIZE, NT6::NUM_TUPLE,
                                          &NT6::pos[0][0], kSymIdxRot180, 2);
    } else if (symmetry == "diag") {
      use_dynamic_eval = load_dynamic_evs(fp, NT6::TUPLE_SIZE, NT6::NUM_TUPLE,
                                          &NT6::pos[0][0], kSymIdxDiag, 2);
    } else if (symmetry == "rotate_notsym") {
      use_dynamic_eval = load_dynamic_evs(fp, 6, 8, kPosRotateNotsym6,
                                          kSymIdxIdentity, 1);
    } else if (symmetry == "rot180_notsym") {
      use_dynamic_eval = load_dynamic_evs(fp, 6, 4, kPosRot180Notsym6,
                                          kSymIdxIdentity, 1);
    } else if (symmetry == "diag_notsym") {
      use_dynamic_eval = load_dynamic_evs(fp, 6, 4, kPosDiagNotsym6,
                                          kSymIdxIdentity, 1);
    }
  }
  fclose(fp);
  if ((symmetry != "sym" && symmetry != "notsym") && !use_dynamic_eval) {
    fprintf(stderr, "Error: unsupported mode or ev read failed: %s\n",
            symmetry.c_str());
    exit(1);
  }
  srand(eval_seed);

  double (*eval_fn)(const int*) = nullptr;
  if (number == "4") {
    if (symmetry == "sym") {
      eval_fn = single_stage ? calcEv_stage0_nt4_sym : NT4::calcEv;
    } else if (symmetry == "notsym") {
      eval_fn = single_stage ? calcEv_stage0_nt4_notsym : NT4_notsym::calcEv;
    } else {
      eval_fn = single_stage ? calcEv_dynamic_stage0 : calcEv_dynamic;
    }
  } else if (number == "5") {
    if (symmetry == "sym") {
      eval_fn = single_stage ? calcEv_stage0_nt5_sym : NT5::calcEv;
    } else if (symmetry == "notsym") {
      eval_fn = single_stage ? calcEv_stage0_nt5_notsym : NT5_notsym::calcEv;
    } else {
      eval_fn = single_stage ? calcEv_dynamic_stage0 : calcEv_dynamic;
    }
  } else if (number == "6") {
    if (symmetry == "sym") {
      eval_fn = single_stage ? calcEv_stage0_nt6_sym : NT6::calcEv;
    } else if (symmetry == "notsym") {
      eval_fn = single_stage ? calcEv_stage0_nt6_notsym : NT6_notsym::calcEv;
    } else {
      eval_fn = single_stage ? calcEv_dynamic_stage0 : calcEv_dynamic;
    }
  }
  if (eval_fn == nullptr) {
    fprintf(stderr, "Error: eval function not set for number=%s symmetry=%s\n",
            number.c_str(), symmetry.c_str());
    exit(1);
  }
  const bool use_sym_cache = (symmetry == "sym");
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
      const int n = 5;
      double evals[n];
      int selected = select_move(state, eval_fn, evals, use_sym_cache);
      if (selected == -1) {
        fprintf(stderr, "Something wrong. No direction played.\n");
      }
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
