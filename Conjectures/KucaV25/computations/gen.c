// V(2,n): a1=2, a2=n, next = least integer > last with exactly one representation a_i + a_j (i<=j).
// Direct generation up to LIM with representation counts (capped at 2) using the term list.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int c,char**v){ int n=atoi(v[1]); long LIM=atol(v[2]);
  char *in=calloc(LIM+1,1); unsigned char *cnt=calloc(LIM+1,1); long *t=malloc(sizeof(long)*LIM); long nt=0;
  // add term: update counts of sums with all existing terms (including itself)
  #define ADD(a) { t[nt++]=a; in[a]=1; for(long i=0;i<nt;i++){ long s=t[i]+a; if(s<=LIM && cnt[s]<2) cnt[s]++; } }
  ADD(2); ADD(n);
  long evens[64]; int ne=0; evens[ne++]=2; if(n%2==0) evens[ne++]=n;
  for(long m=n+1;m<=LIM;m++) if(cnt[m]==1){ ADD(m); if(m%2==0){ evens[ne++]=m; printf("even term %ld\n",m); fflush(stdout);} }
  printf("n=%d terms<=%ld: %ld; even terms:",n,LIM,nt); for(int i=0;i<ne;i++) printf(" %ld",evens[i]); printf("\n");
  FILE*f=fopen(v[3],"wb"); fwrite(in,1,LIM+1,f); fclose(f);
}
