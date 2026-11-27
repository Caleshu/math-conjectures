// Brent-style: odd-recurrence state = last (E3/2) odd bits; hash states sampled at checkpoints to find a cycle.
// We store the bit sequence; a period P is confirmed if T[v]==T[v+P] for a stretch longer than the window.
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
int main(int argc,char**argv){ long n=atol(argv[1]), N0=atol(argv[2]); long MAXU=atol(argv[3]);
  unsigned char*T=calloc(MAXU+1,1); long*terms=malloc(8*(N0+2)); int nt=0; T[2]=1;T[n]=1;terms[nt++]=2;terms[nt++]=n;
  for(long u=n+1;u<=N0;u++){int c=0; for(int i=0;i<nt&&c<2;i++){long a=terms[i],b=u-a; if(b<a)continue; if(T[b])c++;} if(c==1){T[u]=1;terms[nt++]=u;}}
  long E3=2*n*n+2; for(long u=N0+1;u<=MAXU;u++){ if(u%2==0)continue; int c=T[u-2]+T[u-2*n]+T[u-E3]; T[u]=(c==1);}
  // rolling hash of window of W=E3 consecutive u values (odd ones matter) ending at u; record hash at u = end
  long W=E3+2; uint64_t B=1000003ULL, BW=1; for(long i=0;i<W;i++) BW*=B;
  // hash table of size 2^26 for states at all odd u in [N0+W, MAXU]; detect first repeat
  long HS=1L<<27; uint64_t*hk=calloc(HS,8); long*hv=calloc(HS,8);
  uint64_t h=0; for(long u=N0+1;u<=MAXU;u++){ h=h*B+T[u]+1; if(u-W>N0) h-=BW*(T[u-W]+1);
    if(u-N0>W && (u%2)){ uint64_t k=h|1; long idx=k&(HS-1); while(hk[idx] && hk[idx]!=k) idx=(idx+1)&(HS-1);
      if(hk[idx]==k){ long u1=hv[idx]; long P=u-u1; // verify
        int ok=1; for(long v=u1-W+1; v<=u1; v++) if(T[v]!=T[v+P]){ok=0;break;}
        if(ok){ printf("n=%ld: state repeat: period P=%ld, from u0<=%ld\n",n,P,u1-W+1); return 0; } }
      else { hk[idx]=k; hv[idx]=u; } } }
  printf("n=%ld: no repeat up to %ld\n",n,MAXU); return 0;}
