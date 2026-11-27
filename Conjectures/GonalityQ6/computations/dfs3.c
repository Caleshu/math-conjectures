// Exhaustive search: is there X subset of V(Q6), |X| <= LIMIT, such that
//  (a) every y not in X has a neighbor in X   (X meets every closed neighborhood), and
//  (b) no connected subset of Y = V\X is an "egg" (connected, not inside any W with |W|<=10, bd(W)<=30, W != N[v]).
// Egg property is upward closed, so we prune as soon as a (partial) Y-component is an egg.
// WLOG: vertex 0 in Y; neighbors of 0 sorted so X-neighbors come last (coordinate permutations).
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
typedef uint64_t u64;
int N=64, LIMIT; u64 nb[64]; u64 closedN[64];
static inline int pc(u64 x){return __builtin_popcountll(x);}
int bd(u64 W){int s=0; u64 t=W; while(t){int u=__builtin_ctzll(t); t&=t-1; s+=pc(nb[u]&~W);} return s;}
int is_closed(u64 W){ if(pc(W)!=7) return 0; for(int v=0;v<64;v++) if(closedN[v]==W) return 1; return 0;}
// hash cache for in_bad
#define HS (1<<24)
u64 hk[HS]; signed char hv[HS];
int in_bad_rec(u64 W, u64 *seen, int *ns){
  if(bd(W)<=30 && !is_closed(W)) return 1;
  if(pc(W)>=10) return 0;
  u64 fr=0, t=W; while(t){int u=__builtin_ctzll(t); t&=t-1; fr|=nb[u];} fr&=~W;
  while(fr){int w=__builtin_ctzll(fr); fr&=fr-1; u64 W2=W|(1ULL<<w);
    int dup=0; for(int i=0;i<*ns;i++) if(seen[i]==W2){dup=1;break;}
    if(dup) continue; if(*ns<4096) seen[(*ns)++]=W2;
    if(in_bad_rec(W2,seen,ns)) return 1; }
  return 0;
}
int is_egg(u64 K){ // K connected
  int s=pc(K); if(s>10) return 1; if(s<=6) return 0; if(s==7) return is_closed(K);
  u64 h=(K*0x9E3779B97F4A7C15ULL)>>40;          // direct-mapped cache, overwrite on collision
  if(hv[h] && hk[h]==K) return hv[h]==2;
  static u64 seen[4096]; int ns=0;
  int bad=in_bad_rec(K,seen,&ns);
  hk[h]=K; hv[h]= bad?1:2; return !bad;
}
int order[64], pos[64];
int st[64]; // 0 undecided, 1 Y, 2 X
long long nodes=0; int best_found=0;
u64 Ymask=0;
u64 comp_of(int v){ u64 c=1ULL<<v, fr=c; while(fr){ u64 nf=0, t=fr; while(t){int u=__builtin_ctzll(t); t&=t-1; nf|=nb[u]&Ymask;} nf&=~c; c|=nf; fr=nf;} return c;}
int ok_after(int v){ // check constraints touched by deciding v
  // domination: v and its neighbors that are Y with all neighbors decided must have an X neighbor
  u64 chk=(1ULL<<v)|nb[v];
  while(chk){int u=__builtin_ctzll(chk); chk&=chk-1; if(st[u]!=1) continue;
    int und=0, hasX=0; for(int k=0;k<6;k++){int w=u^(1<<k); if(st[w]==0) und=1; if(st[w]==2) hasX=1;}
    if(!und && !hasX) return 0; }
  if(st[v]==1){ u64 c=comp_of(v); if(is_egg(c)) return 0; }
  return 1;
}
int nx=0; int ydeg[64]; int K0=6;
long long splitcnt=0; int P=1, ID=0, SPLITD=14;
int dfs(int i){
  nodes++;
  if(i==SPLITD){ if((splitcnt++)%P!=ID) return 0; }
  if((nodes&((1LL<<24)-1))==0){ fprintf(stderr,"nodes=%lld depth=%d nx=%d\n",nodes,i,nx); }
  if(i==64) return 1;
  int v=order[i];
  // symmetry: neighbors of 0 = 1,2,4,..,32 ; enforce x_1<=x_2<=...  (st: Y=1 < X=2)
  for(int val=1; val<=2; val++){
    if(val==2 && nx>=LIMIT) continue;
    if(v==0 && val==2) continue;
    if(v>=1 && (v&(v-1))==0 && v>1){ int prev=v>>1; if(st[prev]==2 && val==1) continue; }
    st[v]=val; if(val==1) Ymask|=1ULL<<v; else nx++;
    int okd=1;
    if(val==1){ int c=0; for(int k=0;k<6;k++){int w=v^(1<<k); if(st[w]==1){ydeg[w]++; c++;}} ydeg[v]=c; }
    int savedK0=K0;
    if(v==32){ K0=pc(Ymask&nb[0]); }          // all neighbors of 0 decided: fix max degree
    if(val==1){ if(ydeg[v]>K0) okd=0; for(int k=0;k<6;k++){int w=v^(1<<k); if(st[w]==1 && ydeg[w]>K0) okd=0;} }
    if(v==32){ for(int u=0;u<64;u++) if(st[u]==1 && ydeg[u]>K0) okd=0; }
    if(K0==0 && v==32) okd=0;                  // Y independent => |Y|<=32 (independence number of Q6)
    if(okd && ok_after(v) && dfs(i+1)) return 1;
    K0=savedK0;
    if(val==1){ for(int k=0;k<6;k++){int w=v^(1<<k); if(st[w]==1) ydeg[w]--;} }
    st[v]=0; if(val==1) Ymask&=~(1ULL<<v); else nx--;
  }
  return 0;
}
int main(int argc,char**argv){
  LIMIT=atoi(argv[1]); if(argc>3){P=atoi(argv[2]); ID=atoi(argv[3]);}
  for(int v=0;v<64;v++){nb[v]=0; for(int k=0;k<6;k++) nb[v]|=1ULL<<(v^(1<<k)); closedN[v]=nb[v]|(1ULL<<v);}
  // order: by weight (BFS from 0), ties by value
  int k=0; for(int w=0;w<=6;w++) for(int v=0;v<64;v++) if(pc(v)==w) order[k++]=v;
  int r=dfs(0);
  printf("LIMIT=%d result=%s nodes=%lld\n",LIMIT, r?"FOUND":"NONE", nodes);
  if(r){ printf("X:"); for(int v=0;v<64;v++) if(st[v]==2) printf(" %d",v); printf("\n"); }
}
