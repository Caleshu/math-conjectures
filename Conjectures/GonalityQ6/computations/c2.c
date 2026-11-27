// Chip-firing on hypercube Q_n: positive-rank test + exhaustive / annealing search.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define MAXN 64
int n, N, deg;
int adj[MAXN][8];

static unsigned long long rs = 88172645463325252ULL;
static inline unsigned long long xr(void){ rs^=rs<<13; rs^=rs>>7; rs^=rs<<17; return rs; }
static inline double ur(void){ return (xr()>>11)*(1.0/9007199254740992.0); }

// v-reduce an effective divisor D in place (D nonneg everywhere). Returns D[q] after reduction.
int reduce(int *D, int q){
  int burnt[MAXN], cnt[MAXN];
  for(;;){
    memset(burnt,0,sizeof burnt); memset(cnt,0,sizeof cnt);
    int stack[MAXN], sp=0; burnt[q]=1; stack[sp++]=q; int nb=1;
    while(sp){
      int u=stack[--sp];
      for(int k=0;k<deg;k++){int w=adj[u][k]; if(burnt[w]) continue;
        if(++cnt[w] > D[w]){ burnt[w]=1; stack[sp++]=w; nb++; } }
    }
    if(nb==N) return D[q];
    // fire unburnt set U as many times as legal
    int times=1<<30;
    for(int u=0;u<N;u++) if(!burnt[u] && cnt[u]>0){ int t=D[u]/cnt[u]; if(t<times) times=t; }
    for(int u=0;u<N;u++) if(!burnt[u]){
      D[u]-=times*cnt[u];
      for(int k=0;k<deg;k++){int w=adj[u][k]; if(burnt[w]) D[w]+=times;}
    }
  }
}
// number of vertices v where the opponent wins (D-v not winnable)
int fails(const int *D, int stopat){
  int f=0, T[MAXN];
  for(int v=0;v<N;v++){ if(D[v]>0) continue;
    memcpy(T,D,sizeof(int)*N);
    if(reduce(T,v)==0){ if(++f>=stopat) return f; } }
  return f;
}
// exhaustive: enumerate all multisets of size d with D[0]>=1 (vertex-transitive: some vertex has a chip)
long long checked=0; int found=0; int Dg[MAXN];
void rec(int pos, int left){
  if(found) return;
  if(pos==N-1){ Dg[pos]=left; checked++; if(fails(Dg,1)==0){found=1;
      printf("WINNER:"); for(int i=0;i<N;i++) printf(" %d",Dg[i]); printf("\n");} return; }
  int lo = (pos==0)?1:0;
  for(int c=lo;c<=left;c++){ Dg[pos]=c; rec(pos+1,left-c); if(found) return; }
}
int main_old(int argc,char**argv){
  n=atoi(argv[1]); N=1<<n; deg=n;
  for(int v=0;v<N;v++) for(int k=0;k<n;k++) adj[v][k]=v^(1<<k);
  const char*mode=argv[2]; int d=atoi(argv[3]);
  if(!strcmp(mode,"exh")){ rec(0,d); printf("n=%d d=%d checked=%lld winner_found=%d\n",n,d,checked,found); return 0; }
  // anneal: args seed iters T0
  rs ^= (unsigned long long)atoll(argv[4])*0x9E3779B97F4A7C15ULL; for(int i=0;i<10;i++) xr();
  long long iters=atoll(argv[5]); double T0=atof(argv[6]);
  int D[MAXN]={0}; for(int i=0;i<d;i++) D[xr()%N]++;
  int f=fails(D,N), best=f; int B[MAXN]; memcpy(B,D,sizeof B);
  for(long long it=0; it<iters && best>0; it++){
    double T=T0*(1.0-(double)it/iters)+1e-3;
    int E[MAXN]; memcpy(E,D,sizeof E);
    double r=ur();
    if(r<0.05){ reduce(E, xr()%N); }               // jump to an equivalent divisor
    else { int a; do a=xr()%N; while(E[a]==0);
      int b = (r<0.55)? adj[a][xr()%n] : (int)(xr()%N);
      E[a]--; E[b]++; }
    int g=fails(E,N);
    if(g<=f || ur()<exp((f-g)/T)){ memcpy(D,E,sizeof D); f=g;
      if(f<best){best=f; memcpy(B,D,sizeof B);} }
  }
  printf("n=%d d=%d seed=%s best_fails=%d :",n,d,argv[4],best);
  for(int i=0;i<N;i++) printf(" %d",B[i]); printf("\n");
}
int main(){ n=6; N=64; deg=6;
  for(int v=0;v<N;v++) for(int k=0;k<n;k++) adj[v][k]=v^(1<<k);
  int pos=0, total=0;
  for(int type=0; type<2; type++) for(int extra=-1; extra<64; extra++){
    int D[64]={0};
    for(int v=0;v<64;v++){ int w=__builtin_popcount(v); if(type==0 && w==1) D[v]=5; if(type==1 && w==2) D[v]=2; }
    if(extra>=0) D[extra]++;
    total++; if(fails(D,64)==0) { pos++; printf("positive rank: type %d extra %d\n",type,extra); }
  }
  printf("checked %d rigid divisors (degree 30 and 31), positive rank: %d\n", total, pos);
}
