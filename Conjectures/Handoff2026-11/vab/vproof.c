// Computer-assisted proof that V(a,b) (a even, b odd, gcd=1) has finitely many even terms (=> eventually periodic,
// i.e. a finite union of APs plus finitely many terms). V: next term = least integer > last with exactly one
// representation as a sum of two earlier terms (not necessarily distinct).
// Usage: ./vproof a b N0 maxsteps maxP
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
static uint64_t *Bt;
#define GT(u) ((Bt[((u)-1)>>7]>>((((u)-1)>>1)&63))&1)
#define ST(u) (Bt[((u)-1)>>7]|=1ULL<<((((u)-1)>>1)&63))
#define MAXE 256
#define MAXW 1024
typedef struct { uint64_t w[MAXW]; } St;
static int L,NW,ne; static long E[MAXE]; static int off[MAXE];
static inline int getb(const St*s,int k){ return (s->w[k>>6]>>(k&63))&1; }
static inline void push(St*s,int b){ for(int i=NW-1;i>0;i--) s->w[i]=(s->w[i]<<1)|(s->w[i-1]>>63); s->w[0]=(s->w[0]<<1)|b; int top=L&63; if(top) s->w[NW-1]&=((1ULL<<top)-1); }
static inline void step(St*s){ int c=0; for(int i=0;i<ne;i++) c+=getb(s,off[i]); push(s,c==1); }
static int cmpst(const St*a,const St*b){ return memcmp(a->w,b->w,8*NW); }
int main(int argc,char**argv){ long a=atol(argv[1]),b=atol(argv[2]),N0=atol(argv[3]); double maxsteps=atof(argv[4]); long maxP=(long)atof(argv[5]);
  // ---- exact simulation to N0 (exact: odd u only has even+odd reps; even u has even+even and odd+odd reps)
  unsigned char*T=calloc(N0+2,1); long*odds=malloc(8*(N0/2+2)); long no=0; ne=0;
  T[a]=1; T[b]=1; E[ne++]=a; odds[no++]=b;
  for(long u=b+1;u<=N0;u++){ int c=0;
    if(u&1){ for(int i=0;i<ne&&c<2;i++) if(u-E[i]>0 && T[u-E[i]]) c++; }
    else { for(int i=0;i<ne;i++) for(int j=i;j<ne;j++) if(E[i]+E[j]==u) c++;
           for(long i=0;i<no && 2*odds[i]<=u && c<2;i++) if(T[u-odds[i]]) c++; }
    if(c==1){ T[u]=1; if(u&1) odds[no++]=u; else { if(ne>=MAXE){printf("V(%ld,%ld): too many even terms (>%d) by N0\n",a,b,MAXE);return 2;} E[ne++]=u; } } }
  long M=E[ne-1];
  printf("V(%ld,%ld): %d even terms <= %ld:",a,b,ne,N0); for(int i=0;i<ne&&i<12;i++) printf(" %ld",E[i]); if(ne>12) printf(" ..."); printf(" (max %ld)\n",M);
  if(N0 < 4*M+1000){ printf("  N0 too small relative to max even term; inconclusive\n"); return 3; }
  // ---- Brent on odd register; bit k = T[u-2k-2]... define state at odd u = bits T[u], T[u-2], ..., T[u-2(L-1)]; next bit for u+2:
  // T[u+2] = [ sum_e T[u+2-e] == 1 ], u+2-e = u - 2*(e/2 - 1) -> offset k = e/2 - 1.
  L=(int)(M/2); NW=(L+63)/64; if(NW>MAXW){printf("  register too long\n");return 4;}
  for(int i=0;i<ne;i++) off[i]=(int)(E[i]/2-1);
  long uS=(N0&1)?N0:N0-1; St s; memset(&s,0,sizeof s); for(int k=L-1;k>=0;k--) push(&s,T[uS-2*k]);
  St tort=s,hare=s; step(&hare); long power=1,lam=1;
  while(cmpst(&tort,&hare)){ if(power==lam){ tort=hare; power*=2; lam=0; if(power>maxsteps){ printf("  no cycle found with period <= %.2g odd-steps; inconclusive\n",maxsteps); return 5; } } step(&hare); lam++; }
  St x=s,y=s; for(long i=0;i<lam;i++) step(&y); long mu=0; while(cmpst(&x,&y)){ step(&x);step(&y);mu++; }
  long P=2*lam; long u0=uS+2*mu-2*(L-1); if(u0<=N0) u0=N0+1+((N0+1)%2==0); // conservative: periodicity holds from max(start, >N0)
  printf("  odd register: period P=%ld, periodic from u0=%ld\n",P,u0);
  if(P>maxP){ printf("  period too large for the even check; inconclusive\n"); return 6; }
  // ---- proof checks
  long UMAX=2*u0+4*P+2; if(UMAX<N0) UMAX=N0;
  Bt=calloc(UMAX/128+4,8); if(!Bt){printf("alloc\n");return 7;}
  for(long u=1;u<=N0;u+=2) if(T[u]) ST(u);
  for(long u=uS+2;u<=UMAX;u+=2){ int c=0; for(int i=0;i<ne;i++) c+=GT(u-E[i]); if(c==1) ST(u); }
  long u0o=(u0&1)?u0:u0+1;
  for(long v=u0o; v<=u0o+M+2; v+=2) if(GT(v)!=GT(v+P)){ printf("  PERIOD CHECK FAILED\n"); return 8; }
  for(long w=(N0&1)?N0+1:N0+2; w<=UMAX; w+=2){ int r=0; for(long o=1;2*o<=w;o+=2) if(GT(o)&&GT(w-o)){ if(++r==2) break; } if(r==1){ printf("  FAIL: even w=%ld has a unique representation\n",w); return 9; } }
  long W0=2*u0o+2*P; for(long w=W0; w<W0+P; w+=2){ int f=0; for(long o=u0o; o<u0o+P && w-o>=u0o; o+=2) if(GT(o)&&GT(w-o)){f=1;break;} if(!f){ printf("  FAIL: residue of %ld has no witness\n",w); return 10; } }
  long cnt=0; for(long v=u0o; v<u0o+P; v+=2) cnt+=GT(v);
  printf("  PROVED: V(%ld,%ld) has exactly %d even terms; odd part periodic with period %ld (%ld odd terms per period)\n",a,b,ne,P,cnt);
  return 0; }
