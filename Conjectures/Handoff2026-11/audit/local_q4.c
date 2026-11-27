/* Enumerate all square-free subgraphs of Q_4 with max degree <= 2 (each counted once),
 * record the achievable (n1, n2) = (#vertices of degree 1, #vertices of degree 2). */
#include <stdio.h>
int ea[32], eb[32], NE = 0; int sq[48][2]; int NS = 0;  /* 24 squares x 2 opposite pairs */
int deg[16]; int on[32]; long long cnt = 0; int seen[17][17];
int eidx(int a,int b){ for(int k=0;k<NE;k++) if((ea[k]==a&&eb[k]==b)||(ea[k]==b&&eb[k]==a)) return k; return -1; }
int bad(int k){ /* adding edge k creates an opposite pair with an existing edge? */
  for(int s=0;s<NS;s++){ if(sq[s][0]==k && on[sq[s][1]]) return 1; if(sq[s][1]==k && on[sq[s][0]]) return 1; }
  return 0; }
void rec(int k){
  if(k==NE){ int n1=0,n2=0; for(int v=0;v<16;v++){ if(deg[v]==1)n1++; if(deg[v]==2)n2++; } seen[n1][n2]=1; cnt++; return; }
  rec(k+1);
  int a=ea[k], b=eb[k];
  if(deg[a]<2 && deg[b]<2 && !bad(k)){ on[k]=1; deg[a]++; deg[b]++; rec(k+1); on[k]=0; deg[a]--; deg[b]--; }
}
int main(){
  for(int v=0;v<16;v++) for(int i=0;i<4;i++){ int u=v^(1<<i); if(u>v){ ea[NE]=v; eb[NE]=u; NE++; } }
  for(int v=0;v<16;v++) for(int i=0;i<4;i++) for(int j=i+1;j<4;j++){
    if((v>>i&1)||(v>>j&1)) continue;
    int a=v,b=v^(1<<i),c=v^(1<<i)^(1<<j),d=v^(1<<j);
    sq[NS][0]=eidx(a,b); sq[NS][1]=eidx(d,c); NS++;
    sq[NS][0]=eidx(a,d); sq[NS][1]=eidx(b,c); NS++; }
  rec(0);
  printf("configurations: %lld\nachievable (n1,n2):", cnt);
  for(int x=0;x<=16;x++) for(int y=0;y<=16;y++) if(seen[x][y]) printf(" (%d,%d)",x,y);
  printf("\n"); return 0; }
