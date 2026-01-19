#pragma once

// 既存のNTヘッダーファイルのインクルード
#if defined(T1)
#include "1tuples_sym.h"
namespace NT = NT1;
constexpr int nt = 1;
#elif defined(T2)
#include "2tuples_sym.h"
namespace NT = NT2;
constexpr int nt = 2;
#elif defined(T3)
#include "3tuples_sym.h"
namespace NT = NT3;
constexpr int nt = 3;
#elif defined(T4)
#include "4tuples_sym.h"
namespace NT = NT4;
constexpr int nt = 4;
#elif defined(T5)
#include "5tuples_sym.h"
namespace NT = NT5;
constexpr int nt = 5;
#elif defined(T6)
#include "6tuples_sym.h"
namespace NT = NT6;
constexpr int nt = 6;
#elif defined(T7)
#include "7tuples_sym.h"
namespace NT = NT7;
constexpr int nt = 7;
#elif defined(T8)
#include "8tuples_sym.h"
namespace NT = NT8;
constexpr int nt = 8;
#elif defined(T9)
#include "9tuples_sym.h"
namespace NT = NT9;
constexpr int nt = 9;
#else
#include "1tuples_sym.h"
namespace NT = NT1;
constexpr int nt = 1;
#endif