#include <cfloat>
#include <climits>
#include <filesystem>
#include <iostream>

#include "Game2048_3_3.h"
#include "fread.h"
#include "perfect_play.h"
#include "play_table.h"
namespace fs = std::filesystem;
using namespace std;

static string make_safe_name(const string& input) {
  string trimmed = input;
  if (trimmed.rfind("./", 0) == 0) {
    trimmed = trimmed.substr(2);
  }
  string out;
  out.reserve(trimmed.size());
  for (char c : trimmed) {
    if (c == '/' || c == '\\') {
      out += "__";
    } else {
      out += c;
    }
  }
  return out;
}

int progress_calculation(int board[9]) {
  int sum = 0;
  for (int i = 0; i < 9; i++) {
    if (board[i] != 0) {
      sum += 1 << board[i];
    }
  }
  return sum / 2;
}

int main(int argc, char** argv) {
  if (argc < 2) {
    fprintf(stderr, "Usage: eval_state <path_relative_to_board_data>\n");
    exit(1);
  }

  fs::path input_rel = fs::path(argv[1]);
  std::string input_dir = (fs::path("../board_data") / input_rel).string();

  // state.txt のパスを決定
  string state_file = fs::path(input_dir) / "state.txt";

  // ファイルが存在しない場合のエラーハンドリング
  if (!fs::exists(state_file)) {
    cerr << "Error: " << state_file << " does not exist." << endl;
    return 1;
  }

  string eval_player = "PP";
  readDB2();

  // 出力ディレクトリを作成
  string output_dir = "../board_data/" + eval_player + "/";
  fs::create_directory(output_dir);

  // 出力ファイルのパス
  string output_file =
      output_dir + "eval-state-" + make_safe_name(input_rel.string()) + ".txt";

  // 入力データの読み込み
  read_state_one_game(state_file);

  // 出力ファイルを開く
  const char* filename = output_file.c_str();
  FILE* fp = fopen(filename, "w+");
  if (!fp) {
    cerr << "Error: Could not open " << filename << " for writing." << endl;
    return 1;
  }

  int i = 0;
  for (array<int, 9>& arr : boards) {
    if (arr[0] == -1) {
      fprintf(fp, "%s\n", gameovers[i].c_str());
      i++;
    } else {
      state_t state, tmp;
      for (int j = 0; j < 9; j++) {
        state.board[j] = arr[j];
      }
      for (int d = 0; d < 4; d++) {
        if (play(d, state, &tmp)) {
          fprintf(fp, "%f ", eval_afterstate(tmp.board));
        } else {
          fprintf(fp, "-10000000000.000000 ");
        }
        if (d == 3) {
          fprintf(fp, "%d\n", progress_calculation(state.board));
        }
      }
    }
  }

  fclose(fp);

  cout << "Evaluation complete. Results saved to " << output_file << endl;

  return 0;
}
