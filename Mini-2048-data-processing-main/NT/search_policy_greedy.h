#pragma once

#include <cfloat>

#include "Game2048_3_3.h"

using EvalFn = double (*)(const int*);

static inline int select_move(const state_t& state, EvalFn eval_fn,
                              double evals_out[4], bool /*use_sym_cache*/) {
  double max_v = -DBL_MAX;
  int selected = -1;
  for (int d = 0; d < 4; d++) {
    evals_out[d] = -1.0e10;
  }
  state_t copy;
  for (int d = 0; d < 4; d++) {
    if (play(d, state, &copy)) {
      double v = eval_fn(copy.board);
      evals_out[d] = v;
      if (v > max_v) {
        max_v = v;
        selected = d;
      }
    }
  }
  return selected;
}
