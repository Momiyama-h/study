#include <algorithm>
#include <cfloat>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

// Mode selection:
//   -DMODE_SYM_LIKE
//   -DMODE_NOTSYM
//   -DMODE_ROTATE_NOTSYM
//   -DMODE_ROT180_NOTSYM
//   -DMODE_DIAG_NOTSYM
//
// Tuple selection:
//   -DUSE_4TUPLE or -DUSE_5TUPLE (6tuple is default)
// Optional:
//   -DNT4A

#if defined(MODE_SYM_LIKE)
#if defined(USE_5TUPLE)
#include "5tuples_sym.h"
#elif defined(USE_4TUPLE) || defined(NT4A)
#include "4tuples_sym.h"
#else
#include "6tuples_sym.h"
#endif
static inline void read_evs(FILE* fp) { readEvs(fp); }
static inline int get_updatecount(int s, int t, int idx) { return updatecounts[s][t][idx]; }
static constexpr int kNumStages = NUM_STAGES;
static constexpr int kNumTuple = NUM_TUPLE;
static constexpr int kArrayLength = ARRAY_LENGTH;

#elif defined(MODE_NOTSYM)
#if defined(USE_5TUPLE)
#include "5tuples_notsym.h"
static inline void read_evs(FILE* fp) { readEvs(fp); }
static inline int get_updatecount(int s, int t, int idx) { return updatecounts[s][t][idx]; }
static constexpr int kNumStages = NUM_STAGES;
static constexpr int kNumTuple = NUM_TUPLE;
static constexpr int kArrayLength = ARRAY_LENGTH;
#elif defined(USE_4TUPLE) || defined(NT4A)
#include "4tuples_nosym.h"
static inline void read_evs(FILE* fp) { readEvs(fp); }
static inline int get_updatecount(int s, int t, int idx) { return updatecounts[s][t][idx]; }
static constexpr int kNumStages = NUM_STAGES;
static constexpr int kNumTuple = NUM_TUPLE;
static constexpr int kArrayLength = ARRAY_LENGTH;
#else
#include "6tuples_notsym.h"
static inline void read_evs(FILE* fp) { NT6_notsym::readEvs(fp); }
static inline int get_updatecount(int s, int t, int idx) { return NT6_notsym::updatecounts[s][t][idx]; }
static constexpr int kNumStages = NT6_notsym::NUM_STAGES;
static constexpr int kNumTuple = NT6_notsym::NUM_TUPLE;
static constexpr int kArrayLength = NT6_notsym::ARRAY_LENGTH;
#endif

#elif defined(MODE_ROTATE_NOTSYM)
#include "tuples_notsym_rotate.h"
static inline void read_evs(FILE* fp) { readEvs(fp); }
static inline int get_updatecount(int s, int t, int idx) { return updatecounts[s][t][idx]; }
static constexpr int kNumStages = NUM_STAGES;
static constexpr int kNumTuple = NUM_TUPLE;
static constexpr int kArrayLength = ARRAY_LENGTH;

#elif defined(MODE_ROT180_NOTSYM)
#include "tuples_notsym_rot180.h"
static inline void read_evs(FILE* fp) { readEvs(fp); }
static inline int get_updatecount(int s, int t, int idx) { return updatecounts[s][t][idx]; }
static constexpr int kNumStages = NUM_STAGES;
static constexpr int kNumTuple = NUM_TUPLE;
static constexpr int kArrayLength = ARRAY_LENGTH;

#elif defined(MODE_DIAG_NOTSYM)
#include "tuples_notsym_diag.h"
static inline void read_evs(FILE* fp) { readEvs(fp); }
static inline int get_updatecount(int s, int t, int idx) { return updatecounts[s][t][idx]; }
static constexpr int kNumStages = NUM_STAGES;
static constexpr int kNumTuple = NUM_TUPLE;
static constexpr int kArrayLength = ARRAY_LENGTH;

#else
#error "Please define one mode macro (MODE_SYM_LIKE / MODE_NOTSYM / MODE_ROTATE_NOTSYM / MODE_ROT180_NOTSYM / MODE_DIAG_NOTSYM)."
#endif

struct Cell {
  int tuple_id;
  int index;
  int count;
};

static void usage(const char* prog) {
  std::fprintf(stderr, "Usage: %s <dat_path> <table_stage|all> [top_k]\n", prog);
}

int main(int argc, char* argv[]) {
  if (argc < 3) {
    usage(argv[0]);
    return 1;
  }

  const char* dat_path = argv[1];
  const char* stage_arg = argv[2];
  bool use_all_stages = false;
  int stage = 0;
  if (std::strcmp(stage_arg, "all") == 0 || std::strcmp(stage_arg, "ALL") == 0) {
    use_all_stages = true;
  } else {
    stage = std::atoi(stage_arg);
  }
  int top_k = (argc >= 4) ? std::atoi(argv[3]) : 20;
  if (top_k <= 0) top_k = 20;

  if (!use_all_stages && (stage < 0 || stage >= kNumStages)) {
    std::fprintf(stderr, "ERROR: stage out of range: %d (valid: 0..%d)\n", stage, kNumStages - 1);
    return 2;
  }

  FILE* fp = std::fopen(dat_path, "rb");
  if (!fp) {
    std::perror("fopen");
    return 3;
  }
  read_evs(fp);
  std::fclose(fp);

  std::vector<Cell> best;
  best.reserve(static_cast<size_t>(top_k) + 1);

  auto less_count = [](const Cell& a, const Cell& b) {
    if (a.count != b.count) return a.count < b.count;
    if (a.tuple_id != b.tuple_id) return a.tuple_id > b.tuple_id;
    return a.index > b.index;
  };

  for (int t = 0; t < kNumTuple; ++t) {
    for (int idx = 0; idx < kArrayLength; ++idx) {
      int c = 0;
      if (use_all_stages) {
        for (int s = 0; s < kNumStages; ++s) {
          c += get_updatecount(s, t, idx);
        }
      } else {
        c = get_updatecount(stage, t, idx);
      }
      Cell cur{t, idx, c};
      if (static_cast<int>(best.size()) < top_k) {
        best.push_back(cur);
        std::push_heap(best.begin(), best.end(), less_count);
      } else if (!best.empty() && (c > best.front().count)) {
        std::pop_heap(best.begin(), best.end(), less_count);
        best.back() = cur;
        std::push_heap(best.begin(), best.end(), less_count);
      }
    }
  }

  std::sort(best.begin(), best.end(), [](const Cell& a, const Cell& b) {
    if (a.count != b.count) return a.count > b.count;
    if (a.tuple_id != b.tuple_id) return a.tuple_id < b.tuple_id;
    return a.index < b.index;
  });

  std::printf("dat_path: %s\n", dat_path);
  if (use_all_stages) {
    std::printf("table_stage: all (sum over 0..%d)\n", kNumStages - 1);
  } else {
    std::printf("table_stage: %d\n", stage);
  }
  std::printf("shape: NUM_TUPLE=%d ARRAY_LENGTH=%d\n", kNumTuple, kArrayLength);
  std::printf("top_k: %d\n\n", top_k);
  std::printf("rank,tuple_id,index,updatecount\n");
  for (size_t i = 0; i < best.size(); ++i) {
    std::printf("%zu,%d,%d,%d\n", i + 1, best[i].tuple_id, best[i].index, best[i].count);
  }

  return 0;
}
