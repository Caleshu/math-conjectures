// Gregor–Škrekovski: F balanced; mode 0: all pairs dist>=3; mode 1: same-parity pairs dist>=4 (opposite parity unrestricted).
// Check Q_n - F Hamiltonian for all such F containing vertex 0 (WLOG by vertex-transitivity), |F|>=2.
#include <stdio.h>
#include <stdlib.h>
int n,N,mode; int inF[256]; int F[64],fs; long sets=0,tested=0,fails=0;
int par(int x){return __builtin_popcount(x)&1;}
int dist(int a,int b){return __builtin_popcount(a^b);}
int okadd(int x){ for(int i=0;i<fs;i++){int dd=dist(x,F[i]); if(mode==0){ if(dd<3) return 0;} else { if(par(x)==par(F[i]) && dd<4) return 0; if(dd==0) return 0;} } return 1;}
// Hamiltonian cycle search
int vis[256], path[256], M; long hnodes;
int deg_un(int v){int c=0; for(int i=0;i<n;i++){int w=v^(1<<i); if(!inF[w]&&!vis[w])c++;} return c;}
int start;
unsigned long long rs=88172645463325252ULL; unsigned long long xr(){rs^=rs<<13;rs^=rs>>7;rs^=rs<<17;return rs;}
long LIMIT=200000;
int ham(int k,int v){ hnodes++; if(hnodes>LIMIT) return -1;
  if(k==M){ return __builtin_popcount(v^start)==1; }
  // pruning: every unvisited vertex needs >=2 available (unvisited or endpoint/start) neighbours
  for(int i=0;i<n;i++){int w=v^(1<<i); if(inF[w]||vis[w])continue;}
  int cand[16],cc=0, forced=-1;
  for(int i=0;i<n;i++){int w=v^(1<<i); if(inF[w]||vis[w])continue; cand[cc++]=w;}
  // degree check on neighbours of v: a neighbour w of v with only 1 other free option must be next (forced) unless...
  if(k>1) for(int j=0;j<cc;j++){ int w=cand[j]; int c=deg_un(w) + (__builtin_popcount(w^start)==1); if(c<1 && k+1<M) return 0; if(c==1 && k+1<M){ if(forced>=0 && forced!=w) return 0; forced=w; } }
  int key[16]; for(int j=0;j<cc;j++) key[j]=deg_un(cand[j])*1000+(int)(xr()%1000);
  for(int a=0;a<cc;a++)for(int b=a+1;b<cc;b++) if(key[b]<key[a]){int t=key[a];key[a]=key[b];key[b]=t;t=cand[a];cand[a]=cand[b];cand[b]=t;}
  for(int j=0;j<cc;j++){ int w=cand[j]; if(forced>=0&&w!=forced)continue; vis[w]=1; int r=ham(k+1,w); vis[w]=0; if(r) return r; }
  return 0; }
int is_ham(){ M=N-fs; start=-1; for(int v=0;v<N;v++){vis[v]=0; if(!inF[v]&&start<0)start=v;}
  // min-degree check
  for(int v=0;v<N;v++) if(!inF[v]){int c=0; for(int i=0;i<n;i++) if(!inF[v^(1<<i)])c++; if(c<2) return 0;}
  int r=-1; for(int t=0;t<300 && r<0;t++){ for(int v=0;v<N;v++)vis[v]=0; vis[start]=1; hnodes=0; r=ham(1,start); }
  if(r<0){ LIMIT=200000000; for(int v=0;v<N;v++)vis[v]=0; vis[start]=1; hnodes=0; r=ham(1,start); LIMIT=200000; }
  return r; }
void rec(int from){ int ev=0,od=0; for(int i=0;i<fs;i++) { if(par(F[i])) od++; else ev++; }
  if(fs>=2 && ev==od){ sets++; int r=is_ham(); tested++; if(r!=1){ fails++; if(fails<=10){ printf("%s: n=%d F=",r<0?"TIMEOUT":"NOT HAMILTONIAN",n); for(int i=0;i<fs;i++)printf("%d ",F[i]); printf("\n"); fflush(stdout);} } }
  for(int x=from;x<N;x++) if(okadd(x)){ F[fs++]=x; inF[x]=1; rec(x+1); inF[x]=0; fs--; } }
int main(int c,char**v){ n=atoi(v[1]); mode=atoi(v[2]); N=1<<n; F[0]=0; fs=1; inF[0]=1; rec(1);
  printf("n=%d mode=%d balanced sets containing 0: %ld, failures: %ld\n",n,mode,sets,fails); }
