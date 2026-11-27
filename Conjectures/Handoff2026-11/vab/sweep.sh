#!/bin/bash
for a in 4 6 8 10 12; do for b in $(seq $((2*a+1)) 2 61); do
  g=$(python3 -c "import math;print(math.gcd($a,$b))"); [ "$g" != "1" ] && continue
  timeout 150 ./vproof $a $b 1000000 3e9 1.2e9 > out_${a}_${b}.txt 2>&1; echo "exit=$?" >> out_${a}_${b}.txt
done; done
