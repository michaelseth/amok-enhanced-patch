#include <windows.h>
#include <xinput.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef DWORD (WINAPI *ReadPad)(DWORD,XINPUT_STATE*);
static ReadPad read_pad;
static unsigned char held[256];
static int initialized;
static FILE *log_file;

/* Translate the stock game bindings; no input is sent to other applications. */
typedef struct { int running, click_down; } PadMode;
static PadMode mode;
void map_pad(const XINPUT_GAMEPAD *p,unsigned char keys[256],int playing,PadMode *m) {
 memset(keys,0,256);
 const WORD b=p->wButtons;
 keys[VK_UP]=(p->sThumbLY>9000)||(b&XINPUT_GAMEPAD_DPAD_UP);
 keys[VK_DOWN]=(p->sThumbLY<-9000)||(b&XINPUT_GAMEPAD_DPAD_DOWN);
 keys[VK_LEFT]=(!playing&&p->sThumbLX<-9000)||(p->sThumbRX<-9000)||(b&XINPUT_GAMEPAD_DPAD_LEFT);
 keys[VK_RIGHT]=(!playing&&p->sThumbLX>9000)||(p->sThumbRX>9000)||(b&XINPUT_GAMEPAD_DPAD_RIGHT);
 keys['Z']=playing&&p->sThumbLX<-9000;
 keys['X']=playing&&p->sThumbLX>9000;
 keys[VK_CONTROL]=(p->bRightTrigger>30)||(b&XINPUT_GAMEPAD_RIGHT_SHOULDER);
 keys[VK_SPACE]=(p->bLeftTrigger>30)||(b&XINPUT_GAMEPAD_X);
 keys[VK_BACK]=(b&XINPUT_GAMEPAD_Y)!=0;
 keys[VK_RETURN]=(b&XINPUT_GAMEPAD_A)!=0;
 keys[VK_ESCAPE]=(b&(XINPUT_GAMEPAD_START|XINPUT_GAMEPAD_B))!=0;
 keys[VK_TAB]=(b&XINPUT_GAMEPAD_BACK)!=0;
 int click=(b&XINPUT_GAMEPAD_LEFT_THUMB)!=0;
 if(playing&&click&&!m->click_down)m->running=!m->running;
 if(!playing)m->running=0;
 m->click_down=click;
 int moving=keys[VK_UP]||keys[VK_DOWN]||keys['Z']||keys['X']||keys[VK_LEFT]||keys[VK_RIGHT];
 keys[VK_SHIFT]=playing&&((b&XINPUT_GAMEPAD_START)||(m->running&&moving&&!(b&XINPUT_GAMEPAD_B)));
 keys[VK_F1]=(b&XINPUT_GAMEPAD_RIGHT_THUMB)!=0;
 keys[VK_MENU]=(b&XINPUT_GAMEPAD_LEFT_SHOULDER)!=0;
}

static void poll_pad(void) {
 if(!initialized) {
  initialized=1;
  HMODULE module=LoadLibraryExA("xinput1_4.dll",NULL,LOAD_LIBRARY_SEARCH_SYSTEM32);
  if(!module)module=LoadLibraryExA("xinput9_1_0.dll",NULL,LOAD_LIBRARY_SEARCH_SYSTEM32);
  if(module)read_pad=(ReadPad)GetProcAddress(module,"XInputGetState");
  log_file=fopen("controller-status.txt","w");
  if(log_file){fprintf(log_file,"XInput module: %s\n",read_pad?"loaded":"unavailable");fflush(log_file);}
 }
 unsigned char next[256]={0}; XINPUT_STATE state; int connected=-1;
 if(read_pad)for(DWORD i=0;i<4;i++)if(read_pad(i,&state)==ERROR_SUCCESS){connected=(int)i;break;}
 static int previous=-2;
 if(previous!=connected && log_file){fprintf(log_file,"Controller slot: %d (-1 means disconnected)\n",connected);fflush(log_file);previous=connected;}
 HWND game=*(HWND*)0x683630;
 if(connected>=0 && game && GetForegroundWindow()==game)
  map_pad(&state.Gamepad,next,*(volatile int*)0x490054==1,&mode);
 else mode=(PadMode){0};
 unsigned char *game_keys=*(unsigned char**)0x683640;
 if(!game_keys)return;
 for(unsigned i=0;i<256;i++){
  if(next[i]&&!held[i] && !game_keys[i])game_keys[i]=255;
  if(!next[i]&&held[i] && !(GetAsyncKeyState(i)&0x8000))game_keys[i]=0;
 }
 memcpy(held,next,256);
}
static DWORD WINAPI controller_thread(LPVOID unused) {
 (void)unused;
 for(;;){poll_pad();Sleep(8);}
 return 0;
}
#ifdef AMOK_MOD
#ifdef AMOK_FAR_TERRAIN
#include "amok_far_terrain.c"
#endif
BOOL WINAPI DllMain(HINSTANCE instance,DWORD reason,LPVOID reserved) {
 (void)reserved;
 if(reason==DLL_PROCESS_ATTACH){
  DisableThreadLibraryCalls(instance);
#ifdef AMOK_FAR_TERRAIN
  if(!install_far_terrain())return FALSE;
#endif
  HANDLE thread=CreateThread(NULL,0,controller_thread,NULL,0,NULL);
  if(thread)CloseHandle(thread);
 }
 return TRUE;
}
#else
#include <assert.h>
int main(void) {
 unsigned char keys[256];XINPUT_GAMEPAD p={0};
 PadMode m={0};
 map_pad(&p,keys,1,&m);for(int i=0;i<256;i++)assert(keys[i]==0);
 p.sThumbLY=8999;map_pad(&p,keys,1,&m);assert(!keys[VK_UP]);
 p.sThumbLY=10000;p.sThumbRX=-15000;p.bRightTrigger=31;
 p.wButtons=XINPUT_GAMEPAD_A|XINPUT_GAMEPAD_LEFT_THUMB;
 p.sThumbLX=15000;
 map_pad(&p,keys,1,&m);assert(keys['X']&&keys[VK_UP]&&keys[VK_LEFT]&&keys[VK_CONTROL]&&keys[VK_RETURN]&&keys[VK_SHIFT]);assert(!keys[VK_RIGHT]&&!keys[VK_MENU]);
 map_pad(&p,keys,1,&m);assert(m.running); /* Holding click does not toggle repeatedly. */
 p.wButtons=0;map_pad(&p,keys,1,&m);assert(keys[VK_SHIFT]);
 p.wButtons=XINPUT_GAMEPAD_LEFT_THUMB;map_pad(&p,keys,1,&m);assert(!keys[VK_SHIFT]&&!m.running);
 p.wButtons=0;map_pad(&p,keys,0,&m);assert(keys[VK_RIGHT]&&!keys['X']);
 p=(XINPUT_GAMEPAD){0};p.wButtons=XINPUT_GAMEPAD_START|XINPUT_GAMEPAD_BACK|XINPUT_GAMEPAD_LEFT_SHOULDER|XINPUT_GAMEPAD_Y;
 map_pad(&p,keys,1,&m);assert(keys[VK_ESCAPE]&&keys[VK_SHIFT]&&keys[VK_TAB]&&keys[VK_MENU]&&keys[VK_BACK]);assert(!keys[VK_UP]&&!keys[VK_CONTROL]);
 p.wButtons=XINPUT_GAMEPAD_B|XINPUT_GAMEPAD_RIGHT_THUMB;p.sThumbLY=15000;m.running=1;
 map_pad(&p,keys,1,&m);assert(keys[VK_ESCAPE]&&!keys[VK_SHIFT]&&keys[VK_F1]);
 map_pad(&p,keys,0,&m);assert(!m.running&&!keys[VK_SHIFT]);
 puts("Controller mapping tests passed.");return 0;
}
#endif
