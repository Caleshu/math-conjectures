// Computer proof that V(2,n) has exactly the even terms 2, 2n, 2n^2+2 (n odd, n-1 a power of 2).
// 1. Generate V(2,n) by the greedy rule up to L.  2. Check even terms = E.
// 3. Odd rule: for odd u > max E, u in S iff exactly one of u-e (e in E) in S (given even terms = E).
//    Find T,P with state(T) = state(T+P) (window of length maxE), so odd terms are P-periodic from T on.
// 4. For each even residue class rho mod P, count c(rho) = #{odd a in [T,T+P): S(a), S(rep(rho-a))} >= 2.
//    Then every even m >= 2(T+P) has >= 2 representations as a sum of two odd terms -> not a term.
// 5. Even m <= L checked directly by step 2 (need L >= 2(T+P)).
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int c,char**v){ long n=atol(v[1]); long L=atol(v[2]);
  char *in=calloc(L+1,1);
  long *ev=malloc(sizeof(long)*64), ne=0; long *od=malloc(sizeof(long)*(L/2+2)), no=0; long nt=0;
  long E[3]={2,2*n,2*n*n+2}, maxE=E[2]; int ok=1;
  in[2]=1; ev[ne++]=2; in[n]=1; if(n%2) od[no++]=n; else ev[ne++]=n; nt=2;
  for(long m=n+1;m<=L;m++){
    // number of representations m = a + b, a <= b, a,b terms (all terms are < m), capped at 2
    int r=0;
    if(m&1){ for(long i=0;i<ne && r<2;i++){ long b=m-ev[i]; if(b>0 && in[b]) r++; } }   // even + odd
    else {
      for(long i=0;i<ne && r<2;i++) for(long j=i;j<ne && r<2;j++) if(ev[i]+ev[j]==m) r++;   // even + even
      for(long i=0;i<no && r<2 && 2*od[i]<=m;i++){ if(in[m-od[i]]) r++; }               // odd + odd
    }
    if(r==1){ in[m]=1; nt++; if(m&1) od[no++]=m; else { ev[ne++]=m; if(m!=E[1] && m!=E[2]){ printf("n=%ld: EXTRA even term %ld\n",n,m); ok=0; if(ne>60) return 1; } } }
  }
  for(int i=0;i<3;i++) if(!in[E[i]]){ printf("n=%ld: missing even term %ld\n",n,E[i]); ok=0; }
  printf("n=%ld: generated %ld terms up to %ld; even terms OK: %s\n",n,nt,L,ok?"yes":"NO");
  // odd rule check
  long bad=0; for(long u=maxE+1; u<=L; u+=2){ int k=in[u-E[0]]+in[u-E[1]]+in[u-E[2]]; if(in[u]!=(k==1)) bad++; }
  printf("  odd-rule violations above %ld: %ld\n",maxE,bad);
  // find period: smallest P (even) and T such that the window [T-maxE, T) equals [T+P-maxE, T+P)
  long T=maxE+1+((maxE+1)%2==0); // odd
  long bestP=-1, bestT=-1;
  for(long Tc=T; Tc< L/4 && bestP<0; Tc+= (L/400>2? (L/400)|1 : 2)) {
    for(long P=2; Tc+P+maxE < L/2; P+=2){
      if(memcmp(in+Tc-maxE, in+Tc+P-maxE, maxE)==0){ bestP=P; bestT=Tc; break; }
    }
  }
  if(bestP<0){ printf("  no period found within L\n"); return 1; }
  // state at T and T+P equal (window of length maxE before T) => odd terms periodic from T (deterministic rule)
  // refine T downward is not needed. check periodicity on data as sanity
  long pv=0; for(long u=bestT; u+bestP<=L; u++) if((u&1) && in[u]!=in[u+bestP]) pv++;
  printf("  period P=%ld from T=%ld (window %ld); periodicity violations in data: %ld\n",bestP,bestT,maxE,pv);
  long need=2*(bestT+bestP);
  if(need> L){ printf("  need L >= %ld\n",need); return 1; }
  // residue counts
  long minc=1L<<60, argmin=-1;
  for(long rho=0; rho<bestP; rho+=2){
    long cc=0;
    for(long a=bestT; a<bestT+bestP; a++){ if(!(a&1) || !in[a]) continue;
      long b = rho - a; b %= bestP; if(b<0) b+=bestP;   // b = (m - a) mod P
      // representative of (m-a) in window [T, T+P): r = T + ((b - T) mod P)
      long r = bestT + (((b - bestT) % bestP) + bestP) % bestP;
      if(in[r]) cc++; }
    if(cc<minc){minc=cc; argmin=rho;} }
  printf("  min over even residues of #(a in window, both odd terms) = %ld (at residue %ld)\n",minc,argmin);
  printf("  => %s: every even m >= %ld has >= 2 odd representations; even m <= %ld checked directly\n",
     (ok && bad==0 && pv==0 && minc>=2)?"PROOF OK":"PROOF FAILS", need, L);
}
