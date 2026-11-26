// simulated annealing: edge-ordering of Q_d minimizing # increasing paths with K edges (K=L+1)
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
int d,N,M,K; int eu[2000],ev[2000]; int eid[1024][16]; int lab[2000];
int vis[1024];
long cntfrom(int x,int lastlab,int need){ if(need==0) return 1; long s=0;
  for(int i=0;i<d;i++){int y=x^(1<<i); if(vis[y])continue; int l=lab[eid[x][i]]; if(l<=lastlab)continue; vis[y]=1; s+=cntfrom(y,l,need-1); vis[y]=0;} return s;}
long cost(){ long s=0; for(int v=0;v<N;v++){vis[v]=1; s+=cntfrom(v,-1,K); vis[v]=0;} return s;}
// paths through edge e only (for delta): count increasing K-paths containing e -- simpler: full recompute
unsigned long long rs=88172645463325252ULL; unsigned long long xr(){rs^=rs<<13;rs^=rs>>7;rs^=rs<<17;return rs;}
int main(int c,char**v){ d=atoi(v[1]); K=atoi(v[2])+1; long iters=atol(v[3]); rs+=atoi(v[4]); N=1<<d; M=0;
  for(int a=0;a<N;a++)for(int i=0;i<d;i++){int b=a^(1<<i); if(a<b){eu[M]=a;ev[M]=b;eid[a][i]=eid[b][i]=M;M++;}}
  // start: blocks by direction
  for(int e=0;e<M;e++){int i=__builtin_ctz(eu[e]^ev[e]); lab[e]=i*M+ (int)(xr()%M);}
  // normalize to permutation
  int idx[2000]; for(int e=0;e<M;e++)idx[e]=e;
  for(int a=0;a<M;a++)for(int b=a+1;b<M;b++) if(lab[idx[b]]<lab[idx[a]]){int t=idx[a];idx[a]=idx[b];idx[b]=t;}
  for(int r=0;r<M;r++)lab[idx[r]]=r;
  long cur=cost(), best=cur; double T=2.0;
  for(long it=0;it<iters && cur>0;it++){ int a=xr()%M,b=xr()%M; if(a==b)continue; int t=lab[a];lab[a]=lab[b];lab[b]=t;
    long nc=cost(); if(nc<=cur || exp((cur-nc)/T) > (xr()%1000000)/1e6){cur=nc; if(cur<best){best=cur;}} else {t=lab[a];lab[a]=lab[b];lab[b]=t;}
    T*=0.99995; if(T<0.05)T=0.05;
    if(it%200000==0){fprintf(stderr,"it %ld cur %ld best %ld T %.3f\n",it,cur,best,T);} }
  printf("Q_%d K=%d final cost %ld\n",d,K,cur);
  if(cur==0){ for(int e=0;e<M;e++)printf("%d %d %d\n",eu[e],ev[e],lab[e]+1); }
}
