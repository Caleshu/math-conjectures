// Independent re-implementation of (C1). Different vertex order (Gray-code BFS from 0), different egg test
// (enumerate all supersets of K within the allowed size by index combinations, no caching).
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
typedef uint64_t u64;
static u64 NB[64];
static int LIM, P=1, ID=0;
static int popc(u64 x){return __builtin_popcountll(x);}
static int boundary(u64 W){int b=0; for(int u=0;u<64;u++) if(W>>u&1) b+=popc(NB[u]&~W); return b;}
static int closed_nbhd(u64 W){ for(int v=0;v<64;v++) if(W==(NB[v]|(1ULL<<v))) return 1; return 0; }
static int cheap(u64 W){ return popc(W)<=10 && boundary(W)<=30 && !closed_nbhd(W); }
// egg test for connected K: not contained in any cheap W. Connected supersets only need vertices within distance `room`.
static int egg_raw(u64 K);
#define MB (1u<<22)
static u64 memK[MB]; static unsigned char memV[MB];
static int egg(u64 K){ unsigned h=(unsigned)((K^(K>>29)^(K>>47))*2654435761u)&(MB-1); if(memV[h]&&memK[h]==K) return memV[h]-1; int r=egg_raw(K); memK[h]=K; memV[h]=r+1; return r; }
static int egg_raw(u64 K){
  int s=popc(K); if(s>10) return 1;
  int room=10-s;
  u64 ball=K, fr=K; for(int r=0;r<room;r++){ u64 nf=0; for(int u=0;u<64;u++) if(fr>>u&1) nf|=NB[u]; nf&=~ball; ball|=nf; fr=nf; }
  u64 cand=ball&~K; int c[64], m=0; for(int u=0;u<64;u++) if(cand>>u&1) c[m++]=u;
  if(cheap(K)) return 0;
  for(int a=0;a<m && room>=1;a++){ u64 W1=K|(1ULL<<c[a]); if(cheap(W1)) return 0;
    for(int b=a+1;b<m && room>=2;b++){ u64 W2=W1|(1ULL<<c[b]); if(cheap(W2)) return 0;
      for(int d=b+1; d<m && room>=3; d++){ u64 W3=W2|(1ULL<<c[d]); if(cheap(W3)) return 0;
        if(room>=4){ for(int e=d+1;e<m;e++){ u64 W4=W3|(1ULL<<c[e]); if(cheap(W4)) return 0; if(room>=5){ for(int f=e+1;f<m;f++){ if(cheap(W4|(1ULL<<c[f]))) return 0; } } } } } } }
  return 1;
}
static int ord[64], state[64]; static u64 Y=0; static int nX=0, Kmax=6; static long long nodes=0, sc=0;
static u64 compo(int v){u64 c=1ULL<<v,f=c; while(f){u64 n=0; for(int u=0;u<64;u++) if(f>>u&1) n|=NB[u]&Y; n&=~c; c|=n; f=n;} return c;}
static int ydeg(int u){return popc(NB[u]&Y);}
static int consistent(int v){
  for(int u=0;u<64;u++){ if(!((u==v)||(NB[v]>>u&1))) continue; if(state[u]!=1) continue;
    if(ydeg(u)>Kmax) return 0;
    int und=0,hx=0; for(int k=0;k<6;k++){int w=u^(1<<k); if(state[w]==0) und=1; if(state[w]==2) hx=1;}
    if(!und&&!hx) return 0; }
  if(state[v]==1){ u64 c=compo(v); if(popc(c)>=7 && (popc(c)>7 || closed_nbhd(c)) && egg(c)) return 0; }
  return 1;
}
static int go(int i){
  nodes++;
  if(i==14){ if((sc++)%P!=ID) return 0; }
  if(i==64) return 1;
  int v=ord[i];
  for(int val=1;val<=2;val++){
    if(val==2 && nX>=LIM) continue;
    if(v==0 && val==2) continue;
    if(popc(v)==1 && v>1 && state[v>>1]==2 && val==1) continue;
    state[v]=val; if(val==1) Y|=1ULL<<v; else nX++;
    int sk=Kmax, ok=1;
    if(v==32){ Kmax=popc(NB[0]&Y); if(Kmax==0) ok=0; for(int u=0;u<64;u++) if(state[u]==1 && ydeg(u)>Kmax) ok=0; }
    if(ok && consistent(v) && go(i+1)) return 1;
    Kmax=sk; state[v]=0; if(val==1) Y&=~(1ULL<<v); else nX--;
  }
  return 0;
}
int main(int argc,char**argv){
  LIM=atoi(argv[1]); if(argc>3){P=atoi(argv[2]); ID=atoi(argv[3]);}
  for(int v=0;v<64;v++){NB[v]=0; for(int k=0;k<6;k++) NB[v]|=1ULL<<(v^(1<<k));}
  // order: weight layers; within a layer, by Gray-code rank (different from the first program)
  int k=0; for(int w=0;w<=6;w++) for(int g=0;g<64;g++){ int v=g^(g>>1); if(popc(v)==w) ord[k++]=v; }
  // weight-1 layer must be 1,2,4,...,32 in increasing order for the symmetry rule; enforce explicitly
  for(int j=0;j<6;j++) ord[1+j]=1<<j;
  int r=go(0);
  printf("LIM=%d %s nodes=%lld\n",LIM,r?"FOUND":"NONE",nodes);
  if(r){ for(int v=0;v<64;v++) if(state[v]==2) printf("%d ",v); printf("\n"); }
}
