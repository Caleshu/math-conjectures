#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#define MAXN 32
static int n; static unsigned adjm[MAXN]; static int deg[MAXN];
static int readg6(FILE*f){ static char s[4096]; if(!fgets(s,sizeof s,f)) return 0;
  char*p=s; if(*p=='>')p+=10; n=*p++-63; memset(adjm,0,sizeof adjm);
  int k=0,bit=0,c=0; for(int j=1;j<n;j++)for(int i=0;i<j;i++){ if(bit==0){c=*p++-63;bit=6;} bit--; if(c>>bit&1){adjm[i]|=1u<<j;adjm[j]|=1u<<i;} k++;}
  for(int i=0;i<n;i++)deg[i]=__builtin_popcount(adjm[i]); return 1;}
