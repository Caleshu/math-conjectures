// Exact check of Basdevant-Henard-Maurel-Segala-Singh Conjecture 2 (Litt's game).
// For words A,B in {0,1}^L with [A|A] > [B|B], check for every n in [0,NMAX]:
//   (i)  n >= n0  =>  P(Alice wins) < P(Bob wins)   (and equality for n < n0, reported)
//   (ii) P(Bob wins) < 1/2   (equivalently 1/2 < P(Alice)+P(Tie))
// Counts are exact integers (__int128), probabilities = count / 2^n.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef __int128 I;
static int L, NMAX;
static int bit(int w,int i){return (w>>(L-1-i))&1;} // i-th letter, i=0..L-1
static int corr(int a,int b){ // [A|B] = sum_{k in Cor(A,B)} 2^k, k=1..L-1, suffix_k(A)=prefix_k(B)
  int s=0; for(int k=1;k<L;k++){int ok=1; for(int t=0;t<k;t++) if(bit(a,L-k+t)!=bit(b,t)){ok=0;break;} if(ok) s+=1<<k;} return s;}
static int corrset(int a,int b){int s=0; for(int k=1;k<L;k++){int ok=1; for(int t=0;t<k;t++) if(bit(a,L-k+t)!=bit(b,t)){ok=0;break;} if(ok) s|=1<<k;} return s;}
// KMP automaton for a word: next state after reading c from state q (q = matched prefix length, 0..L-1; reaching L counts an occurrence and falls back)
static int kmp_next(int w,int q,int c,int *hit){
  // brute force: string = prefix_q(w)+c, find longest suffix that's a prefix of w
  int buf[64]; for(int i=0;i<q;i++) buf[i]=bit(w,i); buf[q]=c; int len=q+1;
  *hit=0; if(len==L){int ok=1; for(int i=0;i<L;i++) if(buf[i]!=bit(w,i)){ok=0;break;} if(ok)*hit=1;}
  for(int k=(len<L?len:L-1);k>=0;k--){int ok=1; for(int t=0;t<k;t++) if(buf[len-k+t]!=bit(w,t)){ok=0;break;} if(ok) return k;}
  return 0;}
int main(int argc,char**argv){
  L=atoi(argv[1]); NMAX=atoi(argv[2]);
  int W=1<<L; int Q=L; // states 0..L-1
  static int nx[2][64][2], hx[2][64][2];
  long pairs=0, viol=0, eqviol=0; int D=NMAX; // diff offset
  I *cur=malloc(sizeof(I)*64*64*(2*D+1)), *nxt=malloc(sizeof(I)*64*64*(2*D+1));
  double worst_ratio=1e9; int wa=-1,wb=-1,wn=-1;
  for(int a=0;a<W;a++) for(int b=0;b<W;b++){ if(a==b) continue;
    int caa=corr(a,a), cbb=corr(b,b); if(!(caa>cbb)) continue;
    pairs++;
    int sym=corrset(a,a)^corrset(b,b); int mx=0; for(int k=1;k<L;k++) if(sym>>k&1) mx=k;
    int n0=2*L-mx;
    for(int q=0;q<Q;q++) for(int c=0;c<2;c++){ nx[0][q][c]=kmp_next(a,q,c,&hx[0][q][c]); nx[1][q][c]=kmp_next(b,q,c,&hx[1][q][c]); }
    size_t S=(size_t)Q*Q*(2*D+1); memset(cur,0,sizeof(I)*S);
    #define IDX(p,q,d) (((size_t)(p)*Q+(q))*(2*D+1)+(d)+D)
    cur[IDX(0,0,0)]=1;
    for(int n=0;n<=NMAX;n++){
      // evaluate at length n: diff = N_A - N_B
      I aw=0,bw=0,tie=0;
      for(int p=0;p<Q;p++) for(int q=0;q<Q;q++) for(int d=-n;d<=n;d++){ I v=cur[IDX(p,q,d)]; if(!v) continue; if(d>0) aw+=v; else if(d<0) bw+=v; else tie+=v; }
      I tot=(I)1<<n;
      if(argc>4 && a==atoi(argv[3]) && b==atoi(argv[4])) printf("dbg n=%d aw=%lld bw=%lld tie=%lld\n",n,(long long)aw,(long long)bw,(long long)tie);
      // (ii): 2*bw < tot
      if(!(2*bw<tot)){ viol++; if(viol<20) printf("VIOL(ii) L=%d a=%d b=%d n=%d\n",L,a,b,n); }
      if(n>=n0){ if(!(aw<bw)){ viol++; if(viol<20) printf("VIOL(i) L=%d a=%d b=%d n=%d n0=%d\n",L,a,b,n,n0);} }
      else { if(aw!=bw){ eqviol++; if(eqviol<20) printf("NOTE n<n0 but unequal: L=%d a=%d b=%d n=%d n0=%d\n",L,a,b,n,n0);} }
      if(n==NMAX) break;
      memset(nxt,0,sizeof(I)*S);
      for(int p=0;p<Q;p++) for(int q=0;q<Q;q++) for(int d=-n;d<=n;d++){ I v=cur[IDX(p,q,d)]; if(!v) continue;
        for(int c=0;c<2;c++){ int p2=nx[0][p][c], q2=nx[1][q][c]; int dd=d+hx[0][p][c]-hx[1][q][c]; nxt[IDX(p2,q2,dd)]+=v; } }
      I*t=cur;cur=nxt;nxt=t;
    }
  }
  printf("L=%d NMAX=%d pairs=%ld violations=%ld n<n0-inequalities=%ld\n",L,NMAX,pairs,viol,eqviol);
  return 0;}
