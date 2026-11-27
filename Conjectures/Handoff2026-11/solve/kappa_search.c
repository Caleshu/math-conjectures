// k=2: count m<=M with kappa4(m^2-1) < m  (each gives anomaly B=c*m, y=c^2, c=kappa4).
// k=3: find m<=M with kappa6(m^3-1) < m  (each gives anomaly B=c*m, y=c^3, c=kappa6; checked exactly later).
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
typedef unsigned __int128 u128;
static uint64_t mulmod(uint64_t a,uint64_t b,uint64_t p){return (u128)a*b%p;}
static uint64_t pw(uint64_t a,uint64_t e,uint64_t p){uint64_t r=1;a%=p;while(e){if(e&1)r=mulmod(r,a,p);a=mulmod(a,a,p);e>>=1;}return r;}
static int64_t sqrtmod(uint64_t n,uint64_t p){ // Tonelli-Shanks, p odd prime
  n%=p; if(n==0) return 0; if(pw(n,(p-1)/2,p)!=1) return -1;
  uint64_t q=p-1,s=0; while(!(q&1)){q>>=1;s++;} uint64_t z=2; while(pw(z,(p-1)/2,p)!=p-1) z++;
  uint64_t M=s,c=pw(z,q,p),t=pw(n,q,p),R=pw(n,(q+1)/2,p);
  while(t!=1){ uint64_t i=0,tt=t; while(tt!=1){tt=mulmod(tt,tt,p);i++;} uint64_t b=c; for(uint64_t j=0;j<M-i-1;j++) b=mulmod(b,b,p); M=i;c=mulmod(b,b,p);t=mulmod(t,c,p);R=mulmod(R,b,p);} return R;}
int main(int argc,char**argv){ long M=atol(argv[1]); long P=M+2; // primes up to M+2 suffice for m-1,m+1; for m^2+m+1 need sqrt bound
  long S=(long)sqrtl((long double)M*M+M+1)+2; if(S<P) S=P;
  unsigned char*comp=calloc(S+1,1); for(long i=2;(long)i*i<=S;i++) if(!comp[i]) for(long j=i*i;j<=S;j+=i) comp[j]=1;
  // ---- k=2 ----
  // logk[m] = log kappa4(m^2-1); rem tracked via factoring m-1 and m+1 using primes
  double *lk=calloc(M+1,sizeof(double)); uint64_t *r1=malloc(8*(M+3)); // remaining cofactor of m-1 and m+1 stored per integer n = m-1 or m+1: factor n itself
  // factor all n<=M+1 by sieve: store exponent sums per m via combining n=m-1 and n=m+1. Simpler: per prime p, for multiples n of p, compute v_p(n); add to m=n+1 and m=n-1.
  int *dummy=0; (void)dummy;
  // use arrays of exponent of current prime: process prime by prime
  for(long n=0;n<=M+1;n++) r1[n]=n;
  // We need v_p(m^2-1)=v_p(m-1)+v_p(m+1) per prime p and m. Process each prime: for each m with p|(m-1) or p|(m+1).
  for(long p=2;p<=M+1;p++){ if(comp[p]) continue;
    // collect for m in progression m≡1 mod p and m≡-1 mod p (for p=2 same class)
    for(int side=0;side<2;side++){ long start = side==0 ? 1+p : p-1; if(p==2 && side==1) break;
      for(long m=start; m<=M; m+=p){ int e=0; uint64_t a=m-1,b=m+1; while(a%p==0&&a){a/=p;e++;} while(b%p==0){b/=p;e++;} // full v_p of (m-1)(m+1)
        lk[m]+= ((e+3)/4)*log((double)p); }
    }
  }
  // NOTE: for p=2 both m-1,m+1 even handled in side 0 since m odd => m≡1 mod 2; ok. For odd p, p divides at most one of m±1, sides disjoint.
  long cnt2=0; for(long m=3;m<=M;m++){ if(lk[m] < log((double)m)-1e-9) { cnt2++; if(m<200 || (cnt2%50==0)) {} } }
  printf("k=2: m<=%ld with kappa4(m^2-1)<m : %ld\n",M,cnt2);
  long shown=0; for(long m=3;m<=M&&shown<40;m++) if(lk[m] < log((double)m)-1e-9){ printf(" m=%ld c=%.0f",m,exp(lk[m])); shown++; } printf("\n");
  // ---- k=3 ---- v_p(m^3-1)=v_p(m-1)+v_p(m^2+m+1)
  for(long m=0;m<=M;m++){ lk[m]=0; r1[m]=(uint64_t)m*m+m+1; }
  for(long p=2;p<=S;p++){ if(comp[p]) continue;
    // part m-1
    if(p<=M) for(long m=1+p;m<=M;m+=p){ uint64_t a=m-1; int e=0; while(a%p==0){a/=p;e++;} // combine with m^2+m+1 exponent below; accumulate raw exponent in a temp? store via ceil per factor? need joint
      // joint: if p | m-1 and p | m^2+m+1 then p=3 (m≡1 mod 3). handle p=3 jointly below.
      if(p!=3) lk[m]+=((e+5)/6)*log((double)p); }
    // part m^2+m+1 roots
    long roots[2]; int nr=0;
    if(p==3){ roots[0]=1; nr=1; }
    else if(p%3==1){ int64_t r=sqrtmod(p-3,p); if(r<0){fprintf(stderr,"err\n");return 1;} long inv2=(p+1)/2; roots[0]=mulmod((uint64_t)((r-1+p)%p),inv2,p); roots[1]=mulmod((uint64_t)((p-1-r+p)%p),inv2,p); nr=2; }
    for(int i=0;i<nr;i++) for(long m=roots[i]; m<=M; m+=p){ if(m<2) continue; int e=0; while(r1[m]%p==0){r1[m]/=p;e++;}
      if(p==3){ uint64_t a=m-1; while(a%3==0&&a){a/=3;e++;} }
      lk[m]+=((e+5)/6)*log((double)p); }
    if(p==3){ for(long m=2;m<=M;m++) if(m%3!=1){ uint64_t a=m-1; int e=0; while(a%3==0&&a){a/=3;e++;} if(e) lk[m]+=((e+5)/6)*log(3.0);} }
  }
  long cnt3=0; for(long m=2;m<=M;m++){ double l=lk[m]; if(r1[m]>1) l+=log((double)r1[m]); if(l < log((double)m)-1e-9){ cnt3++; printf("k=3 candidate m=%ld log-kappa6=%.3f\n",m,l);} }
  printf("k=3: m<=%ld with kappa6(m^3-1)<m : %ld\n",M,cnt3);
}
