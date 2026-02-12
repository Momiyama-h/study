# Training Change Log

## 2026-02-12
- Align TD update evaluation with policy evaluation by using `eval_board(lastboard)`
  for update targets in training code. This keeps greedy behavior unchanged and
  makes expectimax updates use `calcEvSafe` consistently.
  Affected files:
  - training/learning_ntuple_sym.cpp
  - training/learning_ntuple_sym_nt5a.cpp
  - training/learning_ntuple_notsym.cpp
  - training/learning_ntuple_notsym_nt5a.cpp
