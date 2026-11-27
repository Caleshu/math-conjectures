#!/bin/bash
# $1 = DIST (0 for V, 1 for U); dir V or U
D=$1; dir=$2
for a in 4 6 8 10 12 14 16; do for b in $(seq $((2*a+1)) 2 81); do
  g=$(python3 -c "import math;print(math.gcd($a,$b))"); [ "$g" != "1" ] && continue
  timeout 120 ./aproof $a $b 600000 2e9 1.0e9 $D > $dir/${a}_${b}.txt 2>&1; echo "exit=$?" >> $dir/${a}_${b}.txt
done; done
