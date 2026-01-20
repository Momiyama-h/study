#include <array>
#include <cfloat>
#include <cstdlib>
#include <filesystem>
#include <iostream>

#include "4tuples_sym.h"
#include "4tuples_nosym.h"
#include "6tuples_sym.h"
#include "6tuples_notsym.h"
#include "Game2048_3_3.h"
#include "fread.h"
#include "play_table.h"
namespace fs = std::filesystem;
using namespace std;
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
  if (argc < 2 + 1) {
    fprintf(stderr, "Usage: playgreedy <load-player-name> <EV-file> [sym|notsym] [4|6]\n");
    exit(1);
  }
  string dname = argv[1];
  char* evfile = argv[2];
  string evfile_name(evfile);
  string basename = fs::path(evfile_name).filename().string();
  // prev:
  // string number(1, evfile[0]);
  // string symmetry = "sym";
  // if (evfile_name.find("notsym") != string::npos) { symmetry = "notsym"; }
  string number;
  bool number_set = false;
  bool symmetry_set = false;

  string symmetry = "sym";
  for (int i = 3; i < argc; i++) {
    string opt = argv[i];
    if (opt == "sym" || opt == "notsym") {
      symmetry = opt;
      symmetry_set = true;
    } else if (opt == "4" || opt == "6") {
      number = opt;
      number_set = true;
    } else {
      fprintf(stderr, "Error: unknown option: %s\n", opt.c_str());
      exit(1);
    }
  }
  if (!symmetry_set) {
    if (basename.find("notsym") != string::npos || basename.find("nosym") != string::npos) {
      symmetry = "notsym";
    }
  }
  if (!number_set) {
    if (!basename.empty() && (basename[0] == '4' || basename[0] == '6')) {
      number = string(1, basename[0]);
    } else {
      fprintf(stderr, "Error: evfile must start with '4' or '6': %s\n", basename.c_str());
      exit(1);
    }
  }

  double average = 0;
  FILE* fp = fopen(evfile, "rb");
  if (fp == NULL) {
    fprintf(stderr, "cannot open file: %s\n", evfile);
    exit(1);
  }
  if (number == "4") {
    if (symmetry == "sym") {
      NT4::readEvs(fp);
    } else {
      NT4_notsym::readEvs(fp);
    }
  } else {
    if (symmetry == "sym") {
      NT6::readEvs(fp);
    } else {
      NT6_notsym::readEvs(fp);
    }
  }
  fclose(fp);
  // prev:
  // string s = "../board_data/" + dname + "/state.txt";
  // fs::create_directory("../board_data");
  // string dir = "../board_data/NT" + number + "_" + symmetry + "/";
  string base_root = "../board_data";
  const char* base_env = getenv("BOARD_DATA_ROOT");
  if (base_env && *base_env) {
    base_root = base_env;
  }
  fs::create_directories(base_root);
  string s = base_root + "/" + dname + "/state.txt";
  string dir = base_root + "/NT" + number + "_" + symmetry + "/";
  fs::create_directories(dir);

  read_state_one_game(s);
  string file = "eval-state-" + dname + ".txt";
  string fullPath = dir + file;
  const char* filename = fullPath.c_str();
  fp = fopen(filename, "w+");
  int i = 0;
  vector<vector<double>> eval_list;
  for (array<int, 9>& arr : boards) {
    vector<double> evals(4, -10000);
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
          double eval;
          if (number == "4") {
            if (symmetry == "sym") {
              eval = NT4::calcEv(tmp.board);
            } else {
              eval = NT4_notsym::calcEv(tmp.board);
            }
          } else {
            if (symmetry == "sym") {
              eval = NT6::calcEv(tmp.board);
            } else {
              eval = NT6_notsym::calcEv(tmp.board);
            }
          }
          fprintf(fp, "%f ", eval);
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

  return 0;
}
