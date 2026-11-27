// Given T (exact to N0 by simulation, then odd recurrence), periodic from u0 with period P:
// prove no even w > N0 has exactly one representation.
// (i) direct count r(w) for even w in (N0, WB], WB = 2*u0 + 4*P + 2 ; (ii) S(rho) >= 1 for all even rho mod P.
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
int main(int argc,char**argv){ FILE*f=fopen(argv[1],"rb"); long n,P,u0,MAXU; fread(&n,8,1,f);fread(&P,8,1,f);fread(&u0,8,1,f);fread(&MAXU,8,1,f);
  unsigned char*T=malloc(MAXU+1); fread(T,1,MAXU+1,f); fclose(f); long N0=atol(argv[2]);
  long E[3]={2,2*n,2*n*n+2};
  long WB=2*u0+4*P+2; if(WB+P>MAXU){printf("MAXU too small\n");return 1;}
  long *odd=malloc(sizeof(long)*(MAXU/2+2)); long no=0; for(long v=1;v<=WB;v++) if(v%2&&T[v]) odd[no++]=v;
  long minr=1L<<60, bad=0;
  for(long w=N0+1; w<=WB; w++){ if(w%2) continue; if(T[w]){printf("even term %ld present?!\n",w);bad++;}
    long r=0; for(int i=0;i<3;i++) for(int j=i;j<3;j++) if(E[i]+E[j]==w) r++;
    for(long i=0;i<no && odd[i]<=w/2;i++) if(T[w-odd[i]]) r++;
    if(r==1){ printf("w=%ld has unique representation!\n",w); bad++; }
    if(r<minr) minr=r; }
  // (ii)
  long minS=1L<<60; long argmin=-1;
  for(long rho=0; rho<P; rho+=2){ long S=0; for(long o=u0;o<u0+P;o++){ if(!(o%2)||!T[o]) continue; long o2=((rho-o)%P+P)%P; // need representative >= u0
        long v=o2; while(v<u0) v+=P; if(T[v]) S++; }
    if(S<minS){minS=S;argmin=rho;} }
  printf("n=%ld P=%ld u0=%ld: direct range (%ld,%ld]: min reps=%ld, violations=%ld; tail: min_rho S(rho)=%ld (at rho=%ld)\n",n,P,u0,N0,WB,minr,bad,minS,argmin);
  if(bad==0 && minS>=1) printf("PROOF COMPLETE for n=%ld: even terms are exactly 2, %ld, %ld\n",n,2*n,2*n*n+2);
}
