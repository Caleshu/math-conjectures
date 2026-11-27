// A394166: lexicographically earliest sequence of distinct nonneg ints, no two pixels of the binary plot a knight's move apart.
// new term k after a2=a(n-2), a1=a(n-1): (k&(a1<<2))==0, ((k<<2)&a1)==0, (k&(a2<<1))==0, ((k<<1)&a2)==0.
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
int main(int argc,char**argv){ setvbuf(stdout,0,_IONBF,0); long N=atol(argv[1]); long M=1L<<atoi(argv[2]); unsigned char*used=calloc(M,1);
  uint64_t a2=0,a1=1; used[0]=used[1]=1; long low=2; uint64_t mx=1; int badpow=0; uint64_t nextpow=2; // first term >= nextpow must be power of 2
  long chk[]={1000,10000,100000,1000000,10000000,0}; int ci=0;
  printf("0 1 "); 
  for(long n=2;n<N;n++){ uint64_t k=low;
    for(;;k++){ if(k>=(uint64_t)M){printf("\ncap at n=%ld\n",n); goto out;} if(used[k]) continue;
      if((k&(a1<<2))||((k<<2)&a1)||(k&(a2<<1))||((k<<1)&a2)) continue; break; }
    used[k]=1; if(n<20) printf("%lu ",k);
    while(k>=nextpow){ // k is the first term >= nextpow
      if(k & (k-1)) { badpow++; printf("\nNOT POWER: n=%ld k=%lu threshold=%lu\n",n,k,nextpow);} 
      nextpow<<=1; }
    if(k>mx)mx=k; a2=a1; a1=k; while(used[low]) low++;
    if(chk[ci] && n+1==chk[ci]){ printf("\nterms=%ld smallest-missing=%ld max=%lu",n+1,low,mx); ci++; }
  }
  out: printf("\nsmallest missing=%ld max=%lu power-of-two violations=%d\n",low,mx,badpow); return 0;}
