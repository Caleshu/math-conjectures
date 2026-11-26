#include "g6.h"
// lir(G) <= K ? edge colouring where each colour class is locally irregular (adjacent vertices in the class have different class-degrees)
static int m, eu[64], ev[64], ec[64], K; static int lastE[MAXN]; // index of last edge incident to v
static int cdeg[MAXN][8];
static int check_vertex(int v){ // all edges at v coloured: for each edge vw of colour c with w complete, cdeg differ
  for(int e=0;e<m;e++){ if(ec[e]<0) continue; int a=eu[e],b=ev[e]; if(a!=v&&b!=v) continue; int w=a==v?b:a;
    if(lastE[w] <= lastE[v] || 1){ if(lastE[w]<=lastE[v]) { if(cdeg[v][ec[e]]==cdeg[w][ec[e]]) return 0; } } }
  return 1; }
static int rec(int k){ if(k==m) return 1;
  int maxc=0; for(int i=0;i<k;i++) if(ec[i]+1>maxc) maxc=ec[i]+1;
  for(int c=0;c<K && c<=maxc;c++){ ec[k]=c; cdeg[eu[k]][c]++; cdeg[ev[k]][c]++; int ok=1;
    // vertices that become complete at edge k
    if(lastE[eu[k]]==k && !check_vertex(eu[k])) ok=0;
    if(ok && lastE[ev[k]]==k && !check_vertex(ev[k])) ok=0;
    if(ok && rec(k+1)) return 1;
    cdeg[eu[k]][c]--; cdeg[ev[k]][c]--; ec[k]=-1; }
  return 0; }
static int lir_le(int k){ K=k; for(int e=0;e<m;e++)ec[e]=-1; memset(cdeg,0,sizeof cdeg); return rec(0); }
int main(){ long cnt=0; long hist[10]={0}; while(readg6(stdin)){ cnt++; m=0;
  for(int j=0;j<n;j++)for(int i=0;i<j;i++) if(adjm[i]>>j&1){eu[m]=i;ev[m]=j;m++;}
  for(int v=0;v<n;v++){lastE[v]=-1;} for(int e=0;e<m;e++){lastE[eu[e]]=e;lastE[ev[e]]=e;}
  int k; for(k=1;k<=6;k++) if(lir_le(k)) break;
  hist[k]++;
  if(k>=4 && k<=6){ printf("LIR=%d n=%d m=%d adj:",k,n,m); for(int i=0;i<n;i++)printf(" %x",adjm[i]); printf("\n"); } }
  printf("graphs=%ld  lir=1:%ld 2:%ld 3:%ld 4:%ld 5:%ld 6:%ld  >6(not decomposable?):%ld\n",cnt,hist[1],hist[2],hist[3],hist[4],hist[5],hist[6],hist[7]); }
