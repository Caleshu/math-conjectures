#include <stdio.h>
#include <stdlib.h>
int main(int argc,char**argv){ long n=atol(argv[1]), N0=atol(argv[2]), MAXU=atol(argv[3]);
  unsigned char*T=calloc(MAXU+1,1); long*terms=malloc(8*(N0+2)); int nt=0; T[2]=1;T[n]=1;terms[nt++]=2;terms[nt++]=n;
  for(long u=n+1;u<=N0;u++){int c=0; for(int i=0;i<nt&&c<2;i++){long a=terms[i],b=u-a; if(b<a)continue; if(T[b])c++;} if(c==1){T[u]=1;terms[nt++]=u;}}
  long E1=2,E2=2*n,E3=2*n*n+2; long trip=0,lasttrip=-1, ones=0;
  for(long u=N0+1;u<=MAXU;u++){ if(u%2==0)continue; int c=T[u-E1]+T[u-E2]+T[u-E3]; if(c==3){trip++;lasttrip=u;} T[u]=(c==1); ones+=T[u]; }
  // also over exact region check triples among odd u > E3
  long trip0=0; for(long u=E3+1;u<=N0;u++) if(u%2 && T[u-E1]+T[u-E2]+T[u-E3]==3) trip0++;
  printf("n=%ld: triples in (E3,N0]=%ld, triples beyond N0 up to %ld: %ld (last at %ld); density of odd terms %.4f\n",n,trip0,MAXU,trip,lasttrip,(double)ones/((MAXU-N0)/2));
}
