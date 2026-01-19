#include <zlib.h>
#include <cfloat>
#include <climits>
#include <filesystem>
#include <iostream>
#include <string>

#include "../head/Game2048_3_3.h"
#include "../head/fread.h"
// 必要に応じてmini_0/1/2/3を切り替え

// NT6名前空間のinline関数を使うためmain直前でインクルード
#include "../head/6tuples_mini_2.h"

namespace fs = std::filesystem;
using namespace std;

// ファイル名からパラメータを抽出する構造体と関数を追加
struct FileParams {
  int NT;
  int tupleNumber;
  int multiStaging;
  int oi;
  int seed;
  int c;
  int mini;
};

FileParams parseFileName(const char* filename) {
  FileParams params = {0, 0, 0, 0, 0, 0, 0};
  char basename[256];
  strcpy(basename, filename);

  // ファイルパスから最後の'/'以降を取得
  char* last_slash = strrchr(basename, '/');
  char* actual_name = last_slash ? last_slash + 1 : basename;

  // 最初の数字を取得してNTに設定
  params.NT = atoi(actual_name);

  // .zip 拡張子を削除
  char* ext = strstr(basename, ".zip");
  if (ext) *ext = '\0';

  // .dat 拡張子を削除
  ext = strstr(basename, ".dat");
  if (ext) *ext = '\0';

  char* token = strtok(basename, "_");
  while (token != NULL) {
    if (strncmp(token, "TupleNumber", 11) == 0)
      params.tupleNumber = atoi(token + 11);
    else if (strncmp(token, "Multistaging", 12) == 0)
      params.multiStaging = atoi(token + 12);
    else if (strncmp(token, "OI", 2) == 0)
      params.oi = atoi(token + 2);
    else if (strncmp(token, "seed", 4) == 0)
      params.seed = atoi(token + 4);
    else if (strncmp(token, "c", 1) == 0)
      params.c = atoi(token + 1);
    else if (strncmp(token, "mini", 4) == 0)
      params.mini = atoi(token + 4);

    token = strtok(NULL, "_");
  }
  return params;
}

bool loadCompressedEvs(const char* filename) {
  FileParams params = parseFileName(filename);
  NT6::init(params.tupleNumber, params.multiStaging);
  printf("Initialized with TupleNumber: %d, MultiStaging: %d\n", params.tupleNumber, params.multiStaging);

  gzFile gz_fp = gzopen(filename, "rb");
  if (!gz_fp) {
    fprintf(stderr, "Error opening compressed file\n");
    return false;
  }

  FILE* temp_fp = tmpfile();
  if (!temp_fp) {
    fprintf(stderr, "Error creating temporary file\n");
    gzclose(gz_fp);
    return false;
  }

  char buffer[8192];
  int bytes_read;
  size_t total_bytes = 0;

  while ((bytes_read = gzread(gz_fp, buffer, sizeof(buffer))) > 0) {
    size_t written = fwrite(buffer, 1, bytes_read, temp_fp);
    if (written != (size_t)bytes_read) {
      fprintf(stderr,
              "Error writing to temporary file: expected %d, wrote %zu\n",
              bytes_read, written);
      fclose(temp_fp);
      gzclose(gz_fp);
      return false;
    }
    total_bytes += written;
  }

  if (bytes_read < 0) {
    int errnum;
    fprintf(stderr, "Error during decompression: %s\n",
            gzerror(gz_fp, &errnum));
    fclose(temp_fp);
    gzclose(gz_fp);
    return false;
  }

  rewind(temp_fp);

  // データを読み込む
  NT6::readEvs(temp_fp);

  // クリーンアップ
  fclose(temp_fp);
  gzclose(gz_fp);

  return true;
}

int main(int argc, char** argv) {
  using namespace NT6;
  if (argc < 3) {
    fprintf(stderr, "Usage: eval_after_state <path_to_directory> <evfile>\n");
    exit(1);
  }

  // ../board_data/argv[1] に変換
  std::string input_dir = (fs::path("../board_data") / argv[1]).string();
  std::string after_state_file = (fs::path(input_dir) / "after-state.txt").string();

  // ファイルが存在しない場合のエラーハンドリング
  if (!fs::exists(after_state_file)) {
    cerr << "Error: " << after_state_file << " does not exist." << endl;
    return 1;
  }

  // 評価関数ファイルの読み込み
  const char* evfile = argv[2];
  // FILE* ev_fp = fopen(evfile, "rb");
  // if (!ev_fp) {
  //   cerr << "Error: Cannot open evfile " << evfile << endl;
  //   return 1;
  // }
  // 評価関数の読み込み（inline関数なのでヘッダのみでOK）
  loadCompressedEvs(evfile);
  // fclose(ev_fp);

  // 出力用ディレクトリとファイル名を設定
  // string eval_player = "ev";
  string output_dir = "../board_data/";
  fs::create_directories(output_dir);
  string file = "eval-after-state-" + fs::path(input_dir).filename().string() + ".txt";
  string fullPath = output_dir + file;

  // 出力ファイルを開く
  const char* filename = fullPath.c_str();
  FILE* fp = fopen(filename, "w+");
  if (!fp) {
    cerr << "Error: Could not open " << filename << " for writing." << endl;
    return 1;
  }

  // データの読み込み
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
      double eval = calcEv(board); // eval_afterstate ではなく calcEv を使う
      fprintf(fp, "%f\n", eval);
    }
  }

  fclose(fp);
  cout << "Evaluation complete. Results saved to " << fullPath << endl;

  return 0;
}
