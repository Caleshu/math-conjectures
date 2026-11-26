#include <stdio.h>
#include <stdlib.h>
int n,N; int path[64]; char vis[64]; char used[64][8]; // used[min endpoint][dir]
long found=0, cnt=0;
int bad(int u,int d){ // adding edge u--u^(1<<d) creates inscribed square?
  int a=u&~(1<<d);
  for(int j=0;j<n;j++) if(j!=d && used[a^(1<<j)][d]) return 1;
  return 0;
}
void rec(int k){
  int u=path[k-1];
  if(k==N){ int d=__builtin_ctz(u^path[0]); if(__builtin_popcount(u^path[0])==1 && !bad(u,d)){found++; if(found<=3){for(int i=0;i<N;i++)printf("%d ",path[i]);printf("\n");}} return;}
  for(int d=0;d<n;d++){int v=u^(1<<d); if(vis[v])continue; if(bad(u,d))continue;
    int a=u&~(1<<d); used[a][d]=1; vis[v]=1; path[k]=v; rec(k+1); vis[v]=0; used[a][d]=0;}
}
int main(int c,char**v){n=atoi(v[1]);N=1<<n;path[0]=0;vis[0]=1;rec(1);printf("n=%d square-free ham cycles (directed, from 0): %ld\n",n,found);}
