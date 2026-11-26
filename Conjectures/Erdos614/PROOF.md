# Erdős Problem 614: complete proof of the formula for $k+2 \le n \le (3k+2)/2$

Every step below is mirrored by a Lean lemma; the Lean names are given in brackets. The Lean
development ([`Basic.lean`](Basic.lean), [`Arith.lean`](Arith.lean), [`Claim.lean`](Claim.lean),
[`Main.lean`](Main.lean)) contains no `sorry`/`admit`, and `#print axioms` for the final theorem lists
only Lean's standard `propext`, `Classical.choice`, `Quot.sound`.

## 0. Statement

$f(n,k)$ is the least number of edges of a graph $G$ on $n$ vertices in which every set of $k+2$
vertices induces a subgraph of maximum degree at least $k$ ("$G$ is *good*").

> **Theorem.** If $k+2 \le n$ and $2n \le 3k+2$, then
> $$f(n,k) = \frac{(n-k-1)(n+k-2)}{2}.$$
> [`f_eq`; `erdos_614_of_two_mul_le` restates it with the verbatim formal-conjectures set.]

Throughout, $m = k+2$, $M = m-1 = k+1$, $J = n-m = n-k-2$. The hypothesis $2n \le 3k+2$ is
$2J+3 \le M$, i.e. $m \ge 2J+4$. The formula equals $\frac{(J+1)(2k+J)}{2}$, which is the value
$q(k,2,J) = (J+1)k + \binom{J+1}{2}$ of Erdős–Reid–Schelp–Staton (see the README).

## 1. Notation and elementary lemmas

Fix a graph $H$ (later $H = \overline G$). For a vertex set $S$ and a vertex $v$:

* $d_S(v) = |N(v)\cap S|$ [`degIn`];
* $S$ is a **2-set** if $d_S(v) \ge 2$ for all $v\in S$, i.e. $\delta(H[S]) \ge 2$ [`TwoSet`];
* $D(S) = \sum_{v\in S} d_S(v) = 2e(H[S])$ [`D`].

**L1 (monotone).** $S\subseteq T \Rightarrow d_S(v) \le d_T(v)$. [`degIn_mono`]

**L2 (trivial bounds).** $d_S(v) \le |S|$; if $v\in S$ then $d_S(v)\le |S|-1$; hence
$D(S) \le |S|(|S|-1)$, equivalently $D(S) + |S| \le |S|^2$. [`degIn_le_card`, `D_le`, `D_le'`]

**L3 (disjoint union).** If $A\cap B=\emptyset$ then $d_{A\cup B}(v) = d_A(v) + d_B(v)$. [`degIn_union`]

**L4 (vertex removal).** If $v\in S$ then $D(S) = D(S\setminus v) + 2\,d_S(v)$.
*Proof.* $d_S(w) = d_{S\setminus v}(w) + [w\sim v]$ for every $w$, and
$\sum_{w\in S\setminus v}[w\sim v] = d_S(v)$ because $v\not\sim v$. Split $D(S)$ as
$d_S(v) + \sum_{w \in S\setminus v} d_S(w)$. ∎ [`degIn_erase`, `D_erase`]

**L5 (double counting).** $\sum_{v\in A} d_B(v) = \sum_{w\in B} d_A(w)$; both count pairs
$(v,w)\in A\times B$ with $v\sim w$. [`sum_degIn_comm`]

**L6 (peeling).** If every 2-set $T\subseteq X$ has $|T|\le t$, then
$$D(X) \le \max\bigl(2(|X|-1),\ t(t-1) + 2(|X|-t)\bigr)$$
(natural-number subtraction). [`D_le_of_twoSets_le`]
*Proof.* Induction on $x=|X|$. If $x=0$ then $D(X)=0$. If $1 \le x \le t$, by L2
$D(X) \le x(x-1) \le t(t-1)$. If $x \ge t+1$, then $X$ is not a 2-set (it is too big), so some
$v\in X$ has $d_X(v)\le 1$. By L4, $D(X) = D(X\setminus v) + 2d_X(v) \le B(x-1)+2$, where
$B(y)=\max(2(y-1), t(t-1)+2(y-t))$ is the bound for $X\setminus v$ (all its 2-sets are 2-sets
of $X$). For $x\ge t+1$ we have $B(x-1)+2 \le B(x)$: the second entries satisfy
$t(t-1)+2(x-1-t)+2 = t(t-1)+2(x-t)$ since $x-1 \ge t$. The first entries satisfy
$2(x-2)+2 = 2(x-1)$ when $x\ge 2$, and when $x=1$ we have $t=0$ and $2(0)+2 = 2 = 0+2(1-0)$. ∎

**L7.** For $1\le a\le L$: $\max(2(L-1),\,a(a-1)+2(L-a)) + 3a \le a^2 + 2L$. [`max_peel_le`]
*Proof.* Write $a=b+1$. Both entries plus $3a$ are at most $a^2+2L$: the first because
$2(L-1)+3(b+1) \le (b+1)^2+2L \iff b \le b^2$, and the second with equality. ∎

## 2. The complement form

**Lemma 2.1 (reformulation).** [`not_twoSet_compl_of_good`, `card_adj_add_card_compl_adj`]
For $v\in S$, $|N_G(v)\cap S| + |N_{\overline G}(v)\cap S| = |S|-1$. Hence, for $|S| = k+2$, a vertex
has $G[S]$-degree $\ge k$ iff it has $\overline G[S]$-degree $\le 1$. So **$G$ is good iff
$\overline G$ has no 2-set of size $m=k+2$.** (This reformulation is not new: see Tang–Ma, linked from the
erdosproblems.com forum, 7 Jan 2026.) Only the forward direction is used below.

**Lemma 2.2 (degree sums).** For any $G$ on $n$ vertices, $2e(G) + D_{\overline G}(V) = n(n-1)$.
This holds because $\deg_G(v) + \deg_{\overline G}(v) = n-1$ for each $v$. [`two_mul_card_edges_add_D_compl`]

## 3. The main claim

> **Claim.** Let $M\ge 0$, $J\ge 0$ with $2J+3 \le M$. Let $U$ be a vertex set with $|U| = M+1+J$
> such that no $(M+1)$-subset of $U$ is a 2-set. Then
> $$D(U) + M \le M^2 + 2J + 2,\qquad\text{i.e.}\quad e(H[U]) \le \tbinom{M}{2} + J + 1.$$
> [`claim`]

*Proof.* Induction on $J$ (for all $U$ at once).

**$J=0$.** $U$ itself has size $M+1$, so it is not a 2-set and some $v\in U$ has $d_U(v)\le 1$.
By L4 and L2, $D(U) = D(U\setminus v) + 2d_U(v) \le (M^2 - M) + 2$.

**$J\to J+1$, low-degree vertex.** If some $v\in U$ has $d_U(v)\le 1$, then $U\setminus v$
($|U\setminus v| = M+1+J$, $2J+3\le M$) satisfies the hypotheses, so by induction
$D(U\setminus v) + M \le M^2+2J+2$. By L4, $D(U)+M \le M^2 + 2(J+1) + 2$.

**$J\to J+1$, main case.** Otherwise every vertex of $U$ has $d_U \ge 2$. This case is Theorem 3.1
below, applied with $J+1$ in place of $J$ (note $2(J+1)+3 \le M$). ∎

> **Theorem 3.1 (main case).** [`main_case`] Assume additionally $J\ge 1$ and $d_U(v)\ge 2$ for all
> $v\in U$. Then $D(U)+M \le M^2+2J+2$.

*Proof.* Let $F = \{v\in U : d_U(v) \ge J+2\}$ and $L = U\setminus F$, with $f = |F|$. Every
$w\in L$ has $2 \le d_U(w) \le J+1$.

**Fact A (free vertices).** If $S\subseteq U$, $|U| = |S| + J$, $v\in S$ and $d_U(v)\ge J+2$, then
$d_S(v)\ge 2$. Indeed $d_U(v) = d_S(v) + d_{U\setminus S}(v) \le d_S(v) + J$ by L3 and L2.
[`two_le_degIn_of_free`]

**Fact B (gluing).** There are no $W\subseteq L$, $Y\subseteq F$ with
$|W|+|Y|\le M+1 \le |W|+f$ and $d_{W\cup Y}(w)\ge 2$ for all $w\in W$.
To see this, pick $Y'\subseteq F\setminus Y$ with $|Y'| = M+1-|W|-|Y|$. This is possible since
$|F\setminus Y| = f - |Y| \ge M+1-|W|-|Y|$. Then $S = W\cup Y\cup Y'$ is a disjoint union of size
$M+1$ inside $U$:
- each $w\in W$ has $d_S(w)\ge d_{W\cup Y}(w)\ge 2$ (L1);
- each $v\in Y\cup Y'\subseteq F$ has $d_S(v)\ge 2$ by Fact A, since $|U| = |S|+J$.

So $S$ is a forbidden 2-set. [`glue`]

**$f\le M$.** Otherwise take $Y \subseteq F$, $|Y| = M+1$, $W = \emptyset$ in Fact B.

Write $a = M - f \ge 0$; then $|L| = |U| - f = J+1+a$.

**Fact C (few good vertices).** Let $\Gamma = \{w\in L : d_F(w)\ge 2\}$ ("good"), with $\gamma=|\Gamma|$.
Then $\gamma\le a$. Otherwise take $W\subseteq\Gamma$ with $|W|=a+1$ and $Y=F$ in Fact B: then
$|W|+|Y| = M+1$, and $d_{W\cup F}(w)\ge d_F(w)\ge 2$.

**Bound on $X := \sum_{w\in L} d_F(w)$.** Put $s = \min(f, J+1)$. For $w\in\Gamma$:
$d_F(w)\le |F| = f$ and $d_F(w)\le d_U(w)\le J+1$, so $d_F(w)\le s$. For $w\in L\setminus\Gamma$:
$d_F(w)\le 1$. Hence
$$X + \gamma \le \gamma s + |L|. \tag{X}$$

**Decompositions.** By L3, $d_U = d_F + d_L$. Summing over $U = F\sqcup L$ and using L5
($\sum_{F} d_L = \sum_L d_F = X$):
$$D(U) = D(F) + 2X + D(L), \qquad \sum_{w\in L} d_U(w) = X + D(L). \tag{Dec}$$
Also $\sum_{w\in L} d_U(w) \le (J+1)|L|$, and $D(F) + f\le f^2$ (L2).

**Case $a = 0$** (so $f = M$, $|L| = J+1$, $\gamma = 0$, and (X) gives $X\le |L|$).
Let $Y = \{y\in F : y\sim w$ for some $w\in L\}$. Then $|Y|\le \sum_{w\in L} d_F(w) = X \le J+1$.
Apply Fact B with $W = L$:
- $|L|+|Y| \le 2J+2 \le M+1$;
- $|L| + f = |U| \ge M+1$;
- every neighbour (in $U$) of $w\in L$ lies in $L\cup Y$, so $d_{L\cup Y}(w) = d_U(w)\ge 2$.

This is a contradiction, so this case cannot occur.

**Case I: $1\le a\le J$.** Here $f = M-a \ge 2J+3-J \ge J$, so $|L| = J+1+a\le M+1$. Every 2-set
$T\subseteq L$ has $|T|\le a$: if $|T|\ge a+1$, apply Fact B with $W=T$, $Y=\emptyset$, since
$|T|\le|L|\le M+1$ and $|T|+f\ge M+1$. By L6 with $t=a$ and then L7,
$$D(L) + 3a \le a^2 + 2|L|.$$
Now (Arith, `arith_caseI`) write $L = |L| = J+1+a$. From $\gamma s\le \gamma(J+1)$, (X) gives
$X\le \gamma J + L\le aJ + L$. Using (Dec),
$$D(U) + M \le (f^2-f) + 2(aJ+L) + (a^2+2L-3a) + (f+a) = f^2+a^2+2aJ+4J+4+2a .$$
The target is $M^2+2J+2 = f^2+2fa+a^2+2J+2$, so it suffices that $(a+1)(J+1)\le fa$. Since
$f\ge 2J+3-a$, we have $fa - (a+1)(J+1) \ge (2J+3-a)a-(a+1)(J+1) = (a-1)(J+1-a)\ge 0$.

**Case II: $a\ge J+1$** (Arith, `arith_caseII`). By (Dec),
$D(U) = D(F) + X + \sum_{L} d_U \le (f^2-f) + (\gamma s-\gamma+L) + (J+1)L$, so
$$D(U)+M \le f^2 + (\gamma s - \gamma) + (J+2)(J+1+a) + a,$$
and it suffices that $(\gamma s-\gamma) + J^2+J+a(J+3) \le 2fa + a^2$.

* If $f\le J+1$, then $a \ge 2J+3-f \ge J+2$. Using $\gamma s \le af$ (as $\gamma\le a$, $s\le f$) and
  $-\gamma\le 0$, it suffices that $J^2+J+a(J+3)\le a(f+a)$. This holds because
  $a(f+a)\ge a(2J+3)$ and $aJ\ge (J+2)J\ge J^2+J$.
* If $f\ge J+1$, then $\gamma s - \gamma \le \gamma J\le aJ$, and it suffices that
  $J^2+J+a(2J+3)\le 2fa+a^2$. Write $a = J+1+p$, $f=J+1+q$ with $p,q\ge 0$. Then
  $2fa+a^2-a(2J+3) = a(J+p+2q) \ge (J+1)J$.

All cases give $D(U)+M\le M^2+2J+2$. ∎

## 4. From the claim to $f(n,k)$

**Lower bound** [`le_of_good`]. Let $G$ on $V$, $|V|=n$, be good, and put $H=\overline G$. By Lemma 2.1,
$H$ has no 2-set of size $m = k+2$. Apply the Claim with $M = k+1$, $J = n-k-2$ (valid since
$2J+3\le M \iff 2n\le 3k+2$), $U=V$: $D_H(V) + (k+1) \le (k+1)^2 + 2J + 2$. By Lemma 2.2,
$$2e(G) = n(n-1) - D_H(V) \ge n(n-1) - (k+1)^2 - 2J - 2 + (k+1) = (J+1)(2k+J) = (n-k-1)(n+k-2).$$
(Substitute $n = k+2+J$ and expand.)

**Upper bound: the extremal graph** [`G₀`, `G₀_good`, `G₀_edges`]. On $V=\{0,1,\dots,n-1\}$, let
$G_0$ join $u\ne v$ iff $u\ne 0$, $v\ne 0$, and $\max(u,v) > k$. Its complement is a clique on
$\{0,\dots,k\}$ with every vertex $>k$ joined only to $0$.

* *$G_0$ is good.* Let $|S| = k+2$. Since $\{0,\dots,k\}$ has only $k+1$ elements, some $p\in S$ has
  $p>k$. Every $w\in S\setminus\{p\}$ with $w\ne 0$ is a $G_0$-neighbour of $p$, and at most one
  element of $S$ equals $0$. So $p$ has at least $(k+1)-1 = k$ neighbours in $S$.
* *$2e(G_0)\le (n-k-1)(n+k-2)$.* The degrees are: vertex $0$ has degree $0$; a vertex
  $1\le v\le k$ has all its neighbours in $\{k+1,\dots,n-1\}$, so degree $\le n-k-1$; a vertex
  $v>k$ has degree $\le n-2$, since $v$ and $0$ are excluded. There are at most $k$ vertices of the
  middle kind and at most $n-k-1$ of the last kind, so
  $2e(G_0) = \sum_v \deg v \le k(n-k-1) + (n-k-1)(n-2) = (n-k-1)(n+k-2)$.

**Conclusion** [`f_eq`]. Every good graph has $2e \ge P := (n-k-1)(n+k-2)$. The good graph $G_0$ has
$2e(G_0)\le P$, so $2e(G_0) = P$ (in particular $P$ is even) and $e(G_0) = P/2$ is the minimum. ∎

## 5. Sharpness for $n \ge 2k+1$ (Proposition 3)

> **Proposition.** For every $k\ge 2$ and every $n\ge 2k+1$:
> $f(n,k) \le \frac{(n-k-1)(n+k-2)}{2} - 1$.

*Construction (complement form, $m=k+2$).* $H$ consists of:
- a clique $Q$ on $m-1=k+1$ vertices, containing a vertex $z_0$;
- a cycle $z_0 z_1\cdots z_{k}z_0$ of length $k+1$ (so $z_1,\dots,z_k$ are new; $k\ge 2$ makes it a
  genuine cycle);
- $n-2k-1$ further vertices, each joined only to $z_0$ (pendants).

Then $e(H) = \binom{k+1}2 + (k+1) + (n-2k-1)$, which is one more than
$\binom{m-1}{2} + n-m+1 = \binom{k+1}2 + n-k-1$. So $G = \overline H$ has one edge fewer than the
formula.

*$H$ has no 2-set of size $m$.* Let $S$ be a 2-set.
1. A pendant has degree $\le 1$ in every induced subgraph, so $S$ contains no pendant.
2. Let $P = S\cap\{z_1,\dots,z_k\}$. If $P$ is nonempty but proper, choose $z_i\in P$ next (along the
   path $z_1\cdots z_k$) to a $z_j\notin S$. The only neighbours of $z_i$ are its two cycle
   neighbours, one of which is $z_j$, so $d_S(z_i)\le 1$. That is a contradiction.
3. If $P=\emptyset$, then $S\subseteq Q$ and $|S|\le k+1 < m$.
4. If $P$ is the whole path, then $z_0\in S$ (it is $z_1$'s second neighbour). Moreover
   $S\cap Q=\{z_0\}$ or $|S\cap Q|\ge 3$, because a single other clique vertex would have
   $d_S = 1$. So $|S| = k+1$ or $|S|\ge k+3$.

In no case is $|S| = k+2 = m$. ∎

*Verification.* The construction was checked by brute force from the original definition (on $G$,
not on $H$), with the edge count, for every $k = 2,\dots,15$ at $n=2k+1$ (up to $2.65\times 10^8$
subsets), for $k\le 14$ at $n=2k+2$ and for $k\le 13$ at $n=2k+4$ (`computations/sharpness.c`). This
proposition is **not** formalized in Lean.

Since Pikhurko–Thomason's Theorem 13 gives failure of the formula only when $k<l=n-k-2$, i.e.
$n\ge 2k+3$, the cases $n = 2k+1,\,2k+2$ are, as far as I could find, not covered in the literature.
Together with Theorem 13 and this proposition, the formula fails for **every** $n\ge 2k+1$ ($k\ge2$).
So for $j=2$ the threshold $n \le 2k$ in the Erdős–Reid–Schelp–Staton conjecture cannot be enlarged.
