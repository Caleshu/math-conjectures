// A306211: S_1 = (1); S_{k+1} = S_k followed by RUNS(S_k) (run lengths of S_k).
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char**argv){ long CAP=atol(argv[1]); unsigned char*s=malloc(CAP); long n=1; s[0]=1;
  for(int g=1;;g++){ long m=n; long i=0; long add=0;
    // compute runs of s[0..m-1]
    long cnt[256]={0}; int mx=0; long maxrun1=0;
    while(i<m){ long j=i; while(j<m && s[j]==s[i]) j++; long r=j-i; if(n>=CAP){ goto done;} if(r>255){printf("run>255\n");return 1;} s[n++]=(unsigned char)r; i=j; }
    for(long t=0;t<n;t++){cnt[s[t]]++; if(s[t]>mx)mx=s[t];}
    printf("gen %d len %ld max %d freq:",g+1,n,mx); for(int v=1;v<=mx;v++) printf(" %d:%.3g",v,(double)cnt[v]/n); printf("\n");
  }
  done: printf("cap reached at len %ld\n",n); return 0;}
