#pragma once

#include <string>
#include <vector>

// 共通の定数定義
constexpr long long STORAGE_FREQUENCY = (5 * 10000000);
constexpr long long STORAGE_COUNT = 1;
constexpr long long MAX_GAMES = 1000000000;

// 共通のグローバル変数
struct GlobalConfig {
  static int TupleNumber;
  static int Multistaging;
  static int OI;
  static int TC;
  static std::string Exploratory;
  static int Restart_Len;
  static int storage_c;
  static std::vector<std::string> Exploratorys;
};
