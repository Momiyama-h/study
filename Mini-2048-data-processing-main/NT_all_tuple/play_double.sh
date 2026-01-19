#!/bin/bash

mkdir -p logs

echo "Starting play_greedy.sh..."
nohup ./play_greedy.sh > logs/play_greedy.log 2>&1 &
wait

echo "play_greedy.sh completed. Starting play_Exp.sh..."
nohup ./play_Exp.sh > logs/play_Exp.log 2>&1 &
wait

echo "All experiments completed."
