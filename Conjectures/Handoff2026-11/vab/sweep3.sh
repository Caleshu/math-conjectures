#!/bin/bash
D=$1; dir=$2; shift 2
for a in "$@"; do for b in $(seq $((2*a+1)) 2 $((2*a+13))); do
  g=$(python3 -c "import math;print(math.gcd($a,$b))"); [ "$g" != "1" ] && continue
  [ -f $dir/${a}_${b}.txt ] && grep -q "exit=" $dir/${a}_${b}.txt && continue
  timeout 100 ./aproof $a $b 600000 2e9 1.0e9 $D > $dir/${a}_${b}.txt 2>&1; echo "exit=$?" >> $dir/${a}_${b}.txt
done; done
