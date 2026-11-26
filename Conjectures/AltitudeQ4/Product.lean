/-
# The altitude of the hypercube is less than `d` for every `d ≥ 4`

The *altitude* `f(G)` is the minimum, over all edge-orderings of `G`, of the number of edges of
the longest increasing path. The folklore question is whether `f(Q_d) = d`.

**Theorem (`altitude_le`).** For every `d`, `Q_d` has an edge-ordering whose increasing paths
all have at most `d - d / 4` edges. Hence (`altitude_lt`) `f(Q_d) < d` for every `d ≥ 4`.

The proof is the product bound `f(Q_{a+b}) ≤ f(Q_a) + f(Q_b)` (`altLE_add`): order every
edge in the first `a` directions before every edge in the last `b` directions. Base cases are
`Q_0`, `Q_1` and the explicit ordering of `Q_4` from `AltitudeQ4.lean`.

Conventions. A vertex of `Q_d` is a natural number `v < 2^d`; bit `i` is coordinate `i`.
An edge-ordering is a symmetric labeling `lab u v` of the edges that is injective on
(unordered) edges. Any such labeling induces a bijection onto `1, …, |E|` with the same
increasing paths, so this is the same as the usual notion. An increasing path with `k` edges
is a list of `k + 1` distinct vertices, consecutive ones adjacent, with strictly increasing
edge labels.
-/
import Mathlib
import Conjectures.AltitudeQ4.AltitudeQ4

namespace Altitude

/-- `u` and `v` are adjacent in `Q_d`: both are `< 2^d` and they differ in exactly one of the
first `d` bits. -/
def Adj (d u v : ℕ) : Prop :=
  u < 2 ^ d ∧ v < 2 ^ d ∧
    ∃ i < d, u.testBit i ≠ v.testBit i ∧ ∀ j < d, j ≠ i → u.testBit j = v.testBit j

instance (d u v : ℕ) : Decidable (Adj d u v) := by unfold Adj; infer_instance

/-- The labels along the list strictly increase. -/
def Inc (lab : ℕ → ℕ → ℕ) : List ℕ → Prop
  | u :: v :: w :: l => lab u v < lab v w ∧ Inc lab (v :: w :: l)
  | _ => True

/-- An increasing path of `Q_d` (with `l.length - 1` edges). -/
def IncPath (d : ℕ) (lab : ℕ → ℕ → ℕ) (l : List ℕ) : Prop :=
  l.Nodup ∧ l.IsChain (Adj d) ∧ Inc lab l

/-- `lab` is an edge-ordering of `Q_d` with all labels `< B`. -/
structure IsOrdering (d B : ℕ) (lab : ℕ → ℕ → ℕ) : Prop where
  symm : ∀ u v, Adj d u v → lab u v = lab v u
  lt : ∀ u v, Adj d u v → lab u v < B
  inj : ∀ u v x y, Adj d u v → Adj d x y → lab u v = lab x y →
    (u = x ∧ v = y) ∨ (u = y ∧ v = x)

/-- `f(Q_d) ≤ k`: some edge-ordering of `Q_d` has no increasing path with more than `k` edges. -/
def AltLE (d k : ℕ) : Prop :=
  ∃ B lab, IsOrdering d B lab ∧ ∀ l, IncPath d lab l → l.length ≤ k + 1

/-! ### List lemmas -/

lemma inc_tail {lab : ℕ → ℕ → ℕ} {u : ℕ} {l : List ℕ} (h : Inc lab (u :: l)) : Inc lab l := by
  match l, h with
  | [], _ => trivial
  | [_], _ => trivial
  | _ :: _ :: _, h => exact h.2

lemma inc_append_left {lab : ℕ → ℕ → ℕ} :
    ∀ (l₁ l₂ : List ℕ), Inc lab (l₁ ++ l₂) → Inc lab l₁
  | [], _, _ => trivial
  | [_], _, _ => trivial
  | [_, _], _, _ => trivial
  | u :: v :: w :: l₁, l₂, h => ⟨h.1, inc_append_left (v :: w :: l₁) l₂ h.2⟩

lemma inc_append_right {lab : ℕ → ℕ → ℕ} :
    ∀ (l₁ l₂ : List ℕ), Inc lab (l₁ ++ l₂) → Inc lab l₂
  | [], _, h => h
  | _ :: l₁, l₂, h => inc_append_right l₁ l₂ (inc_tail h)

lemma incPath_append {d : ℕ} {lab : ℕ → ℕ → ℕ} {l₁ l₂ : List ℕ}
    (h : IncPath d lab (l₁ ++ l₂)) : IncPath d lab l₁ ∧ IncPath d lab l₂ := by
  obtain ⟨hn, hc, hi⟩ := h
  rw [List.nodup_append] at hn
  rw [List.isChain_append] at hc
  exact ⟨⟨hn.1, hc.1, inc_append_left _ _ hi⟩, ⟨hn.2.1, hc.2.1, inc_append_right _ _ hi⟩⟩

lemma isChain_and' {R S : ℕ → ℕ → Prop} :
    ∀ {l : List ℕ}, l.IsChain R → l.IsChain S → l.IsChain (fun x y => R x y ∧ S x y)
  | [], _, _ => List.isChain_nil
  | [_], _, _ => List.isChain_singleton _
  | _ :: _ :: _, hR, hS =>
    (isChain_and' hR.tail hS.tail).cons_cons ⟨hR.rel, hS.rel⟩

lemma const_of_chain {f : ℕ → ℕ} :
    ∀ {l : List ℕ}, l.IsChain (fun x y => f x = f y) → ∀ x ∈ l, ∀ y ∈ l, f x = f y
  | [], _ => by simp
  | [_], _ => by simp
  | u :: v :: l, h => by
    have ih := const_of_chain h.tail
    have key : ∀ x ∈ u :: v :: l, f x = f v := by
      intro x hx
      rcases List.mem_cons.1 hx with rfl | hx
      · exact h.rel
      · exact ih x hx v (by simp)
    intro x hx y hy
    rw [key x hx, key y hy]

/-! ### Splitting coordinates -/

lemma div_lt_of_lt {a b u : ℕ} (hu : u < 2 ^ (a + b)) : u / 2 ^ a < 2 ^ b := by
  rw [Nat.div_lt_iff_lt_mul (by positivity), ← pow_add, Nat.add_comm]; exact hu

lemma eq_of_mod_div {a u v : ℕ} (h1 : u % 2 ^ a = v % 2 ^ a) (h2 : u / 2 ^ a = v / 2 ^ a) :
    u = v := by
  rw [← Nat.mod_add_div u (2 ^ a), ← Nat.mod_add_div v (2 ^ a), h1, h2]

/-- An edge of `Q_{a+b}` either stays in a copy of `Q_a` (same high part) or in a copy of
`Q_b` (same low part). -/
lemma adj_split {a b u v : ℕ} (h : Adj (a + b) u v) :
    (u / 2 ^ a = v / 2 ^ a ∧ Adj a (u % 2 ^ a) (v % 2 ^ a)) ∨
    (u % 2 ^ a = v % 2 ^ a ∧ u / 2 ^ a ≠ v / 2 ^ a ∧ Adj b (u / 2 ^ a) (v / 2 ^ a)) := by
  obtain ⟨hu, hv, i, hi, hne, hoth⟩ := h
  by_cases hia : i < a
  · left
    refine ⟨?_, Nat.mod_lt _ (by positivity), Nat.mod_lt _ (by positivity), i, hia, ?_, ?_⟩
    · apply Nat.eq_of_testBit_eq; intro j
      rw [Nat.testBit_div_two_pow, Nat.testBit_div_two_pow]
      by_cases hj : j + a < a + b
      · exact hoth (j + a) hj (by omega)
      · rw [Nat.testBit_lt_two_pow (lt_of_lt_of_le hu (Nat.pow_le_pow_right (by omega) (by omega))),
          Nat.testBit_lt_two_pow (lt_of_lt_of_le hv (Nat.pow_le_pow_right (by omega) (by omega)))]
    · simpa [Nat.testBit_mod_two_pow, hia] using hne
    · intro j hj hji
      simp only [Nat.testBit_mod_two_pow, hj, decide_true, Bool.true_and]
      exact hoth j (by omega) hji
  · right
    refine ⟨?_, ?_, div_lt_of_lt hu, div_lt_of_lt hv, i - a, by omega, ?_, ?_⟩
    · apply Nat.eq_of_testBit_eq; intro j
      simp only [Nat.testBit_mod_two_pow]
      by_cases hj : j < a
      · simp only [hj, decide_true, Bool.true_and]; exact hoth j (by omega) (by omega)
      · simp [hj]
    · intro heq
      apply hne
      have := congrArg (fun x => x.testBit (i - a)) heq
      simp only [Nat.testBit_div_two_pow] at this
      rwa [Nat.sub_add_cancel (by omega)] at this
    · rw [Nat.testBit_div_two_pow, Nat.testBit_div_two_pow, Nat.sub_add_cancel (by omega)]
      exact hne
    · intro j hj hji
      rw [Nat.testBit_div_two_pow, Nat.testBit_div_two_pow]
      exact hoth (j + a) (by omega) (by omega)

/-! ### The product ordering -/

/-- Edges inside a copy of `Q_a` (labels `< Ba * 2^b`) come before edges inside a copy of
`Q_b`. Within each block, labels are those of `la` / `lb`, with ties between copies broken by
the index of the copy. -/
def prodLab (a b Ba : ℕ) (la lb : ℕ → ℕ → ℕ) (u v : ℕ) : ℕ :=
  if u / 2 ^ a = v / 2 ^ a then la (u % 2 ^ a) (v % 2 ^ a) * 2 ^ b + u / 2 ^ a
  else Ba * 2 ^ b + lb (u / 2 ^ a) (v / 2 ^ a) * 2 ^ a + u % 2 ^ a

lemma mul_add_unique {m x y r s : ℕ} (hr : r < m) (hs : s < m) (h : x * m + r = y * m + s) :
    x = y ∧ r = s := by
  have hm : 0 < m := by omega
  have h1 : (x * m + r) / m = (y * m + s) / m := by rw [h]
  rw [Nat.add_comm (x * m), Nat.add_comm (y * m), Nat.add_mul_div_right _ _ hm,
    Nat.add_mul_div_right _ _ hm, Nat.div_eq_of_lt hr, Nat.div_eq_of_lt hs] at h1
  simp only [Nat.zero_add] at h1
  subst h1
  exact ⟨rfl, by omega⟩

section Product

variable {a b Ba Bb : ℕ} {la lb : ℕ → ℕ → ℕ}

lemma prodLab_low {u v : ℕ} (h : u / 2 ^ a = v / 2 ^ a) :
    prodLab a b Ba la lb u v = la (u % 2 ^ a) (v % 2 ^ a) * 2 ^ b + u / 2 ^ a := by
  simp [prodLab, h]

lemma prodLab_high {u v : ℕ} (h : u / 2 ^ a ≠ v / 2 ^ a) :
    prodLab a b Ba la lb u v = Ba * 2 ^ b + lb (u / 2 ^ a) (v / 2 ^ a) * 2 ^ a + u % 2 ^ a := by
  simp [prodLab, h]

lemma prodLab_low_lt (ha : IsOrdering a Ba la) {u v : ℕ} (huv : Adj (a + b) u v)
    (h : u / 2 ^ a = v / 2 ^ a) : prodLab a b Ba la lb u v < Ba * 2 ^ b := by
  rw [prodLab_low h]
  have hadj : Adj a (u % 2 ^ a) (v % 2 ^ a) := by
    rcases adj_split huv with h' | h'
    · exact h'.2
    · exact absurd h h'.2.1
  have h1 := ha.lt _ _ hadj
  have h2 := div_lt_of_lt huv.1
  calc la (u % 2 ^ a) (v % 2 ^ a) * 2 ^ b + u / 2 ^ a
      < la (u % 2 ^ a) (v % 2 ^ a) * 2 ^ b + 2 ^ b := by omega
    _ = (la (u % 2 ^ a) (v % 2 ^ a) + 1) * 2 ^ b := by ring
    _ ≤ Ba * 2 ^ b := Nat.mul_le_mul_right _ h1

lemma isOrdering_prod (ha : IsOrdering a Ba la) (hb : IsOrdering b Bb lb) :
    IsOrdering (a + b) (Ba * 2 ^ b + Bb * 2 ^ a) (prodLab a b Ba la lb) where
  symm u v huv := by
    rcases adj_split huv with ⟨h, hadj⟩ | ⟨h, hne, hadj⟩
    · rw [prodLab_low h, prodLab_low h.symm, ha.symm _ _ hadj, h]
    · rw [prodLab_high hne, prodLab_high (Ne.symm hne), hb.symm _ _ hadj, h]
  lt u v huv := by
    by_cases h : u / 2 ^ a = v / 2 ^ a
    · have := prodLab_low_lt (lb := lb) ha huv h; omega
    · rw [prodLab_high h]
      have hadj : Adj b (u / 2 ^ a) (v / 2 ^ a) := by
        rcases adj_split huv with h' | h'
        · exact absurd h'.1 h
        · exact h'.2.2
      have h1 := hb.lt _ _ hadj
      have h2 : u % 2 ^ a < 2 ^ a := Nat.mod_lt _ (by positivity)
      have : lb (u / 2 ^ a) (v / 2 ^ a) * 2 ^ a + u % 2 ^ a < Bb * 2 ^ a :=
        calc lb (u / 2 ^ a) (v / 2 ^ a) * 2 ^ a + u % 2 ^ a
            < lb (u / 2 ^ a) (v / 2 ^ a) * 2 ^ a + 2 ^ a := by omega
          _ = (lb (u / 2 ^ a) (v / 2 ^ a) + 1) * 2 ^ a := by ring
          _ ≤ Bb * 2 ^ a := Nat.mul_le_mul_right _ h1
      omega
  inj u v x y huv hxy heq := by
    by_cases h1 : u / 2 ^ a = v / 2 ^ a <;> by_cases h2 : x / 2 ^ a = y / 2 ^ a
    · -- both inside copies of `Q_a`
      have hadj1 : Adj a (u % 2 ^ a) (v % 2 ^ a) := by
        rcases adj_split huv with h' | h'
        · exact h'.2
        · exact absurd h1 h'.2.1
      have hadj2 : Adj a (x % 2 ^ a) (y % 2 ^ a) := by
        rcases adj_split hxy with h' | h'
        · exact h'.2
        · exact absurd h2 h'.2.1
      rw [prodLab_low h1, prodLab_low h2] at heq
      obtain ⟨hl, hh⟩ := mul_add_unique (div_lt_of_lt huv.1) (div_lt_of_lt hxy.1) heq
      rcases ha.inj _ _ _ _ hadj1 hadj2 hl with ⟨e1, e2⟩ | ⟨e1, e2⟩
      · exact Or.inl ⟨eq_of_mod_div e1 hh, eq_of_mod_div e2 (by rw [← h1, hh, h2])⟩
      · exact Or.inr ⟨eq_of_mod_div e1 (by rw [hh, h2]), eq_of_mod_div e2 (by rw [← h1, hh])⟩
    · have := prodLab_low_lt (lb := lb) ha huv h1
      rw [heq, prodLab_high h2] at this; omega
    · have := prodLab_low_lt (lb := lb) ha hxy h2
      rw [← heq, prodLab_high h1] at this; omega
    · -- both inside copies of `Q_b`
      obtain ⟨hm1, -, hadj1⟩ := (adj_split huv).resolve_left (fun h => h1 h.1)
      obtain ⟨hm2, -, hadj2⟩ := (adj_split hxy).resolve_left (fun h => h2 h.1)
      rw [prodLab_high h1, prodLab_high h2] at heq
      have heq' : lb (u / 2 ^ a) (v / 2 ^ a) * 2 ^ a + u % 2 ^ a =
          lb (x / 2 ^ a) (y / 2 ^ a) * 2 ^ a + x % 2 ^ a := by omega
      obtain ⟨hl, hh⟩ := mul_add_unique (Nat.mod_lt _ (by positivity))
        (Nat.mod_lt _ (by positivity)) heq'
      rcases hb.inj _ _ _ _ hadj1 hadj2 hl with ⟨e1, e2⟩ | ⟨e1, e2⟩
      · exact Or.inl ⟨eq_of_mod_div hh e1, eq_of_mod_div (by rw [← hm1, hh, hm2]) e2⟩
      · exact Or.inr ⟨eq_of_mod_div (by rw [hh, hm2]) e1, eq_of_mod_div (by rw [← hm1, hh]) e2⟩

/-- A path whose edges all stay in one copy of `Q_a` projects to an increasing path of `Q_a`. -/
lemma proj_low {l : List ℕ} (hl : IncPath (a + b) (prodLab a b Ba la lb) l)
    (hlow : l.IsChain (fun x y => x / 2 ^ a = y / 2 ^ a)) :
    IncPath a la (l.map (· % 2 ^ a)) := by
  obtain ⟨hn, hc, hi⟩ := hl
  have hconst := const_of_chain hlow
  refine ⟨hn.map_on fun x hx y hy hxy => eq_of_mod_div hxy (hconst x hx y hy), ?_, ?_⟩
  · rw [List.isChain_map]
    refine (isChain_and' hc hlow).imp fun u v ⟨huv, h⟩ => ?_
    rcases adj_split huv with h' | h'
    · exact h'.2
    · exact absurd h h'.2.1
  · clear hn hc hconst
    induction l with
    | nil => trivial
    | cons u l ih =>
      match l, hi, hlow, ih with
      | [], _, _, _ => trivial
      | [_], _, _, _ => trivial
      | v :: w :: l, hi, hlow, ih =>
        refine ⟨?_, ih hlow.tail (inc_tail hi)⟩
        have h1 : u / 2 ^ a = v / 2 ^ a := hlow.rel
        have h2 : v / 2 ^ a = w / 2 ^ a := hlow.tail.rel
        have := hi.1
        rw [prodLab_low h1, prodLab_low h2, ← h1] at this
        exact Nat.lt_of_mul_lt_mul_right (Nat.lt_of_add_lt_add_right this)

/-- A path whose edges all stay in one copy of `Q_b` projects to an increasing path of `Q_b`. -/
lemma proj_high {l : List ℕ} (hl : IncPath (a + b) (prodLab a b Ba la lb) l)
    (hhigh : l.IsChain (fun x y => x / 2 ^ a ≠ y / 2 ^ a)) :
    IncPath b lb (l.map (· / 2 ^ a)) := by
  obtain ⟨hn, hc, hi⟩ := hl
  have hlo : l.IsChain (fun x y => x % 2 ^ a = y % 2 ^ a) :=
    (isChain_and' hc hhigh).imp fun u v ⟨huv, h⟩ =>
      ((adj_split huv).resolve_left fun h' => h h'.1).1
  have hconst := const_of_chain hlo
  refine ⟨hn.map_on fun x hx y hy hxy => eq_of_mod_div (hconst x hx y hy) hxy, ?_, ?_⟩
  · rw [List.isChain_map]
    exact (isChain_and' hc hhigh).imp fun u v ⟨huv, h⟩ =>
      ((adj_split huv).resolve_left fun h' => h h'.1).2.2
  · clear hn hc hconst
    induction l with
    | nil => trivial
    | cons u l ih =>
      match l, hi, hhigh, hlo, ih with
      | [], _, _, _, _ => trivial
      | [_], _, _, _, _ => trivial
      | v :: w :: l, hi, hhigh, hlo, ih =>
        refine ⟨?_, ih hhigh.tail (inc_tail hi) hlo.tail⟩
        have h1 : u / 2 ^ a ≠ v / 2 ^ a := hhigh.rel
        have h2 : v / 2 ^ a ≠ w / 2 ^ a := hhigh.tail.rel
        have e1 : u % 2 ^ a = v % 2 ^ a := hlo.rel
        have := hi.1
        rw [prodLab_high h1, prodLab_high h2, ← e1] at this
        show lb (u / 2 ^ a) (v / 2 ^ a) < lb (v / 2 ^ a) (w / 2 ^ a)
        exact Nat.lt_of_mul_lt_mul_right (Nat.lt_of_add_lt_add_left (Nat.lt_of_add_lt_add_right this))

/-- Every increasing path is a run of `Q_a`-edges followed by a run of `Q_b`-edges. -/
lemma split_path (ha : IsOrdering a Ba la) :
    ∀ {l : List ℕ}, l ≠ [] → IncPath (a + b) (prodLab a b Ba la lb) l →
      ∃ p w q, l = p ++ w :: q ∧ (p ++ [w]).IsChain (fun x y => x / 2 ^ a = y / 2 ^ a) ∧
        (w :: q).IsChain (fun x y => x / 2 ^ a ≠ y / 2 ^ a)
  | [], h, _ => absurd rfl h
  | [v], _, _ => ⟨[], v, [], rfl, List.isChain_singleton _, List.isChain_singleton _⟩
  | v :: x :: rest, _, hl => by
    have htail : IncPath (a + b) (prodLab a b Ba la lb) (x :: rest) :=
      (incPath_append (l₁ := [v]) (l₂ := x :: rest) hl).2
    obtain ⟨p, w, q, hpq, hlow, hhigh⟩ := split_path ha (List.cons_ne_nil _ _) htail
    by_cases hvx : v / 2 ^ a = x / 2 ^ a
    · refine ⟨v :: p, w, q, by rw [hpq]; rfl, ?_, hhigh⟩
      -- `p ++ [w]` starts with `x`
      have hx : (p ++ [w]).head? = some x := by
        cases p with
        | nil => simp only [List.nil_append] at hpq ⊢; simp [(List.cons.inj hpq).1]
        | cons y p => simp only [List.cons_append] at hpq ⊢; simp [(List.cons.inj hpq).1]
      exact List.IsChain.cons hlow (fun y hy => by
        have hy' : y ∈ (p ++ [w]).head? := hy
        rw [hx, Option.mem_def, Option.some.injEq] at hy'
        subst hy'; exact hvx)
    · -- the first edge leaves the `Q_a` block, so every later edge does too
      refine ⟨[], v, x :: rest, rfl, List.isChain_singleton _, ?_⟩
      cases p with
      | nil =>
        simp only [List.nil_append] at hpq
        obtain ⟨rfl, rfl⟩ := List.cons.inj hpq
        exact hhigh.cons_cons hvx
      | cons y p =>
        exfalso
        simp only [List.cons_append] at hpq
        obtain ⟨rfl, hrest⟩ := List.cons.inj hpq
        -- the edge after `x` is a `Q_a`-edge: label `< Ba * 2^b ≤ label of v x`
        obtain ⟨z, rest', rfl⟩ : ∃ z rest', rest = z :: rest' := by
          cases p <;> simp_all
        have hxz : x / 2 ^ a = z / 2 ^ a := by
          cases p with
          | nil => simp at hrest; obtain ⟨rfl, -⟩ := hrest; exact hlow.rel
          | cons z' p => simp at hrest; obtain ⟨rfl, -⟩ := hrest; exact hlow.rel
        have hadj : Adj (a + b) x z := hl.2.1.tail.rel
        have h1 := prodLab_low_lt (lb := lb) ha hadj hxz
        have h2 := hl.2.2.1
        rw [prodLab_high hvx] at h2
        omega

theorem altLE_add {ka kb : ℕ} (ha : AltLE a ka) (hb : AltLE b kb) : AltLE (a + b) (ka + kb) := by
  obtain ⟨Ba, la, hoa, hpa⟩ := ha
  obtain ⟨Bb, lb, hob, hpb⟩ := hb
  refine ⟨_, prodLab a b Ba la lb, isOrdering_prod hoa hob, fun l hl => ?_⟩
  rcases List.eq_nil_or_concat' l with rfl | ⟨_, _, rfl⟩
  · simp
  obtain ⟨p, w, q, hpq, hlow, hhigh⟩ := split_path (lb := lb) hoa (by simp) hl
  rw [hpq] at hl ⊢
  have hparts := incPath_append (l₁ := p ++ [w]) (l₂ := q) (by simpa using hl)
  have hpart2 := (incPath_append (l₁ := p) (l₂ := w :: q) hl).2
  have h1 := hpa _ (proj_low hparts.1 hlow)
  have h2 := hpb _ (proj_high hpart2 hhigh)
  simp only [List.length_map, List.length_append, List.length_cons, List.length_nil] at h1 h2 ⊢
  omega

end Product

/-! ### Base cases -/

theorem altLE_zero : AltLE 0 0 := by
  refine ⟨0, fun _ _ => 0, ⟨fun _ _ h => ?_, fun _ _ h => ?_, fun _ _ _ _ h => ?_⟩, ?_⟩
  all_goals try (obtain ⟨-, -, i, hi, -⟩ := h; omega)
  rintro l ⟨-, hc, -⟩
  match l, hc with
  | [], _ => simp
  | [_], _ => simp
  | _ :: _ :: _, hc => obtain ⟨-, -, i, hi, -⟩ := hc.rel; omega

theorem altLE_one : AltLE 1 1 := by
  refine ⟨1, fun _ _ => 0, ⟨fun _ _ _ => rfl, fun _ _ _ => by omega, ?_⟩, ?_⟩
  · rintro u v x y ⟨hu, hv, i, hi, hne, -⟩ ⟨hx, hy, j, hj, hne', -⟩ -
    have : u ≠ v := fun h => hne (h ▸ rfl)
    have : x ≠ y := fun h => hne' (h ▸ rfl)
    simp only [pow_one] at hu hv hx hy
    omega
  · rintro l ⟨hn, hc, -⟩
    match l, hn, hc with
    | [], _, _ => simp
    | [_], _, _ => simp
    | [_, _], _, _ => simp
    | u :: v :: w :: l, hn, hc =>
      exfalso
      have hu := hc.rel.1
      have hv := hc.rel.2.1
      have hw := hc.tail.rel.2.1
      simp only [pow_one] at hu hv hw
      simp only [List.nodup_cons, List.mem_cons, not_or] at hn
      omega

/-- The explicit ordering of `Q_4` from `AltitudeQ4.lean`. -/
def lab4 (u v : ℕ) : ℕ := AltitudeQ4.labN (min u v) (max u v)

/-- `Adj 4` as a Boolean. -/
def adj4 (u v : ℕ) : Bool := decide (Adj 4 u v)

/-- Boolean check: on `Q_4`, `lab4` is symmetric, `< 33`, and injective on edges. -/
def ordOK : Bool :=
  (List.range 16).all fun u => (List.range 16).all fun v =>
    !adj4 u v || (lab4 u v == lab4 v u && decide (lab4 u v < 33) &&
      (List.range 16).all fun x => (List.range 16).all fun y =>
        !adj4 x y || lab4 u v != lab4 x y || (u == x && v == y) || (u == y && v == x))

/-- Boolean check: no increasing path on 5 distinct vertices in `Q_4`. -/
def pathOK : Bool :=
  (List.range 16).all fun v0 => (List.range 16).all fun v1 => !adj4 v0 v1 ||
  (List.range 16).all fun v2 => !adj4 v1 v2 || !decide (lab4 v0 v1 < lab4 v1 v2) ||
  (List.range 16).all fun v3 => !adj4 v2 v3 || !decide (lab4 v1 v2 < lab4 v2 v3) ||
  (List.range 16).all fun v4 => !adj4 v3 v4 || !decide (lab4 v2 v3 < lab4 v3 v4) ||
    !decide ([v0, v1, v2, v3, v4].Nodup)

lemma ordOK_eq : ordOK = true := by decide +kernel
lemma pathOK_eq : pathOK = true := by decide +kernel

lemma q4_ordering : IsOrdering 4 33 lab4 := by
  have h := ordOK_eq
  simp only [ordOK, List.all_eq_true, List.mem_range, Bool.or_eq_true, Bool.not_eq_true',
    Bool.and_eq_true, beq_iff_eq, decide_eq_true_eq, bne_iff_ne, ne_eq] at h
  have hA : ∀ {u v}, Adj 4 u v → adj4 u v = true := fun huv => decide_eq_true huv
  refine ⟨fun u v huv => ?_, fun u v huv => ?_, fun u v x y huv hxy heq => ?_⟩
  · rcases h u huv.1 v huv.2.1 with h' | h'
    · rw [hA huv] at h'; exact absurd h' (by simp)
    · exact h'.1.1
  · rcases h u huv.1 v huv.2.1 with h' | h'
    · rw [hA huv] at h'; exact absurd h' (by simp)
    · exact h'.1.2
  · rcases h u huv.1 v huv.2.1 with h' | h'
    · rw [hA huv] at h'; exact absurd h' (by simp)
    · rcases h'.2 x hxy.1 y hxy.2.1 with ((h'' | h'') | h'') | h''
      · rw [hA hxy] at h''; exact absurd h'' (by simp)
      · exact absurd heq h''
      · exact Or.inl h''
      · exact Or.inr h''

lemma q4_no_path {v0 v1 v2 v3 v4 : ℕ} (a1 : Adj 4 v0 v1) (a2 : Adj 4 v1 v2) (a3 : Adj 4 v2 v3)
    (a4 : Adj 4 v3 v4) (i1 : lab4 v0 v1 < lab4 v1 v2) (i2 : lab4 v1 v2 < lab4 v2 v3)
    (i3 : lab4 v2 v3 < lab4 v3 v4) (hn : [v0, v1, v2, v3, v4].Nodup) : False := by
  have h := pathOK_eq
  simp only [pathOK, List.all_eq_true, List.mem_range, Bool.or_eq_true, Bool.not_eq_true',
    decide_eq_false_iff_not] at h
  have hA : ∀ {u v}, Adj 4 u v → adj4 u v = true := fun huv => decide_eq_true huv
  rcases h v0 a1.1 v1 a1.2.1 with h | h
  · rw [hA a1] at h; exact absurd h (by simp)
  rcases h v2 a2.2.1 with (h | h) | h
  · rw [hA a2] at h; exact absurd h (by simp)
  · exact h i1
  rcases h v3 a3.2.1 with (h | h) | h
  · rw [hA a3] at h; exact absurd h (by simp)
  · exact h i2
  rcases h v4 a4.2.1 with ((h | h) | h)
  · rw [hA a4] at h; exact absurd h (by simp)
  · exact h i3
  · exact h hn

theorem altLE_four : AltLE 4 3 := by
  refine ⟨33, lab4, q4_ordering, fun l ⟨hn, hc, hi⟩ => ?_⟩
  by_contra hlen
  match l, hn, hc, hi, hlen with
  | v0 :: v1 :: v2 :: v3 :: v4 :: l, hn, hc, hi, _ =>
    exact q4_no_path hc.rel hc.tail.rel hc.tail.tail.rel hc.tail.tail.tail.rel hi.1 hi.2.1
      hi.2.2.1 (hn.sublist (List.sublist_append_left [v0, v1, v2, v3, v4] l))
  | [], _, _, _, h => simp at h
  | [_], _, _, _, h => simp at h
  | [_, _], _, _, _, h => simp at h
  | [_, _, _], _, _, _, h => simp at h
  | [_, _, _, _], _, _, _, h => simp at h

/-! ### Main theorem -/

theorem altLE_four_mul_add (k r : ℕ) : AltLE (4 * k + r) (3 * k + r) := by
  induction r with
  | zero =>
    induction k with
    | zero => exact altLE_zero
    | succ k ih =>
      have := altLE_add ih altLE_four
      rwa [show 4 * k + 0 + 4 = 4 * (k + 1) + 0 by ring,
        show 3 * k + 0 + 3 = 3 * (k + 1) + 0 by ring] at this
  | succ r ih => exact (altLE_add (b := 1) ih altLE_one : AltLE (4 * k + r + 1) (3 * k + r + 1))

/-- **Altitude bound.** `f(Q_d) ≤ d - ⌊d/4⌋` for every `d`. -/
theorem altitude_le (d : ℕ) : AltLE d (d - d / 4) := by
  have := altLE_four_mul_add (d / 4) (d % 4)
  rwa [show 4 * (d / 4) + d % 4 = d by omega, show 3 * (d / 4) + d % 4 = d - d / 4 by omega]
    at this

/-- **`f(Q_d) = d` fails for every `d ≥ 4`:** `Q_d` has an edge-ordering with no increasing
path of `d` edges. -/
theorem altitude_lt (d : ℕ) (hd : 4 ≤ d) :
    ∃ B lab, IsOrdering d B lab ∧ ∀ l, IncPath d lab l → l.length < d + 1 := by
  obtain ⟨B, lab, ho, hp⟩ := altitude_le d
  exact ⟨B, lab, ho, fun l hl => by have := hp l hl; omega⟩

end Altitude
