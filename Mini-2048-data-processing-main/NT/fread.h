#include <array>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using namespace std;

string game_over;
vector<array<int, 9>> boards;  // int[9]の配列を格納するベクター
vector<string> gameovers;
string gameoverLine;  // gameover_turnの行を格納する

void read_state_one_game(string filename) {
  ifstream inputFile(filename);  // 入力ファイルを開く
  if (!inputFile.is_open()) {
    cerr << "Failed to open file.\n";
    return;
  }
  string line;

  while (getline(inputFile, line)) {
    if (line.find("gameover_turn") != string::npos) {
      // gameover_turnが見つかったら、その行を保存してループを抜ける
      gameoverLine = line;
      gameovers.push_back(gameoverLine);
      array<int, 9> temp;
      temp[0] = -1;
      boards.push_back(temp);
    } else {
      array<int, 9> temp;
      istringstream iss(line);
      bool valid = true;
      for (int i = 0; i < 9; ++i) {
        if (!(iss >> temp[i])) {  // 読み込み失敗時は無効とみなす
          valid = false;
          break;
        }
      }
      if (valid) {
        boards.push_back(temp);  // 有効なデータのみ追加
      } else {
        cerr << "Invalid data format: " << line << '\n';
      }
    }
  }

  inputFile.close();
}
