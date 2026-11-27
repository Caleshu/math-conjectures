// Instrument A394166: at each "record power" (first term >= 2^k), what happens to the smallest missing number?
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
static int adm(uint64_t k,uint64_t a1,uint64_t a2){ return !((k&(a1<<2))||((k<<2)&a1)||(k&(a2<<1))||((k<<1)&a2)); }
int main(int argc,char**argv){ setvbuf(stdout,0,_IONBF,0); long N=atol(argv[1]); long M=1L<<atoi(argv[2]);
  unsigned char*used=calloc(M,1); uint64_t *a=malloc(sizeof(uint64_t)*N); a[0]=0;a[1]=1;used[0]=used[1]=1; long low=2; uint64_t mx=1;
  long *firstpos=calloc(M>>8,sizeof(long)); // not used
  for(long n=2;n<N;n++){ uint64_t k=low; for(;;k++){ if(k>=(uint64_t)M){printf("cap\n");return 1;} if(!used[k] && adm(k,a[n-1],a[n-2])) break; }
    a[n]=k; used[k]=1; if(k>mx){ mx=k; if(n<N-3) printf("R n=%ld a=%lu prev=%lu smissing=%ld\n",n,k,a[n-1],low);} while(used[low]) low++; }
  // second pass: for each record, where did smissing land?
  return 0;}
