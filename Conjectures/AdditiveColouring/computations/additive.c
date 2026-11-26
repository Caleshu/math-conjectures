#include "g6.h"
// eta(G) <= 2 ?  labels in {0,1} (meaning 1,2); S(v)=deg+#nbrs with label 1
static int lab[MAXN], last[MAXN];
static int ok_upto(int k){ // all vertices v with last[v]==k now have S determined; check edges among determined
  for(int v=0;v<n;v++) if(last[v]==k){ int sv=0; for(int u=0;u<n;u++) if(adjm[v]>>u&1) sv+=lab[u];
      for(int u=0;u<n;u++) if((adjm[v]>>u&1) && last[u]<=k){ int su=0; for(int w=0;w<n;w++) if(adjm[u]>>w&1) su+=lab[w]; if(su+deg[u]==sv+deg[v]) return 0;}}
  return 1;}
static int rec(int k){ if(k==n) return 1; for(int l=0;l<2;l++){lab[k]=l; if(ok_upto(k)&&rec(k+1)) return 1;} return 0;}
int main(){ long cnt=0,bad=0; while(readg6(stdin)){ cnt++;
  for(int v=0;v<n;v++){ last[v]=0; for(int u=0;u<n;u++) if(adjm[v]>>u&1 && u>last[v]) last[v]=u; }
  if(!rec(0)){ bad++; if(bad<=5){ printf("ETA>2: n=%d adj:",n); for(int i=0;i<n;i++)printf(" %x",adjm[i]); printf("\n");} } }
  printf("graphs=%ld eta>2=%ld\n",cnt,bad); }
