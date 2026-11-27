#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
static int adm(uint64_t k,uint64_t a1,uint64_t a2){ return !((k&(a1<<2))||((k<<2)&a1)||(k&(a2<<1))||((k<<1)&a2)); }
static int bl(uint64_t x){int b=0; while(x){b++;x>>=1;} return b;}
int main(int argc,char**argv){ long N=atol(argv[1]); long M=1L<<atoi(argv[2]);
  unsigned char*used=calloc(M,1); uint64_t *a=malloc(sizeof(uint64_t)*N); a[0]=0;a[1]=1;used[0]=used[1]=1; long low=2;
  long cntHigh2=0, cntOther=0, maxwait=0;
  // check submask lemma too
  long subviol=0;
  for(long n=2;n<N;n++){ uint64_t k=low; for(;;k++){ if(k>=(uint64_t)M){printf("cap\n");return 1;} if(!used[k] && adm(k,a[n-1],a[n-2])) break; }
    a[n]=k; used[k]=1;
    // submask lemma check (sample: all proper submasks via iteration if popcount<=12)
    if(__builtin_popcountll(k)<=12){ for(uint64_t sub=(k-1)&k;;sub=(sub-1)&k){ if(!used[sub]) {subviol++;break;} if(sub==0)break; } }
    if((long)k==low){ // smallest missing placed
      int L=bl(k)+2; uint64_t m=(1ULL<<L)-1;
      int h1=((a[n-1]&m)==0), h2=((a[n-2]&m)==0);
      if(h1&&h2) cntHigh2++; else cntOther++;
      if(n<400000 && (n<3000 || !(h1&&h2))) {} 
      if(!(h1&&h2) && k>100) printf("s=%lu placed n=%ld prev2 low=(%lu,%lu) h1=%d h2=%d\n",k,n,a[n-1]&m,a[n-2]&m,h1,h2);
    }
    while(used[low]) low++; }
  printf("smallest-missing placements: both previous two high-only(mod 2^(bits+2)) = %ld, other = %ld; submask violations=%ld\n",cntHigh2,cntOther,subviol);
}
