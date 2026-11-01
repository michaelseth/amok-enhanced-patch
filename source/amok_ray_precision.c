/* Distribute horizontal ray division remainders rather than discarding them
   once and accumulating their error across the whole 4K viewport. */
typedef struct { int step, remainder, error, denominator; } RayStepper;
static int ray_step(RayStepper *s){
 int delta=s->step;
 s->error+=s->remainder;
 if(s->error>=s->denominator){s->error-=s->denominator;delta++;}
 if(s->error<=-s->denominator){s->error+=s->denominator;delta--;}
 return delta;
}
#ifndef AMOK_RAY_TEST
static RayStepper ray_x,ray_y;
static unsigned ray_column,ray_columns;
static int ray_active;
static int ray_start_x,ray_start_y;
static int ray_precision_logged;
__attribute__((used,noinline)) static void begin_ray_precision(void){
 unsigned width=*(unsigned*)0x49009c;
 ray_columns=*(unsigned short*)0x686ea0;
 ray_column=0;ray_active=0;
 if(width!=3840||ray_columns!=width/2)return;
 unsigned angle=*(unsigned short*)0x686eaa;
 int s=((short*)0x579b5c)[angle],c=((short*)0x579f5c)[angle];
 int span_x=(-((c*13)>>2)*3)>>2;
 int span_y=(((s*13)>>2)*3)>>2;
 int denominator=width/4;
 ray_x=(RayStepper){span_x/denominator,span_x%denominator,0,denominator};
 ray_y=(RayStepper){span_y/denominator,span_y%denominator,0,denominator};
 /* Require the recovered numerators to match the original setup exactly. */
 if(ray_x.step!=*(int*)0x686e4c||ray_y.step!=*(int*)0x686e50)return;
 ray_start_x=*(int*)0x686e44;ray_start_y=*(int*)0x686e48;
 ray_active=1;
 if(!ray_precision_logged&&terrain_log){
  fprintf(terrain_log,"Ray precision active: %u columns, signed spacing remainders %d/%d and %d/%d.\n",
   ray_columns,ray_x.remainder,denominator,ray_y.remainder,denominator);
  fflush(terrain_log);ray_precision_logged=1;
 }
}
__attribute__((used,noinline)) static void advance_precise_ray(void){
 if(!ray_active){
  *(int*)0x6a08a0+=*(int*)0x6a08a8;
  *(int*)0x6a08a4+=*(int*)0x6a08ac;
  return;
 }
 /* The first-frame staging validator renders the scene twice. */
 if(ray_column==ray_columns){
  ray_column=0;ray_x.error=ray_y.error=0;
  *(int*)0x6a08a0=ray_start_x;*(int*)0x6a08a4=ray_start_y;
 }
 *(int*)0x6a08a0+=ray_step(&ray_x);
 *(int*)0x6a08a4+=ray_step(&ray_y);
 ray_column++;
}
__attribute__((naked)) static void ray_precision_bridge(void){
 __asm__ volatile("pushfl\n pushal\n call _advance_precise_ray\n popal\n popfl\n push $0x6a05b4\n ret\n");
}
static int install_ray_precision(void){
 unsigned char *site=(unsigned char*)0x6a059e;
 const unsigned char expected[]={0xa1,0xa8,0x08,0x6a,0x00,0x01,0x05,0xa0,0x08,0x6a,0x00,
  0xa1,0xac,0x08,0x6a,0x00,0x01,0x05,0xa4,0x08,0x6a,0x00};
 if(memcmp(site,expected,sizeof(expected)))return 0;
 DWORD old;VirtualProtect(site,sizeof(expected),PAGE_EXECUTE_READWRITE,&old);
 site[0]=0xe9;*(int32_t*)(site+1)=(int32_t)((unsigned char*)ray_precision_bridge-(site+5));
 memset(site+5,0x90,sizeof(expected)-5);
 FlushInstructionCache(GetCurrentProcess(),site,sizeof(expected));
 VirtualProtect(site,sizeof(expected),old,&old);
 if(terrain_log){fprintf(terrain_log,"Horizontal ray remainder correction installed (native 4K only).\n");fflush(terrain_log);}
 return 1;
}
#endif
