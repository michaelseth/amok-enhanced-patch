/* Renderer-only experimental range extension. Game physics retain their cache. */
static uint32_t far_palettes[280];
static unsigned long near_samples, near_mismatches, far_samples;
static FILE *terrain_log;
#ifdef AMOK_FAST_TERRAIN
#include "amok_fast_terrain.c"
#endif

__attribute__((used,noinline)) static int sample_far_terrain(void) {
 int x=*(volatile int*)0x6a08e8 >> 16;
 int y=*(volatile int*)0x6a08ec >> 16;
 unsigned tx=((unsigned)x>>3)&255, ty=((unsigned)y>>3)&255;
 /* Match the original loader's out-of-map Y boundary handling. */
 if ((y>>3)<0 || (y>>3)>255) { tx&=3;ty&=3; }
 unsigned macro=(ty>>2)*64+(tx>>2);
 unsigned tile=(ty&3)*4+(tx&3);
 unsigned short macro_id=((unsigned short*)0x4eb854)[macro];
 unsigned char *definitions=*(unsigned char**)0x4f9efc;
 unsigned char *heights=*(unsigned char**)0x4f9ef4;
 unsigned char *textures=*(unsigned char**)0x4f9ef8;
 unsigned short *pair=(unsigned short*)(definitions+(unsigned)macro_id*64+tile*4);
 unsigned local=((unsigned)y&7)*8+((unsigned)x&7);
 unsigned value=((unsigned)heights[(unsigned)pair[0]*64+local]<<8)
               | textures[(unsigned)pair[1]*64+local];
 int cx=*(volatile int*)0x48a8f0 >> 16;
 int cy=*(volatile int*)0x48a8f4 >> 16;
 int dx=x-cx,dy=y-cy;
 if(dx>=-96 && dx<=96 && dy>=-96 && dy<=96 && near_samples<10000){
  unsigned cached=((unsigned short*)0x4cb834)[((unsigned)y&255)*256+((unsigned)x&255)];
  near_samples++;near_mismatches+=(cached!=value);
  if(near_samples==10000 && terrain_log){
   fprintf(terrain_log,"Near-cache comparison: %lu samples, %lu mismatches\n",near_samples,near_mismatches);fflush(terrain_log);
  }
 }
 if((dx>150||dx<-150||dy>150||dy<-150) && far_samples++==0 && terrain_log){
  fprintf(terrain_log,"First extended-range sample: relative coordinates %d, %d\n",dx,dy);fflush(terrain_log);
 }
 return (short)value;
}
__attribute__((naked)) static void terrain_sample_bridge(void){
#ifdef AMOK_FAST_TERRAIN
 __asm__ volatile("push %eax\n push %ecx\n mov 0x6a08e8,%eax\n sar $16,%eax\n and $2047,%eax\n mov 0x6a08ec,%edx\n sar $16,%edx\n cmp $2048,%edx\n jb 1f\n and $31,%eax\n and $31,%edx\n 1: and $2047,%edx\n shl $11,%edx\n add %eax,%edx\n movswl _far_world(,%edx,2),%edx\n pop %ecx\n pop %eax\n ret\n");
#else
 __asm__ volatile("push %ecx\n push %eax\n call _sample_far_terrain\n mov %eax,%edx\n pop %eax\n pop %ecx\n ret\n");
#endif
}
static int install_far_terrain(void){
 static const unsigned char expected[25]={0xa1,0xe8,0x08,0x6a,0x00,0xc1,0xe8,0x10,0x8a,0x25,0xee,0x08,0x6a,0x00,0x03,0xc0,0x03,0x05,0xd8,0x08,0x6a,0x00,0x0f,0xbf,0x10};
 unsigned char *sites[2]={(unsigned char*)0x6a0665,(unsigned char*)0x6a06e5};
 terrain_log=fopen("terrain-range-status.txt","w");
#ifdef AMOK_FAST_TERRAIN
 if(!install_fast_terrain())return 0;
#endif
 for(int i=0;i<2;i++)if(memcmp(sites[i],expected,25)){
  if(terrain_log){fprintf(terrain_log,"Hook %d bytes:",i);for(int j=0;j<25;j++)fprintf(terrain_log," %02x",sites[i][j]);fprintf(terrain_log,"\n");fflush(terrain_log);}return 0;
 }
 for(int i=0;i<280;i++){
  unsigned row=0;
#ifdef AMOK_SOFT_FOG
  /* Ease into the existing level-colored fog across the final ~21% of range. */
  if(i>220){
   double t=(double)(i-220)/59.0;
   row=(unsigned)(31.0*t*t*(3.0-2.0*t)+0.5);
  }
#endif
  far_palettes[i]=0x4fb6b8+row*256;
 }
 for(int i=0;i<2;i++){
  DWORD old;VirtualProtect(sites[i],25,PAGE_EXECUTE_READWRITE,&old);
  sites[i][0]=0xe8;*(int32_t*)(sites[i]+1)=(int32_t)((unsigned char*)terrain_sample_bridge-(sites[i]+5));
  memset(sites[i]+5,0x90,20);FlushInstructionCache(GetCurrentProcess(),sites[i],25);
  VirtualProtect(sites[i],25,old,&old);
 }
 DWORD palette_protect;
 VirtualProtect((void*)0x4205ad,4,PAGE_EXECUTE_READWRITE,&palette_protect);
 *(uint32_t*)0x4205ad=(uint32_t)far_palettes;
 FlushInstructionCache(GetCurrentProcess(),(void*)0x4205ad,4);
 VirtualProtect((void*)0x4205ad,4,palette_protect,&palette_protect);
 if(terrain_log){fprintf(terrain_log,"Extended terrain sampler installed; ray range 280, original 140.\n");fflush(terrain_log);}
 return 1;
}
