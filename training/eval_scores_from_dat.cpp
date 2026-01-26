#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <cfloat>
#include <cstring>
#include <string>
#include <vector>

#include "Game2048_3_3.h"

#if defined(USE_4TUPLE)
#if defined(USE_NOSYM)
#include "4tuples_nosym.h"
static inline double eval_board(const int* board) { return calcEv(board); }
static inline void read_evs(FILE* fp) { readEvs(fp); }
#else
#include "4tuples_sym.h"
static inline double eval_board(const int* board) { return calcEv(board); }
static inline void read_evs(FILE* fp) { readEvs(fp); }
#endif
#else
#if defined(USE_NOSYM)
#include "6tuples_notsym.h"
static inline double eval_board(const int* board) {
  return NT6_notsym::calcEv(board);
}
static inline void read_evs(FILE* fp) { NT6_notsym::readEvs(fp); }
#else
#include "6tuples_sym.h"
static inline double eval_board(const int* board) { return calcEv(board); }
static inline void read_evs(FILE* fp) { readEvs(fp); }
#endif
#endif

struct Stats {
  int count = 0;
  double mean = 0.0;
  double m2 = 0.0;

  void add(double x) {
    count++;
    double delta = x - mean;
    mean += delta / count;
    double delta2 = x - mean;
    m2 += delta * delta2;
  }

  double stddev() const {
    if (count == 0) {
      return 0.0;
    }
    double var = m2 / count;
    return std::sqrt(var);
  }
};

static void usage(const char* prog) {
  std::fprintf(
      stderr,
      "Usage: %s <dat_path> <out_csv> [--games N] [--avescope N] [--seed N]\n",
      prog);
}

int main(int argc, char* argv[]) {
  if (argc < 3) {
    usage(argv[0]);
    return 1;
  }

  const char* dat_path = argv[1];
  const char* out_csv = argv[2];
  int games = 10000;
  int avescope = 1000;
  int seed = 0;

  for (int i = 3; i < argc; i++) {
    if (std::strcmp(argv[i], "--games") == 0 && i + 1 < argc) {
      games = std::atoi(argv[++i]);
    } else if (std::strcmp(argv[i], "--avescope") == 0 && i + 1 < argc) {
      avescope = std::atoi(argv[++i]);
    } else if (std::strcmp(argv[i], "--seed") == 0 && i + 1 < argc) {
      seed = std::atoi(argv[++i]);
    } else {
      std::fprintf(stderr, "Unknown option: %s\n", argv[i]);
      usage(argv[0]);
      return 1;
    }
  }

  if (games <= 0 || avescope <= 0) {
    std::fprintf(stderr, "games and avescope must be > 0\n");
    return 1;
  }

  FILE* fp = std::fopen(dat_path, "rb");
  if (!fp) {
    std::perror("fopen dat_path");
    return 1;
  }
  read_evs(fp);
  std::fclose(fp);

  if (seed != 0) {
    std::srand(seed);
  }

  int buckets = (games + avescope - 1) / avescope;
  std::vector<Stats> stats(buckets);

  for (int gid = 0; gid < games; gid++) {
    state_t state = initGame();

    while (true) {
      state_t copy;
      double max_ev_r = -DBL_MAX;
      int selected = -1;
      for (int d = 0; d < 4; d++) {
        if (play(d, state, &copy)) {
          double ev_r = eval_board(copy.board) + (copy.score - state.score);
          if (ev_r > max_ev_r) {
            max_ev_r = ev_r;
            selected = d;
          }
        }
      }
      if (selected == -1) {
        break;
      }
      play(selected, state, &state);
      putNewTile(&state);
      if (gameOver(state)) {
        break;
      }
    }

    int bucket = gid / avescope;
    stats[bucket].add(static_cast<double>(state.score));
  }

  FILE* out = std::fopen(out_csv, "w");
  if (!out) {
    std::perror("fopen out_csv");
    return 1;
  }
  std::fprintf(out, "start_game,end_game,avg_score,stddev,count\n");
  for (int i = 0; i < buckets; i++) {
    int start_game = i * avescope + 1;
    int end_game = (i + 1) * avescope;
    if (end_game > games) {
      end_game = games;
    }
    std::fprintf(out, "%d,%d,%.6f,%.6f,%d\n", start_game, end_game,
                 stats[i].mean, stats[i].stddev(), stats[i].count);
  }
  std::fclose(out);

  return 0;
}
