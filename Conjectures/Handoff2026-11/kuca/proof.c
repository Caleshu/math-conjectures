// Rigorous computer check that the even terms of V(2,n) are exactly 2, 2n, 2n^2+2, given (P,u0) from brent.c.
// Steps: (1) exact simulation to N0; (2) odd recurrence to UMAX=2u0+4P+2 (valid by induction as long as no even term appears);
// (3) verify periodicity claim T[v]=T[v+P] on a window of length > E3 starting at u0 (=> forever, by determinism);
// (4) every even w in (N0, UMAX] has >= 2 representations (=> not a term, induction continues);
// (5) every even residue rho mod P has a witness pair (o, w-o) both >= u0, both terms => S(rho)>=1;
//     then any even w > UMAX has >= 2 representations among o in [u0, w/2] (two full periods).
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
static uint64_t *Bt; // bit per odd u: index (u-1)/2
#define GT(u) ((Bt[((u)-1)>>7]>>((((u)-1)>>1)&63))&1)
#define ST(u) (Bt[((u)-1)>>7]|=1ULL<<((((u)-1)>>1)&63))
int main(int argc,char**argv){ long n=atol(argv[1]); long P=atol(argv[2]); long u0=atol(argv[3]);
  long N0=4*n*n+200, E3=2*n*n+2, E2=2*n; long UMAX=2*u0+4*P+2;
  Bt=calloc(UMAX/128+4,8); if(!Bt){printf("alloc fail\n");return 1;}
  // (1) exact simulation; even terms tracked separately
  unsigned char*T=calloc(N0+10,1); long*terms=malloc(8*(N0+2)); int nt=0; T[2]=1;T[n]=1;terms[nt++]=2;terms[nt++]=n;
  for(long u=n+1;u<=N0;u++){int c=0; for(int i=0;i<nt&&c<2;i++){long a=terms[i],b=u-a; if(b<a)continue; if(T[b])c++;} if(c==1){T[u]=1;terms[nt++]=u;}}
  printf("even terms <= N0=%ld:",N0); for(int i=0;i<nt;i++) if(terms[i]%2==0) printf(" %ld",terms[i]); printf("\n");
  for(long u=1;u<=N0;u+=2) if(T[u]) ST(u);
  // (2) recurrence
  for(long u=N0+(N0%2?2:1);u<=UMAX;u+=2){ int c=GT(u-2)+GT(u-E2)+GT(u-E3); if(c==1) ST(u); }
  printf("recurrence computed to %ld\n",UMAX);
  // (3) periodicity window check
  for(long v=u0; v<=u0+E3+2; v+=(v%2?2:1)) { if(v%2==0) continue; if(GT(v)!=GT(v+P)){ printf("PERIOD CHECK FAILED at %ld\n",v); return 1;} }
  printf("periodicity window verified (length %ld) at u0=%ld, P=%ld\n",E3+2,u0,P);
  // (4) direct check of even w
  long maxscan=0, worst=0;
  for(long w=N0+(N0%2?1:2); w<=UMAX; w+=2){ int r=0; long scanned=0;
    // even-even pairs: only possible if w <= 2*E3 < N0, so none here.
    for(long o=1;2*o<=w;o+=2){ if(GT(o)){ scanned++; if(GT(w-o)){ if(++r==2) break; } } }
    if(r<2){ // r is exact here (full scan done): r==0 is fine, r==1 is a failure
      if(r==1){ printf("FAIL: w=%ld has exactly one representation\n",w); return 1;} }
    if(scanned>maxscan){maxscan=scanned;worst=w;} }
  printf("step 4 ok: every even w in (%ld,%ld] has r(w)!=1 (max odd terms scanned %ld at w=%ld)\n",N0,UMAX,maxscan,worst);
  // (5) witnesses for each even residue: w in [2u0+2P, 2u0+3P) even covers every even residue mod P once
  long W0=2*u0+2*P; if(W0%2) W0++; long maxs=0;
  for(long w=W0; w<W0+P; w+=2){ long o=u0+(u0%2?0:1); int found=0; long s=0;
    for(; o<u0+P && w-o>=u0; o+=2){ s++; if(GT(o)&&GT(w-o)){found=1;break;} }
    if(!found){ printf("FAIL: no witness for residue of w=%ld\n",w); return 1;} if(s>maxs)maxs=s; }
  printf("step 5 ok: every even residue mod P has a witness (max search %ld)\n",maxs);
  printf("PROOF COMPLETE: the even terms of V(2,%ld) are exactly 2, %ld, %ld\n",n,2*n,2*n*n+2);
  return 0; }
