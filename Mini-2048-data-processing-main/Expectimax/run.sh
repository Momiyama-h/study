#!/bin/bash

# 配列に値を格納
values=(-5000 -2500 -1000 -500 -100 100 500 1000 2500 5000)

# 配列をループで回す
for j in 4 5; do
    for i in "${values[@]}"; do
        nohup ./a.out 0 10000 "4tuple_data_9_evs${i}.dat" $j&
    done
    for i in "${values[@]}"; do
        nohup ./a.out 0 10000 "6tuple_data_9_evs${i}.dat" $j&
    done
done
