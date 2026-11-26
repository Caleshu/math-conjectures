#include "g6.h"
// is chi_pcf(G) <= K ?  proper colouring; every non-isolated vertex has a colour appearing exactly once in N(v)
static int K, col[MAXN], last[MAXN], order_ok;
static int vertex_ok(int v){ int cnt[8]={0}; for(int u=0;u<n;u++) if(adjm[v]>>u&1) cnt[col[u]]++;
  for(int c=0;c<K;c++) if(cnt[c]==1) return 1; return deg[v]==0; }
static int rec(int k){ if(k==n) return 1;
  int maxc = 0; for(int i=0;i<k;i++) if(col[i]+1>maxc) maxc=col[i]+1; // symmetry: colours introduced in order
  for(int c=0;c<K && c<=maxc;c++){ int ok=1; for(int u=0;u<k;u++) if((adjm[k]>>u&1) && col[u]==c){ok=0;break;}
    if(!ok) continue; col[k]=c;
    for(int v=0;v<n && ok;v++) if(last[v]==k && !vertex_ok(v)) ok=0;
    if(ok && rec(k+1)) return 1; }
  return 0; }
int main(int argc,char**argv){ K=atoi(argv[1]); long cnt=0,bad=0; while(readg6(stdin)){ cnt++;
  for(int v=0;v<n;v++){ last[v]=-1; for(int u=0;u<n;u++) if(adjm[v]>>u&1 && u>last[v]) last[v]=u; if(last[v]<v) last[v]=v; }
  if(!rec(0)){ bad++; if(bad<=5){ printf("NEEDS>%d: n=%d adj:",K,n); for(int i=0;i<n;i++)printf(" %x",adjm[i]); printf("\n");} } }
  printf("graphs=%ld needing>%d=%ld\n",cnt,K,bad); }
