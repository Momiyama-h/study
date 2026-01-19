#pragma once

#include "Game2048_3_3.h"
#include "common_defines.h"
#include "save.h"

class LearningBase {
 protected:
  long long traincount = 0;
  const long long STORAGE_FREQUENCY = (5 * 10000000);
  const long long STORAGE_COUNT = 1;
  const long long MAX_GAMES = 1000000000;
  int storage_c = 0;

  // デバッグ用のフラグ
  bool debug_mode = false;

  void debugPrint(const char* format, ...) {
    if (!debug_mode) return;
    va_list args;
    va_start(args, format);
    vprintf(format, args);
    va_end(args);
  }

  // 状態をデバッグ出力
  void printGameState(const state_t& state, int selected_move, double score) {
    if (!debug_mode) return;
    printf("Current Board:\n");
    for (int i = 0; i < 9; i++) {
      printf("%d ", state.board[i]);
      if ((i + 1) % 3 == 0) printf("\n");
    }
    printf("Selected Move: %d\n", selected_move);
    printf("Score: %.2f\n", score);
  }

  // 学習状態をデバッグ出力
  void printLearningState(const int* lastboard, double max_ev_r,
                          int traincount) {
    if (!debug_mode) return;
    printf("Training Count: %d\n", traincount);
    printf("Last Board State:\n");
    for (int i = 0; i < 9; i++) {
      printf("%d ", lastboard[i]);
      if ((i + 1) % 3 == 0) printf("\n");
    }
    printf("Max Expected Value: %.2f\n", max_ev_r);
  }

  virtual void initializeGame(int seed, int tupleNumber) {
    srand(seed);
    init(tupleNumber, Multistaging);
    print_info();
    initEvs(OI);
  }

  virtual void processGame(state_t& state, int& traincount) {
    int turn = 0;
    int lastboard[9] = {0};
    while (!gameOver(state)) {
      state_t copy;
      double max_ev_r = -DBL_MAX;
      int selected = selectMove(state);

      play(selected, state, &state);
      if (turn > 1) {
        updateLearning(lastboard, max_ev_r);
        traincount++;
      }
      memcpy(lastboard, state.board, sizeof(lastboard));
      putNewTile(&state);
      turn++;
    }
  }

  virtual int selectMove(const state_t& state) = 0;
  virtual void updateLearning(const int* lastboard, double max_ev_r) = 0;

 public:
  void enableDebug(bool enable = true) { debug_mode = enable; }
  virtual void run(int argc, char* argv[]) = 0;
};

class GreedyLearning : public LearningBase {
 protected:
  int selectMove(const state_t& state) override {
    state_t copy;
    double max_ev_r = -DBL_MAX;
    int selected = -1;
    debugPrint("Greedy Move Selection:\n");
    for (int d = 0; d < 4; d++) {
      if (play(d, state, &copy)) {
        double ev_r = calcEv(copy.board) + (copy.score - state.score);
        debugPrint("Direction %d: EV=%.2f\n", d, ev_r);
        if (ev_r > max_ev_r) {
          max_ev_r = ev_r;
          selected = d;
        }
      }
    }
    return selected;
  }

  void updateLearning(const int* lastboard, double max_ev_r) override {
    update(lastboard, max_ev_r - calcEv(lastboard));
  }
};

class EGreedyLearning : public LearningBase {
 private:
  double epsilon = 0.1;

 protected:
  int selectMove(const state_t& state) override {
    state_t copy;
    vector<int> validMoves;
    int bestMove = -1;
    double max_ev_r = -DBL_MAX;

    for (int d = 0; d < 4; d++) {
      if (play(d, state, &copy)) {
        double ev_r = calcEv(copy.board) + (copy.score - state.score);
        validMoves.push_back(d);
        if (ev_r > max_ev_r) {
          max_ev_r = ev_r;
          bestMove = d;
        }
      }
    }

    if ((double)rand() / RAND_MAX < epsilon && !validMoves.empty()) {
      return validMoves[rand() % validMoves.size()];
    }
    return bestMove;
  }

  void updateLearning(const int* lastboard, double max_ev_r) override {
    update(lastboard, max_ev_r - calcEv(lastboard));
  }
};

class UCBLearning : public LearningBase {
 private:
  double c = 1.2;  // UCB exploration constant

 protected:
  int selectMove(const state_t& state) override {
    state_t copy;
    vector<double> values(4, 0.0);
    vector<int> counts(4, 0);
    int totalPlays = 0;

    for (int d = 0; d < 4; d++) {
      if (play(d, state, &copy)) {
        values[d] = calcEv(copy.board) + (copy.score - state.score);
        counts[d] = calcAErr(copy.board);
        totalPlays += counts[d];
      }
    }

    int selected = -1;
    double maxUcb = -DBL_MAX;
    for (int d = 0; d < 4; d++) {
      if (counts[d] > 0) {
        double ucb = values[d] + c * sqrt(log(totalPlays) / counts[d]);
        if (ucb > maxUcb) {
          maxUcb = ucb;
          selected = d;
        }
      }
    }
    return selected;
  }

  void updateLearning(const int* lastboard, double max_ev_r) override {
    update(lastboard, max_ev_r - calcEv(lastboard));
  }
};

// デバッグ用のテストクラス
class LearningTester {
 public:
  static void runTests() {
    testGreedyLearning();
    testEGreedyLearning();
    testUCBLearning();
  }

 private:
  static void testGreedyLearning() {
    GreedyLearning greedy;
    greedy.enableDebug(true);
    runBasicTest(greedy, "Greedy");
  }

  static void testEGreedyLearning() {
    EGreedyLearning egreedy;
    egreedy.enableDebug(true);
    runBasicTest(egreedy, "E-Greedy");
  }

  static void testUCBLearning() {
    UCBLearning ucb;
    ucb.enableDebug(true);
    runBasicTest(ucb, "UCB");
  }

  static void runBasicTest(LearningBase& learner, const char* name) {
    printf("\nTesting %s Learning Algorithm\n", name);
    // テストケースの設定
    state_t test_state = initGame();
    // 既知の状態をセット
    test_state.board[0] = 2;
    test_state.board[1] = 2;
    test_state.board[2] = 0;
    test_state.board[3] = 0;
    test_state.board[4] = 2;
    test_state.board[5] = 0;
    test_state.board[6] = 0;
    test_state.board[7] = 0;
    test_state.board[8] = 2;

    // アルゴリズムのテスト実行
    int moves[10];
    for (int i = 0; i < 10; i++) {
      moves[i] = learner.selectMove(test_state);
      printf("Move %d: Selected direction %d\n", i + 1, moves[i]);

      state_t next_state;
      if (play(moves[i], test_state, &next_state)) {
        test_state = next_state;
        putNewTile(&test_state);
      }
    }
  }
};
