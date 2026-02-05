#pragma once

#include <cfloat>
#include <climits>
#include <unordered_map>
#include <vector>

#include "Game2048_3_3.h"

#ifndef EXPECTIMAX_PLY
#define EXPECTIMAX_PLY 3
#endif

#ifndef EXPECTIMAX_REWARD_WEIGHT
#define EXPECTIMAX_REWARD_WEIGHT 1.0
#endif

using EvalFn = double (*)(const int*);

static inline long long board_to_index_raw(const int board[9]) {
  static const long long pow11[9] = {
      1LL, 11LL, 121LL, 1331LL, 14641LL, 161051LL, 1771561LL, 19487171LL,
      214358881LL};
  long long id = 0;
  for (int i = 0; i < 9; i++) {
    id += (long long)board[i] * pow11[i];
  }
  return id;
}

static inline long long board_to_index_sym(const int board[9]) {
  static const int rotate3[8][9] = {
      {0, 1, 2, 3, 4, 5, 6, 7, 8},
      {2, 1, 0, 5, 4, 3, 8, 7, 6},
      {2, 5, 8, 1, 4, 7, 0, 3, 6},
      {0, 3, 6, 1, 4, 7, 2, 5, 8},
      {8, 7, 6, 5, 4, 3, 2, 1, 0},
      {6, 7, 8, 3, 4, 5, 0, 1, 2},
      {6, 3, 0, 7, 4, 1, 8, 5, 2},
      {8, 5, 2, 7, 4, 1, 6, 3, 0}};
  static const long long pow11[9] = {
      1LL, 11LL, 121LL, 1331LL, 14641LL, 161051LL, 1771561LL, 19487171LL,
      214358881LL};
  long long best = LLONG_MAX;
  for (int k = 0; k < 8; k++) {
    long long id = 0;
    for (int i = 0; i < 9; i++) {
      id += (long long)board[rotate3[k][i]] * pow11[i];
    }
    if (id < best) {
      best = id;
    }
  }
  return best;
}

static inline long long board_to_index(const int board[9], bool use_sym_cache) {
  return use_sym_cache ? board_to_index_sym(board) : board_to_index_raw(board);
}

static inline std::vector<std::unordered_map<long long, double>>&
expectimax_cache() {
  static std::vector<std::unordered_map<long long, double>> cache(
      EXPECTIMAX_PLY + 1);
  return cache;
}

static inline void clear_expectimax_cache() {
  for (auto& m : expectimax_cache()) {
    m.clear();
  }
}

static inline double move_expand(const state_t& state, int depth, EvalFn eval_fn,
                                 bool use_sym_cache);
static inline double input_expand(const state_t& state, int depth, EvalFn eval_fn,
                                  bool use_sym_cache);

static inline double move_expand(const state_t& state, int depth, EvalFn eval_fn,
                                 bool use_sym_cache) {
  depth--;
  double max_v = -DBL_MAX;
  state_t copy;
  for (int d = 0; d < 4; d++) {
    if (play(d, state, &copy)) {
      double v = input_expand(copy, depth, eval_fn, use_sym_cache) +
                 EXPECTIMAX_REWARD_WEIGHT * (copy.score - state.score);
      if (v > max_v) {
        max_v = v;
      }
    }
  }
  if (max_v == -DBL_MAX) {
    return 0.0;
  }
  return max_v;
}

static inline double input_expand(const state_t& state, int depth, EvalFn eval_fn,
                                  bool use_sym_cache) {
  auto& cache = expectimax_cache();
  const long long key = board_to_index(state.board, use_sym_cache);
  if (depth >= 0) {
    auto it = cache[depth].find(key);
    if (it != cache[depth].end()) {
      return it->second;
    }
  }
  if (depth == 0) {
    cache[depth][key] = eval_fn(state.board);
    return cache[depth][key];
  }

  double sum = 0.0;
  int count = 0;
  state_t copy = state;
  for (int i = 0; i < 9; i++) {
    if (copy.board[i] == 0) {
      copy.board[i] = 1;
      sum += move_expand(copy, depth, eval_fn, use_sym_cache) * 9.0;
      copy.board[i] = 2;
      sum += move_expand(copy, depth, eval_fn, use_sym_cache);
      copy.board[i] = 0;
      count += 1;
    }
  }
  double val = 0.0;
  if (count > 0) {
    val = sum / (count * 10.0);
  }
  if (depth >= 0) {
    cache[depth][key] = val;
  }
  return val;
}

static inline int select_move(const state_t& state, EvalFn eval_fn,
                              double evals_out[4], bool use_sym_cache) {
  clear_expectimax_cache();
  for (int d = 0; d < 4; d++) {
    evals_out[d] = -1.0e10;
  }
  const int depth = (EXPECTIMAX_PLY > 0) ? EXPECTIMAX_PLY : 1;
  move_expand(state, depth, eval_fn, use_sym_cache);

  double max_v = -DBL_MAX;
  int selected = -1;
  state_t copy;
  for (int d = 0; d < 4; d++) {
    if (play(d, state, &copy)) {
      const long long key = board_to_index(copy.board, use_sym_cache);
      double v = -DBL_MAX;
      if (depth - 1 >= 0) {
        auto it = expectimax_cache()[depth - 1].find(key);
        if (it != expectimax_cache()[depth - 1].end()) {
          v = it->second;
        }
      }
      v += EXPECTIMAX_REWARD_WEIGHT * (copy.score - state.score);
      evals_out[d] = v;
      if (v > max_v) {
        max_v = v;
        selected = d;
      }
    }
  }
  return selected;
}
