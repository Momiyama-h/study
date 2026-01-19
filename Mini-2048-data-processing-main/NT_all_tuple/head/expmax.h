#include <algorithm>
#include <array>
#include <cfloat>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <list>
#include <numeric>
#include <string>
#include <unordered_map>
#include <vector>
int to_index(const int board[9]) {
  const static int rotate3[8][9] = {
      {0, 1, 2, 3, 4, 5, 6, 7, 8}, {2, 1, 0, 5, 4, 3, 8, 7, 6},
      {2, 5, 8, 1, 4, 7, 0, 3, 6}, {0, 3, 6, 1, 4, 7, 2, 5, 8},
      {8, 7, 6, 5, 4, 3, 2, 1, 0}, {6, 7, 8, 3, 4, 5, 0, 1, 2},
      {6, 3, 0, 7, 4, 1, 8, 5, 2}, {8, 5, 2, 7, 4, 1, 6, 3, 0}};
  const static long long pow11[9] = {1LL,       11LL,       121LL,
                                     1331LL,    14641LL,    161051LL,
                                     1771561LL, 19487171LL, 214358881LL};
  int index = INT_MAX;
  long long sindex0 = 0;
  for (int i = 0; i < 9; i++) {
    int j = rotate3[0][i];
    sindex0 += board[j] * pow11[i];
  }
  long long sindex1 = 0;
  for (int i = 0; i < 9; i++) {
    int j = rotate3[1][i];
    sindex1 += board[j] * pow11[i];
  }
  long long sindex2 = 0;
  for (int i = 0; i < 9; i++) {
    int j = rotate3[2][i];
    sindex2 += board[j] * pow11[i];
  }
  long long sindex3 = 0;
  for (int i = 0; i < 9; i++) {
    int j = rotate3[3][i];
    sindex3 += board[j] * pow11[i];
  }
  long long sindex4 = 0;
  for (int i = 0; i < 9; i++) {
    int j = rotate3[4][i];
    sindex4 += board[j] * pow11[i];
  }
  long long sindex5 = 0;
  for (int i = 0; i < 9; i++) {
    int j = rotate3[5][i];
    sindex5 += board[j] * pow11[i];
  }
  long long sindex6 = 0;
  for (int i = 0; i < 9; i++) {
    int j = rotate3[6][i];
    sindex6 += board[j] * pow11[i];
  }
  long long sindex7 = 0;
  for (int i = 0; i < 9; i++) {
    int j = rotate3[7][i];
    sindex7 += board[j] * pow11[i];
  }
  return std::min(
      {sindex0, sindex1, sindex2, sindex3, sindex4, sindex5, sindex6, sindex7});
}
long long exp_count = 0;

vector<unordered_map<int, double> > um(11, unordered_map<int, double>());

double move_expand(const state_t &state, int depth);
double input_expand(const state_t &state, int depth);

int expectimax(const state_t &state, int depth, double *evals) {
  // printf("====================\n");
  move_expand(state, depth);

  // 子の最大値をとる
  int selected = -1;
  double maxv = -DBL_MAX;
  for (int d = 0; d < 4; d++) {
    state_t copy;
    if (play(d, state, &copy)) {
      int index = to_index(copy.board);
      double v = um[depth - 1][index] + copy.score - state.score;
      evals[d] = v;
      // printf("move %d val %f\n", index, v);
      if (maxv < v) {
        selected = d;
        maxv = v;
      }
    }
  }
  // printf("selected move = %d\n", selected);
  for (int i = 0; i < depth; i++) um[i].clear();
  return selected;
}

double move_expand(const state_t &state, int depth) {
  // printf("At depth %d (move_expand): \n", depth); state.print();
  depth--;
  double maxv = -DBL_MAX;
  for (int d = 0; d < 4; d++) {
    state_t copy;
    if (play(d, state, &copy)) {
      double v = input_expand(copy, depth) + (copy.score - state.score);
      if (maxv < v) maxv = v;
    }
  }
  // Game over の扱い
  if (maxv == -DBL_MAX) maxv = 0;
  // printf("returning from move_expand depth %d: %f\n", depth, maxv);
  return maxv;
}

double input_expand(const state_t &state, int depth) {
  int index = to_index(state.board);
  // printf("At depth %d (input_expand): id = %d\n", depth, index);
  if (um[depth].find(index) != um[depth].end()) {
    // printf("cache hit: returing %f\n", um[depth][index]);
    exp_count++;
    return um[depth][index];
  }
  if (depth == 0) {
    um[depth][index] = calcEv(state.board);
    // printf("leaf: reurning %f\n", um[depth][index]);
    exp_count++;
    return um[depth][index];
  }
  double sum = 0;
  int count = 0;
  state_t copy = state.clone();
  for (int i = 0; i < 9; i++) {
    if (copy.board[i] == 0) {
      copy.board[i] = 1;
      sum += move_expand(copy, depth) * 9;
      copy.board[i] = 2;
      sum += move_expand(copy, depth);
      copy.board[i] = 0;
      count += 1;
    }
  }
  um[depth][index] = sum / (count * 10);
  // printf("from id = %d  returning %f\n", index, um[depth][index]);
  exp_count++;
  return um[depth][index];
}