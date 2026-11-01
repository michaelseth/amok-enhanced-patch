/* Preserve every native-resolution pixel, but draw columns contiguously first. */
#include <emmintrin.h>
#ifndef STAGE_U32
#define STAGE_U32(a) (*(uint32_t*)(a))
#define STAGE_U16(a) (*(unsigned short*)(a))
#endif
static uint32_t *terrain_stage;
static unsigned stage_capacity;
__attribute__((used)) static int terrain_column_stride=4;
__attribute__((used)) static int terrain_stage_column;
static uint32_t original_terrain_base, original_terrain_pitch;
static unsigned stage_height, stage_columns;
static int terrain_stage_active;
static int terrain_stage_enabled=1,terrain_stage_checked;
static uint32_t *stage_reference_pixels,*stage_reference_clip;
static int stage_reference_pending;
__attribute__((naked)) static void render_terrain_reference(void){
 __asm__ volatile("mov $0x686e38,%eax\n push $0x6a0396\n ret\n");
}

__attribute__((used,noinline)) static void begin_terrain_stage(void){
 unsigned width=STAGE_U32(0x49009c),height=STAGE_U32(0x4900a8);
 unsigned columns=STAGE_U16(0x686ea0);
 unsigned pitch=STAGE_U16(0x686ea8);
 terrain_stage_active=0;terrain_column_stride=4;
 terrain_stage_column=0;
 /* Only the full native viewport and stock two-pixel columns are supported. */
 if(!terrain_stage_enabled||width!=3840||height!=2160||columns!=width/2||pitch!=width*2)return;
 if(!terrain_stage_checked){
  unsigned entries=1+STAGE_U16(0x686ea6)/2;
  stage_reference_pixels=(uint32_t*)VirtualAlloc(NULL,columns*height*4,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
  stage_reference_clip=(uint32_t*)VirtualAlloc(NULL,columns*entries*4,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
  if(stage_reference_pixels&&stage_reference_clip){
   render_terrain_reference();
   memcpy(stage_reference_pixels,(void*)STAGE_U32(0x686e84),columns*height*4);
   memcpy(stage_reference_clip,(void*)STAGE_U32(0x686e88),columns*entries*4);
   stage_reference_pending=1;
  }
  terrain_stage_checked=1;
 }
 if(stage_capacity<columns*height){
  if(terrain_stage)VirtualFree(terrain_stage,0,MEM_RELEASE);
  terrain_stage=(uint32_t*)VirtualAlloc(NULL,columns*height*4,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);
  if(!terrain_stage){stage_capacity=0;return;}
  stage_capacity=columns*height;
 }
 original_terrain_base=STAGE_U32(0x686e84);
 original_terrain_pitch=pitch;stage_height=height;stage_columns=columns;
 STAGE_U32(0x686e84)=(uint32_t)terrain_stage;
 STAGE_U16(0x686ea8)=4;
 terrain_column_stride=height*4;terrain_stage_active=1;
}
__attribute__((used,noinline)) static void end_terrain_stage(void){
 if(!terrain_stage_active)return;
 uint32_t *output=(uint32_t*)original_terrain_base;
 for(unsigned x=0;x<stage_columns;x+=4)for(unsigned y=0;y<stage_height;y+=4){
  __m128 a=_mm_castsi128_ps(_mm_loadu_si128((__m128i*)(terrain_stage+x*stage_height+y)));
  __m128 b=_mm_castsi128_ps(_mm_loadu_si128((__m128i*)(terrain_stage+(x+1)*stage_height+y)));
  __m128 c=_mm_castsi128_ps(_mm_loadu_si128((__m128i*)(terrain_stage+(x+2)*stage_height+y)));
  __m128 d=_mm_castsi128_ps(_mm_loadu_si128((__m128i*)(terrain_stage+(x+3)*stage_height+y)));
  _MM_TRANSPOSE4_PS(a,b,c,d);
  _mm_storeu_si128((__m128i*)(output+y*stage_columns+x),_mm_castps_si128(a));
  _mm_storeu_si128((__m128i*)(output+(y+1)*stage_columns+x),_mm_castps_si128(b));
  _mm_storeu_si128((__m128i*)(output+(y+2)*stage_columns+x),_mm_castps_si128(c));
  _mm_storeu_si128((__m128i*)(output+(y+3)*stage_columns+x),_mm_castps_si128(d));
 }
 /* Sprite occlusion stores physical framebuffer addresses, including row edges. */
 uint32_t *clip=(uint32_t*)STAGE_U32(0x686e88);
 unsigned entries=1+STAGE_U16(0x686ea6)/2;
 for(unsigned x=0;x<stage_columns;x++){
  uint32_t bottom=(uint32_t)(terrain_stage+x*stage_height);
  uint32_t actual=original_terrain_base+x*4;
  for(unsigned n=0;n<entries;n++){
   int rows=(int)(clip[x*entries+n]-bottom)/4;
   clip[x*entries+n]=actual+rows*original_terrain_pitch;
  }
 }
 STAGE_U32(0x686e84)=original_terrain_base;STAGE_U16(0x686ea8)=original_terrain_pitch;
 if(stage_reference_pending){
  unsigned pixels_bad=0,clip_bad=0;
  unsigned below_horizon_bad=0;
  for(unsigned i=0;i<stage_columns*stage_height;i++)if(output[i]!=stage_reference_pixels[i]){
   unsigned x=i%stage_columns,y=i/stage_columns;
   int horizon=(int)(stage_reference_clip[x*entries+entries-1]-(original_terrain_base+x*4))/(int)original_terrain_pitch;
   below_horizon_bad+=(int)y>horizon;
   if(pixels_bad<8&&terrain_log)fprintf(terrain_log,"Staging mismatch x=%u y=%u horizon=%d direct=%08x staged=%08x\n",x,y,horizon,stage_reference_pixels[i],output[i]);
   pixels_bad++;
  }
  for(unsigned i=0;i<stage_columns*entries;i++)clip_bad+=clip[i]!=stage_reference_clip[i];
  if(terrain_log){fprintf(terrain_log,"Native staging comparison: %u pixel-pair mismatches (%u below horizon); %u occlusion-pointer mismatches.\n",pixels_bad,below_horizon_bad,clip_bad);fflush(terrain_log);}
  if(pixels_bad||clip_bad){
   memcpy(output,stage_reference_pixels,stage_columns*stage_height*4);
   memcpy(clip,stage_reference_clip,stage_columns*entries*4);
   terrain_stage_enabled=0;terrain_column_stride=4;
  }
  VirtualFree(stage_reference_pixels,0,MEM_RELEASE);VirtualFree(stage_reference_clip,0,MEM_RELEASE);
  stage_reference_pending=0;
 }
}
__attribute__((naked)) static void terrain_next_column_bridge(void){
 __asm__ volatile("push %eax\n mov _terrain_column_stride,%eax\n add %eax,0x6a08e0\n cmp $4,%eax\n je 2f\n add %eax,0x6a0924\n add %eax,0x6a0928\n incl _terrain_stage_column\n cmpl $1,_terrain_stage_column\n jne 2f\n decl 0x6a0924\n decl 0x6a0928\n 2: pop %eax\n push $0x6a0871\n ret\n");
}
static int install_terrain_stage(void){
 unsigned char *site=(unsigned char*)0x6a086a;
 static const unsigned char expected[]={0x83,0x05,0xe0,0x08,0x6a,0x00,0x04};
 if(memcmp(site,expected,7))return 0;
 DWORD old;VirtualProtect(site,7,PAGE_EXECUTE_READWRITE,&old);
 site[0]=0xe9;*(int32_t*)(site+1)=(int32_t)((unsigned char*)terrain_next_column_bridge-(site+5));
 memset(site+5,0x90,2);FlushInstructionCache(GetCurrentProcess(),site,7);VirtualProtect(site,7,old,&old);
 return 1;
}


