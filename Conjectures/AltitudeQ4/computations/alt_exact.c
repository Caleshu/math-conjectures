// exact: does Q_d have an edge-ordering with no increasing path of L+1 edges? (backtracking)
#include <stdio.h>
#include <stdlib.h>
int d,N,M,L; int eu[200],ev[200]; int lab[64][64]; int used[200]; long nodes=0;
int vis[64];
// is there an increasing path with L+1 edges whose LAST edge is (a->b) with label t (all labels assigned so far < t)?
// search backwards from a: path ... -> x -> a with labels decreasing going back
int back(int x,int lastlab,int need){ if(need==0) return 1;
  for(int i=0;i<d;i++){int y=x^(1<<i); if(vis[y])continue; int l=lab[x][y]; if(l<0||l>=lastlab)continue;
    vis[y]=1; int r=back(y,l,need-1); vis[y]=0; if(r) return 1;} return 0;}
int creates(int e,int t){ for(int s=0;s<2;s++){int a=s?ev[e]:eu[e],b=s?eu[e]:ev[e]; vis[a]=vis[b]=1; int r=back(a,t,L); vis[a]=vis[b]=0; if(r) return 1;} return 0;}
// also forward? Since labels assigned in increasing order, new edge always largest: only paths ending at it matter.
int rec(int t){ nodes++; if(t==M) return 1;
  for(int e=0;e<M;e++) if(!used[e]){ if(creates(e,t)) continue; used[e]=1; lab[eu[e]][ev[e]]=lab[ev[e]][eu[e]]=t;
     if(rec(t+1)) return 1; used[e]=0; lab[eu[e]][ev[e]]=lab[ev[e]][eu[e]]=-1; if(t==0) return 0; /* edge-transitive: first edge WLOG */ }
  return 0;}
int main(int c,char**v){ d=atoi(v[1]); L=atoi(v[2]); N=1<<d; M=0;
  for(int a=0;a<N;a++)for(int i=0;i<d;i++){int b=a^(1<<i); if(a<b){eu[M]=a;ev[M]=b;M++;}}
  for(int a=0;a<N;a++)for(int b=0;b<N;b++)lab[a][b]=-1;
  int r=rec(0); printf("Q_%d: ordering with longest increasing path <= %d edges: %s (nodes %ld)\n",d,L,r?"EXISTS":"NONE",nodes);
  if(r){for(int e=0;e<M;e++)printf("%d-%d:%d ",eu[e],ev[e],lab[eu[e]][ev[e]]+1);printf("\n");} }
