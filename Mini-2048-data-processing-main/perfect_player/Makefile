# コンパイラとオプション設定
CXX = g++
CXXFLAGS = -std=c++20 -mcmodel=large -O2

# ソースファイル
PLAY_PP = Play_perfect_player
EVAL_STATE = eval_state
EVAL_AFTER_STATE = eval_after_state

# バイナリファイル
PLAY_PP_BIN = $(PLAY_PP)
EVAL_STATE_BIN = $(EVAL_STATE)
EVAL_AFTER_STATE_BIN = $(EVAL_AFTER_STATE)

# デフォルトターゲット
all: $(PLAY_PP_BIN) $(EVAL_STATE_BIN) $(EVAL_AFTER_STATE_BIN)

# コンパイルルール
$(PLAY_PP_BIN): $(PLAY_PP).cpp
	$(CXX) $(CXXFLAGS) -o $@ $^

$(EVAL_STATE_BIN): $(EVAL_STATE).cpp
	$(CXX) $(CXXFLAGS) -o $@ $^

$(EVAL_AFTER_STATE_BIN): $(EVAL_AFTER_STATE).cpp
	$(CXX) $(CXXFLAGS) -o $@ $^

# 実行ルール
run_play_pp:
	@read -p "Enter seed: " seed; \
	 read -p "Enter game count: " games; \
	 ./$(PLAY_PP_BIN) $$seed $$games

run_eval_state:
	@read -p "Enter player name (e.g., NT4): " player; \
	 ./$(EVAL_STATE_BIN) $$player

run_eval_after_state:
	@read -p "Enter player name (e.g., NT4): " player; \
	 ./$(EVAL_AFTER_STATE_BIN) $$player

# クリーンアップ
clean:
	rm -f $(PLAY_PP_BIN) $(EVAL_STATE_BIN) $(EVAL_AFTER_STATE_BIN)
