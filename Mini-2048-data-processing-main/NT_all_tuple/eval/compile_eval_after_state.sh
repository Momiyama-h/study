#!/bin/bash
# eval_after_state.cpp のコンパイル用スクリプト

SRC=eval_after_state.cpp
OUT=eval_after_state
CXX=g++

CXXFLAGS="-std=c++20 -g -O2 -Wall -I../head"
LDFLAGS="-lz"

$CXX $CXXFLAGS $SRC -o $OUT $LDFLAGS

if [ $? -eq 0 ]; then
  echo "コンパイル成功: ./$OUT"
else
  echo "コンパイル失敗"
fi
