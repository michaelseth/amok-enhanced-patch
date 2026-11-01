#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#define AMOK_RAY_TEST
#include "amok_ray_precision.c"
int main(void){
 unsigned long checked=0;
 for(int trig=-32767;trig<=32767;trig++){
  int span=(((trig*13)>>2)*3)>>2;
  RayStepper s={span/960,span%960,0,960};
  int value=0;
  for(int column=1;column<=1920;column++){
   value+=ray_step(&s);
   int expected=(int)(((int64_t)span*column)/960);
   if(value!=expected||abs(s.error)>=960){fprintf(stderr,"Mismatch at %d/%d\n",trig,column);return 1;}
   checked++;
  }
 }
 printf("%lu ray positions match exact signed division; endpoints and remainder bounds verified.\n",checked);
 return 0;
}
