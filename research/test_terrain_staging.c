#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
static FILE *terrain_log;
static unsigned char test_game_view[0x10000],test_game_params[0x10000];
#define STAGE_PTR(a) ((a)<0x680000?test_game_view+(a)-0x490000:test_game_params+(a)-0x680000)
#define STAGE_U32(a) (*(uint32_t*)STAGE_PTR(a))
#define STAGE_U16(a) (*(unsigned short*)STAGE_PTR(a))
#include "amok_terrain_staging.c"
int main(void){
 uint32_t *output=(uint32_t*)VirtualAlloc(NULL,3840*2160*2,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
 uint32_t *clip=(uint32_t*)VirtualAlloc(NULL,1920*141*4,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
 assert(output&&clip);
 STAGE_U32(0x49009c)=3840;STAGE_U32(0x4900a8)=2160;
 STAGE_U16(0x686ea0)=1920;STAGE_U16(0x686ea6)=280;
 STAGE_U16(0x686ea8)=7680;STAGE_U32(0x686e84)=(uint32_t)output;
 STAGE_U32(0x686e88)=(uint32_t)clip;
 terrain_stage_checked=1;begin_terrain_stage();assert(terrain_stage_active);
 for(unsigned x=0;x<1920;x++)for(unsigned y=0;y<2160;y++)terrain_stage[x*2160+y]=(x<<16)|y;
 for(unsigned x=0;x<1920;x++)for(unsigned n=0;n<141;n++){
  int row=(int)(n*17)-1;
  clip[x*141+n]=(uint32_t)terrain_stage+x*2160*4+row*4;
 }
 end_terrain_stage();
 for(unsigned y=0;y<2160;y++)for(unsigned x=0;x<1920;x++)assert(output[y*1920+x]==((x<<16)|y));
 for(unsigned x=0;x<1920;x++)for(unsigned n=0;n<141;n++){
  int row=(int)(n*17)-1;
  assert(clip[x*141+n]==(uint32_t)output+x*4+row*7680);
 }
 assert(STAGE_U16(0x686ea8)==7680&&STAGE_U32(0x686e84)==(uint32_t)output);
 puts("All 4,147,200 native pixel pairs and 270,720 sprite occlusion pointers match.");
 return 0;
}

