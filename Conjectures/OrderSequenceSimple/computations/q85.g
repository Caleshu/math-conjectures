LoadPackage("ctbllib");
cmp := function(a, b)
  local ta, tb, ca, cb, ords, cuma, cumb, t, aDomB, bDomA, oa, ob;
  ta := CharacterTable(a); tb := CharacterTable(b);
  if ta = fail or tb = fail then Print(a, " / ", b, ": table missing\n"); return; fi;
  Print(a, " |G|=", Size(ta), "   ", b, " |H|=", Size(tb), "  equal: ", Size(ta)=Size(tb), "\n");
  oa := OrdersClassRepresentatives(ta); ob := OrdersClassRepresentatives(tb);
  ca := SizesConjugacyClasses(ta); cb := SizesConjugacyClasses(tb);
  ords := Set(Concatenation(oa, ob));
  aDomB := true; bDomA := true;
  for t in ords do
    cuma := Sum(Filtered([1..Length(oa)], i -> oa[i] <= t), i -> ca[i]);
    cumb := Sum(Filtered([1..Length(ob)], i -> ob[i] <= t), i -> cb[i]);
    if cuma > cumb then aDomB := false; fi;
    if cumb > cuma then bDomA := false; fi;
  od;
  Print("  ", a, " dominates ", b, ": ", aDomB, "    ", b, " dominates ", a, ": ", bDomA, "\n");
  Print("  orders ", a, ": ", List(ords, t -> [t, Sum(Filtered([1..Length(oa)], i -> oa[i] = t), i -> ca[i])]), "\n");
  Print("  orders ", b, ": ", List(ords, t -> [t, Sum(Filtered([1..Length(ob)], i -> ob[i] = t), i -> cb[i])]), "\n");
end;
cmp("A8", "L3(4)");
cmp("S6(3)", "O7(3)");
cmp("S6(5)", "O7(5)");
cmp("S8(3)", "O9(3)");
cmp("S6(7)", "O7(7)");
cmp("S6(9)", "O7(9)");
cmp("S10(3)", "O11(3)");
QUIT;
