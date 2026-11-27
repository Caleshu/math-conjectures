Reset(GlobalMersenneTwister, 12345);
N := 200000;
S := Sp(6, 5); O := Omega(7, 5);
cS := 0; cO := 0; c2S := 0; c2O := 0;
for i in [1..N] do
  x := PseudoRandom(S); k := ProjectiveOrder(x)[1];
  if k <= 4 then cS := cS + 1; fi; if k = 2 then c2S := c2S + 1; fi;
  y := PseudoRandom(O); k := Order(y);
  if k <= 4 then cO := cO + 1; fi; if k = 2 then c2O := c2O + 1; fi;
od;
Print("PSp(6,5): order<=4 fraction ", Float(cS/N), "  (table ", Float(17566281876/228501000000000), ")\n");
Print("Omega(7,5): order<=4 fraction ", Float(cO/N), "  (table ", Float(215584857876/228501000000000), ")\n");
QUIT;
