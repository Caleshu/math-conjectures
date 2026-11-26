// Build ordering of Q_d (d>=4): Q4-direction edges first (by Q4 label, ties by copy), then directions 4..d-1 in blocks.
// Compute the longest increasing path exactly (DFS over increasing paths with distinct vertices).
#include <stdio.h>
#include <stdlib.h>
int d,N; long lab[1<<10][10]; int vis[1<<10];
int L4[16][16];
int best=0;
void dfs(int v,long last,int len){ if(len>best)best=len;
  for(int i=0;i<d;i++){int w=v^(1<<i); if(vis[w])continue; long l=lab[v][i]; if(l<=last)continue; vis[w]=1; dfs(w,l,len+1); vis[w]=0;} }
int main(int c,char**argv){ d=atoi(argv[1]); N=1<<d;
  int T[32][3]={{0,8,1},{4,6,2},{0,4,3},{9,11,4},{1,3,5},{2,10,6},{2,3,7},{0,2,8},{8,9,9},{12,14,10},{5,13,11},{12,13,12},{7,15,13},{6,7,14},{11,15,15},{10,14,16},{1,5,17},{5,7,18},{6,14,19},{2,6,20},{8,10,21},{1,9,22},{0,1,23},{3,11,24},{3,7,25},{4,12,26},{4,5,27},{8,12,28},{13,15,29},{9,13,30},{10,11,31},{14,15,32}};
  for(int k=0;k<32;k++){L4[T[k][0]][T[k][1]]=L4[T[k][1]][T[k][0]]=T[k][2];}
  for(int v=0;v<N;v++)for(int i=0;i<d;i++){int w=v^(1<<i); int lo=v<w?v:w;
    if(i<4) lab[v][i]=(long)L4[v&15][w&15]*N + (lo>>4);
    else lab[v][i]=(long)33*N + (long)(i-4)*N + lo; }
  for(int v=0;v<N;v++){vis[v]=1; dfs(v,-1,0); vis[v]=0;}
  printf("Q_%d: longest increasing path under product ordering = %d edges (d-1 = %d)\n",d,best,d-1); }
