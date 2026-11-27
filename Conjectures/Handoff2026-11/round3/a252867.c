// a(0)=0,a(1)=1,a(2)=2; a(n)= smallest unused k with (k & a(n-1))==0 and (k & a(n-2))!=0.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc,char**argv){ long N=atol(argv[1]); long M=1L<<27; unsigned char*used=calloc(M,1);
  long a2=1,a1=2; used[0]=used[1]=used[2]=1; long low=3, maxv=2;
  for(long n=3;n<N;n++){ long k=low; while(used[k] || (k&a1) || !(k&a2)) { k++; if(k>=M){printf("overflow n=%ld\n",n);return 1;} }
    used[k]=1; if(k>maxv)maxv=k; a2=a1; a1=k; while(used[low]) low++;
    if(n<25) printf("%ld ",k);
    if((n&(n-1))==0 && n>=1024) printf("\nn=%ld smallest-missing=%ld max=%ld",n,low,maxv);
  }
  printf("\nN=%ld smallest missing=%ld max term=%ld\n",N,low,maxv); return 0;}
