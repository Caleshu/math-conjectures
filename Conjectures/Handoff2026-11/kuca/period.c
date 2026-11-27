// V(2,n): exact simulation to N0, then (assuming evens = E found so far) odd terms follow
// O(u) = [ #{e in E : O(u-e)} == 1 ] for odd u. Find preperiod u0 and period P of O (on odd u).
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
int main(int argc,char**argv){ long n=atol(argv[1]); long N0=atol(argv[2]); long MAXU=atol(argv[3]);
  unsigned char *T=calloc(MAXU+1,1); // term indicator
  // exact simulation up to N0 (brute force representation counts)
  long *terms=malloc(sizeof(long)*(N0+2)); int nt=0; T[2]=1;T[n]=1; terms[nt++]=2; terms[nt++]=n;
  for(long u=n+1;u<=N0;u++){ int c=0; for(int i=0;i<nt && c<2;i++){ long a=terms[i]; long b=u-a; if(b<a) continue; if(b<=MAXU && T[b]) c++; } if(c==1){T[u]=1;terms[nt++]=u;} }
  long E[64]; int ne=0; for(int i=0;i<nt;i++) if(terms[i]%2==0) E[ne++]=terms[i];
  printf("n=%ld evens up to N0=%ld:",n,N0); for(int i=0;i<ne;i++) printf(" %ld",E[i]); printf("\n");
  long W=E[ne-1]; // window
  // continue odd recurrence beyond N0
  for(long u=N0+1;u<=MAXU;u++){ if(u%2==0) continue; int c=0; for(int i=0;i<ne;i++){ long b=u-E[i]; if(b>0&&T[b]) c++; } T[u]=(c==1); }
  // period detection on odd positions: find smallest P (even, step in u) and u0 such that T[u]=T[u+P] for all odd u in [u0, MAXU-P]
  // use rolling: test candidate P by checking a long tail.
  for(long P=2;P<=MAXU/4;P+=2){ long u=MAXU-P; int ok=1; long last_bad=-1;
    for(long v=MAXU-P; v>N0; v--){ if(v%2==0) continue; if(T[v]!=T[v+P]){ last_bad=v; break;} }
    // need tail long enough: [last_bad+2, MAXU-P] length >= W (window) to guarantee by determinism
    long start=last_bad<0?N0+1:last_bad+2;
    if(MAXU-P-start > W+10){ printf("period P=%ld (in u), periodic from u0=%ld (checked to %ld)\n",P,start,MAXU); 
      long cnt=0; for(long v=start; v<start+P; v++) if(v%2 && T[v]) cnt++; printf("odd terms per period: %ld (density %.4f per odd)\n",cnt,(double)cnt/(P/2));
      FILE*f=fopen(argv[4],"wb"); fwrite(&n,8,1,f); fwrite(&P,8,1,f); fwrite(&start,8,1,f); fwrite(&MAXU,8,1,f); fwrite(T,1,MAXU+1,f); fclose(f); return 0; }
  }
  printf("no period found up to MAXU/4\n"); return 0; }
