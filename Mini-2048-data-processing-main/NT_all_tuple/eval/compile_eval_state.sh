#!/bin/bash
# gdb用デバッグビルドスクリプト

SRC=eval_state.cpp
OUT=eval_state
CXX=g++

# CXXFLAGS="-std=c++20 -g -O0 -Wall -I../head"
CXXFLAGS="-std=c++20 -g -O2 -Wall -I../head"
LDFLAGS="-lz"

$CXX $CXXFLAGS $SRC -o $OUT $LDFLAGS

if [ $? -eq 0 ]; then
  echo "デバッグ用バイナリ ./$OUT を作成しました。gdbで実行できます。"
else
  echo "ビルド失敗"
fi
