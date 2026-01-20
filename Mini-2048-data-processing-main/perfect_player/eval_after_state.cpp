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

int main(int argc, char** argv) {
  if (argc < 1 + 1) {
    fprintf(stderr, "Usage: eval_after_state <path_relative_to_board_data>\n");
    exit(1);
  }

  fs::path input_rel = fs::path(argv[1]);
  std::string input_dir = (fs::path("../board_data") / input_rel).string();

    // after-state.txt のパスを生成
    std::string after_state_file = (fs::path(input_dir) / "after-state.txt").string();

  // ファイルが存在しない場合のエラーハンドリング
  if (!fs::exists(after_state_file)) {
    cerr << "Error: " << after_state_file << " does not exist." << endl;
    return 1;
  }

  // 出力用ディレクトリとファイル名を設定
  string eval_player = "PP";
  string output_dir = "../board_data/" + eval_player + "/";
  fs::create_directory(output_dir);

  string file =
      "eval-after-state-" + make_safe_name(input_rel.string()) + ".txt";
  string fullPath = output_dir + file;

  // 出力ファイルを開く
  const char* filename = fullPath.c_str();
  FILE* fp = fopen(filename, "w+");
  if (!fp) {
    cerr << "Error: Could not open " << filename << " for writing." << endl;
    return 1;
  }

  // データの読み込み
  readDB2();
  read_state_one_game(after_state_file);

  // 評価値を計算して出力
  int i = 0;
  for (array<int, 9>& arr : boards) {
    if (arr[0] == -1) {
      fprintf(fp, "%s\n", gameovers[i].c_str());
      i++;
    } else {
      int board[9];
      for (int j = 0; j < 9; j++) {
        board[j] = arr[j];
      }
      double eval = eval_afterstate(board);
      fprintf(fp, "%f\n", eval);
    }
  }

  fclose(fp);
  cout << "Evaluation complete. Results saved to " << fullPath << endl;

  return 0;
}
