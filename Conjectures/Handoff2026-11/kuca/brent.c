// Brent cycle detection on the odd-term shift register of V(2,n), assuming evens {2,2n,2n^2+2}.
// State: last L = n^2+1 odd-position bits (u-2, u-4, ..., u-E3). Multiword. New bit = [b(1)+b(n)+b(L)==1].
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#define MAXW 64
typedef struct { uint64_t w[MAXW]; } St;
static int L, NW;
static inline int getb(const St*s,int k){ return (s->w[k>>6]>>(k&63))&1; } // k=0 is most recent
static inline void push(St*s,int b){ // shift: bit k -> k+1
  for(int i=NW-1;i>0;i--) s->w[i]=(s->w[i]<<1)|(s->w[i-1]>>63); s->w[0]=(s->w[0]<<1)|b;
  int top=L&63; if(top) s->w[NW-1]&=((1ULL<<top)-1); }
static inline void step(St*s,long n){ int b=getb(s,0)+getb(s,n-1)+getb(s,L-1); push(s,b==1); }
int main(int argc,char**argv){ long n=atol(argv[1]); double maxsteps=atof(argv[2]); long N0=4*n*n+200;
  L=n*n+1; NW=(L+63)/64; if(NW>MAXW) return 1;
  unsigned char*T=calloc(N0+10,1); long*terms=malloc(8*(N0+2)); int nt=0; T[2]=1;T[n]=1;terms[nt++]=2;terms[nt++]=n;
  for(long u=n+1;u<=N0;u++){int c=0; for(int i=0;i<nt&&c<2;i++){long a=terms[i],b=u-a; if(b<a)continue; if(T[b])c++;} if(c==1){T[u]=1;terms[nt++]=u;}}
  long uS = (N0%2)? N0 : N0-1; // last odd <= N0; state = bits T[uS], T[uS-2], ...
  St s; memset(&s,0,sizeof s); for(int k=L-1;k>=0;k--) push(&s,T[uS-2*k]);
  // Brent
  St tort=s; long power=1, lam=1; St hare=s; step(&hare,n); double steps=1;
  while(memcmp(&tort,&hare,sizeof(St))){ if(power==lam){ tort=hare; power*=2; lam=0; if(power>maxsteps){ printf("n=%ld: no cycle with period <= %.3g (odd steps)\n",n,maxsteps); return 0;} }
    step(&hare,n); lam++; steps++; }
  printf("n=%ld: period lambda=%ld odd-steps (P=%ld in u)\n",n,lam,2*lam);
  // find mu
  St a=s,b=s; for(long i=0;i<lam;i++) step(&b,n); long mu=0; while(memcmp(&a,&b,sizeof(St))){ step(&a,n);step(&b,n);mu++; }
  printf("n=%ld: preperiod mu=%ld odd-steps after u=%ld => periodic from u0=%ld\n",n,mu,uS,uS+2*mu-2*(L-1));
  return 0; }
