#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
static FILE *terrain_log;
#include "amok_fast_terrain.c"
int main(void){
 assert(VirtualAlloc((void*)0x480000,0x80000,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE));
 unsigned char heights[256*64],textures[256*64];
 unsigned short definitions[32*32];
 for(unsigned i=0;i<sizeof(heights);i++){heights[i]=(unsigned char)(i*7);textures[i]=(unsigned char)(i*13);}
 for(unsigned i=0;i<32*16;i++){definitions[i*2]=(i*3)&255;definitions[i*2+1]=(i*5)&255;}
 *(unsigned char**)0x4f9ef4=heights;*(unsigned char**)0x4f9ef8=textures;*(unsigned char**)0x4f9efc=(unsigned char*)definitions;
 unsigned short *map=(unsigned short*)0x4eb854;
 for(unsigned i=0;i<4096;i++)map[i]=(i*17)&31;
 terrain_log=stdout;prepare_fast_terrain();
 for(int y=-40;y<2090;y+=7)for(int x=-40;x<2090;x+=11){
  unsigned xx=(unsigned)x&2047,yy=(unsigned)y&2047;
  if((unsigned)y>=2048){xx&=31;yy&=31;}
  assert(far_world[yy*2048+xx]==reference_world(x,y));
 }
 map[0]=11;prepare_fast_terrain();assert(far_world[0]==reference_world(0,0));
 heights[0]^=127;cache_ready=0;prepare_fast_terrain();assert(far_world[2048*32]==reference_world(0,32));
 LARGE_INTEGER frequency,start,middle,end;QueryPerformanceFrequency(&frequency);
 volatile unsigned checksum=0;
 QueryPerformanceCounter(&start);
 for(unsigned i=0;i<1000000;i++)checksum+=reference_world((i*17)&2047,(i*29)&2047);
 QueryPerformanceCounter(&middle);
 for(unsigned i=0;i<1000000;i++)checksum+=far_world[((i*29)&2047)*2048+((i*17)&2047)];
 QueryPerformanceCounter(&end);
 printf("Parity, changed map chunk and level invalidation passed. Direct %.2f ms; decoded %.2f ms; checksum %u\n",
  (middle.QuadPart-start.QuadPart)*1000.0/frequency.QuadPart,(end.QuadPart-middle.QuadPart)*1000.0/frequency.QuadPart,checksum);
 return 0;
}
