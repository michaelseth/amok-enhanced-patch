/* Decode the same source data once; refresh map chunks when their IDs change. */
__attribute__((used)) static unsigned short far_world[2048*2048];
__attribute__((used)) static volatile int cache_ready;
static unsigned short cached_macro[4096];
static unsigned char macro_valid[4096];
static LARGE_INTEGER terrain_frequency, previous_terrain_frame;
static double terrain_frame_sum, terrain_frame_max;
static unsigned terrain_frame_count;
#ifdef AMOK_RENDER_PROFILE
#ifdef AMOK_RAY_PRECISION
#include "amok_ray_precision.c"
#endif
#ifdef AMOK_TERRAIN_STAGE
#include "amok_terrain_staging.c"
#endif
static LARGE_INTEGER terrain_render_start;
static double terrain_render_sum, terrain_render_max;
static unsigned terrain_render_count;
__attribute__((used,noinline)) static void begin_terrain_render(void){
 QueryPerformanceCounter(&terrain_render_start);
#ifdef AMOK_RAY_PRECISION
 begin_ray_precision();
#endif
#ifdef AMOK_TERRAIN_STAGE
 begin_terrain_stage();
#endif
}
__attribute__((used,noinline)) static void end_terrain_render(void){
#ifdef AMOK_TERRAIN_STAGE
 end_terrain_stage();
#endif
 LARGE_INTEGER end;QueryPerformanceCounter(&end);
 double ms=(end.QuadPart-terrain_render_start.QuadPart)*1000.0/terrain_frequency.QuadPart;
 terrain_render_sum+=ms;if(ms>terrain_render_max)terrain_render_max=ms;
 if(++terrain_render_count==120){
  if(terrain_log){fprintf(terrain_log,"Terrain drawing cost: mean %.2f ms, max %.2f ms (120 frames).\n",terrain_render_sum/120,terrain_render_max);fflush(terrain_log);}
  terrain_render_sum=terrain_render_max=0;terrain_render_count=0;
 }
}
__attribute__((naked)) static void terrain_render_bridge(void){
 __asm__ volatile("pushfl\n pushal\n call _begin_terrain_render\n popal\n popfl\n push $1f\n push $0x6a0396\n ret\n 1: pushfl\n pushal\n call _end_terrain_render\n popal\n popfl\n ret\n");
}
#endif

static unsigned short reference_world(int x,int y){
 unsigned tx=((unsigned)x>>3)&255,ty=((unsigned)y>>3)&255;
 if((y>>3)<0||(y>>3)>255){tx&=3;ty&=3;}
 unsigned id=((unsigned short*)0x4eb854)[(ty>>2)*64+(tx>>2)];
 unsigned short *pair=(unsigned short*)(*(unsigned char**)0x4f9efc+id*64+((ty&3)*4+(tx&3))*4);
 unsigned local=((unsigned)y&7)*8+((unsigned)x&7);
 return ((unsigned)(*(unsigned char**)0x4f9ef4)[pair[0]*64+local]<<8)
        |(*(unsigned char**)0x4f9ef8)[pair[1]*64+local];
}
__attribute__((used,noinline)) static void prepare_fast_terrain(void){
 LARGE_INTEGER now;QueryPerformanceCounter(&now);
 if(!terrain_frequency.QuadPart)QueryPerformanceFrequency(&terrain_frequency);
 if(previous_terrain_frame.QuadPart){
  double ms=(now.QuadPart-previous_terrain_frame.QuadPart)*1000.0/terrain_frequency.QuadPart;
  if(ms<250){
   terrain_frame_sum+=ms;if(ms>terrain_frame_max)terrain_frame_max=ms;
   if(++terrain_frame_count==120){
    if(terrain_log){fprintf(terrain_log,"Terrain frame intervals: mean %.2f ms, max %.2f ms (120 frames).\n",terrain_frame_sum/120,terrain_frame_max);fflush(terrain_log);}
    terrain_frame_sum=terrain_frame_max=0;terrain_frame_count=0;
   }
  }
 }
 previous_terrain_frame=now;
 int fresh=!cache_ready;
 if(fresh)memset(macro_valid,0,sizeof(macro_valid));
 unsigned short *map=(unsigned short*)0x4eb854;
 unsigned char *definitions=*(unsigned char**)0x4f9efc;
 unsigned char *heights=*(unsigned char**)0x4f9ef4;
 unsigned char *textures=*(unsigned char**)0x4f9ef8;
 for(unsigned macro=0;macro<4096;macro++){
  unsigned id=map[macro];
  if(macro_valid[macro]&&cached_macro[macro]==id)continue;
  unsigned bx=(macro&63)*32,by=(macro>>6)*32;
  for(unsigned tile=0;tile<16;tile++){
   unsigned short *pair=(unsigned short*)(definitions+id*64+tile*4);
   unsigned char *h=heights+pair[0]*64,*t=textures+pair[1]*64;
   unsigned x=bx+(tile&3)*8,y=by+(tile>>2)*8;
   for(unsigned row=0;row<8;row++)for(unsigned col=0;col<8;col++)
    far_world[(y+row)*2048+x+col]=((unsigned)h[row*8+col]<<8)|t[row*8+col];
  }
  cached_macro[macro]=(unsigned short)id;macro_valid[macro]=1;
 }
 cache_ready=1;
 if(fresh&&terrain_log){
  unsigned state=12345,mismatch=0;
  for(unsigned i=0;i<20000;i++){
   state=state*1664525+1013904223;int x=(int)(state&8191)-4096;
   state=state*1664525+1013904223;int y=(int)(state&8191)-4096;
   unsigned xx=(unsigned)x&2047,yy=(unsigned)y&2047;
   if((unsigned)y>=2048){xx&=31;yy&=31;}
   mismatch+=far_world[yy*2048+xx]!=reference_world(x,y);
  }
  fprintf(terrain_log,"Decoded terrain parity: 20000 samples, %u mismatches (including map boundaries).\n",mismatch);
  fflush(terrain_log);
 }
}
__attribute__((naked)) static void terrain_frame_bridge(void){
 __asm__ volatile("pushfl\n pushal\n call _prepare_fast_terrain\n popal\n popfl\n push %ebx\n push %ecx\n push %edx\n push %esi\n push %edi\n push %ebp\n push $0x420372\n ret\n");
}
__attribute__((naked)) static void terrain_level_bridge(void){
 __asm__ volatile("mov %edx,0x4f9efc\n movl $0,_cache_ready\n push $0x4117aa\n ret\n");
}
static int install_fast_terrain(void){
 unsigned char *sites[]={(unsigned char*)0x42036c,(unsigned char*)0x4117a4};
 const unsigned char expected[][6]={{0x53,0x51,0x52,0x56,0x57,0x55},{0x89,0x15,0xfc,0x9e,0x4f,0x00}};
 unsigned char *destinations[]={(unsigned char*)terrain_frame_bridge,(unsigned char*)terrain_level_bridge};
 for(int i=0;i<2;i++)if(memcmp(sites[i],expected[i],6))return 0;
 for(int i=0;i<2;i++){
  DWORD old;VirtualProtect(sites[i],6,PAGE_EXECUTE_READWRITE,&old);
  sites[i][0]=0xe9;*(int32_t*)(sites[i]+1)=(int32_t)(destinations[i]-(sites[i]+5));sites[i][5]=0x90;
  FlushInstructionCache(GetCurrentProcess(),sites[i],6);VirtualProtect(sites[i],6,old,&old);
 }
#ifdef AMOK_RENDER_PROFILE
#ifdef AMOK_RAY_PRECISION
 if(!install_ray_precision())return 0;
#endif
#ifdef AMOK_TERRAIN_STAGE
 if(!install_terrain_stage())return 0;
#endif
 unsigned char *render_site=(unsigned char*)0x42066f;
 static const unsigned char original_call[]={0xe8,0x22,0xfd,0x27,0x00};
 if(memcmp(render_site,original_call,5))return 0;
 DWORD old;VirtualProtect(render_site,5,PAGE_EXECUTE_READWRITE,&old);
 render_site[0]=0xe8;*(int32_t*)(render_site+1)=(int32_t)((unsigned char*)terrain_render_bridge-(render_site+5));
 FlushInstructionCache(GetCurrentProcess(),render_site,5);VirtualProtect(render_site,5,old,&old);
#endif
 if(terrain_log){fprintf(terrain_log,"Fast decoded terrain renderer installed; refreshes each frame and rebuilds on level load.\n");fflush(terrain_log);}
 return 1;
}
