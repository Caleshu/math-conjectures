#define main main_orig
#include "faulty.c"
#undef main
int main(){ // negative control: Q3 - {0,3} (two even vertices) is unbalanced -> not Hamiltonian; Q4 - {0,15}: balanced? 0 even, 15 even -> unbalanced
  n=3;N=8; for(int i=0;i<N;i++)inF[i]=0; F[0]=0;F[1]=3;fs=2;inF[0]=inF[3]=1; printf("Q3-{0,3}: %d (expect 0)\n",is_ham());
  for(int i=0;i<N;i++)inF[i]=0; F[0]=0;F[1]=7;fs=2;inF[0]=inF[7]=1; printf("Q3-{0,7}: %d (expect 1)\n",is_ham());
  n=4;N=16; for(int i=0;i<N;i++)inF[i]=0; F[0]=0;F[1]=1;F[2]=2;F[3]=4;fs=4; inF[0]=inF[1]=inF[2]=inF[4]=1; printf("Q4-{0,1,2,4}: %d (expect 0: vertex 3? 3's nbrs 1,2 removed ->deg<2)\n",is_ham());
}
