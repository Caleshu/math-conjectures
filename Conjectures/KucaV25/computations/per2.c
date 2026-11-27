#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
// b[j] for odd u=2j+1. state: bit i = b[j-1-i], i=0..25
static inline uint32_t step(uint32_t s){ int k=(s&1)+((s>>4)&1)+((s>>25)&1); uint32_t nb=(k==1); return ((s<<1)|nb)&((1u<<26)-1); }
int main(){ long LIM=2000000; char*in=malloc(LIM+1); FILE*f=fopen("v5.bin","rb"); fread(in,1,LIM+1,f); fclose(f);
  // initial state at u=53 (j=26): bits b[25..0]
  uint32_t s=0; for(int i=0;i<26;i++){ long u=53-2*(i+1); s|=(uint32_t)in[u]<<i; }
  // check simulation matches data
  uint32_t t=s; long mism=0; for(long u=53;u<=LIM;u+=2){ t=step(t); if((t&1)!=in[u]) mism++; }
  printf("simulation mismatches vs data: %ld\n",mism);
  // Brent cycle detection from state s (state before u=53)
  uint32_t tort=s, hare=step(s); long power=1, lam=1;
  while(tort!=hare){ if(power==lam){ tort=hare; power*=2; lam=0; } hare=step(hare); lam++; }
  // mu
  tort=s; hare=s; for(long i=0;i<lam;i++) hare=step(hare); long mu=0; while(tort!=hare){ tort=step(tort); hare=step(hare); mu++; }
  printf("period (in odd steps) = %ld, preperiod = %ld  => in integers: period %ld, starts by u = %ld\n",lam,mu,2*lam,53+2*mu);
}
