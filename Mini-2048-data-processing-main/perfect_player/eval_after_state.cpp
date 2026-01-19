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

int main(int argc, char** argv) {
  if (argc < 1 + 1) {
    fprintf(stderr, "Usage: eval_after_state <path_to_directory>\n");
    exit(1);
  }

    // ../board_data/argv[1] に変換
    std::string input_dir = (fs::path("../board_data") / argv[1]).string();

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
      "eval-after-state-" + fs::path(input_dir).filename().string() + ".txt";
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
