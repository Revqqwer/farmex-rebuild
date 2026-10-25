/* Owned ASCII INI fixture only. No command line input, process handles or game. */
#include <windows.h>
#include <stdio.h>
#include <string.h>

struct Numeric { const char *name,*key; unsigned int fallback,expected; int boolean; };
static const struct Numeric numeric[]={
 {"bool_zero","zero",0,0,1},{"bool_two","two",0,2,1},
 {"bool_256","big",0,256,1},{"bool_negative","negative",0,0xffffffffu,1},
 {"bool_missing_256","absent",256,0,1},{"bool_missing_257","absent",257,1,1},
 {"dword_missing_256","absent",256,256,0},
 {"dword_negative","negative",0,0xffffffffu,0},
 {"dword_hex","hex",0,42,0},{"dword_case_insensitive","TWO",0,2,0}
};
struct StringCase { const char *name,*key,*fallback,*expected; unsigned int length; };
static const struct StringCase strings[]={
 {"string_plain","plain","","alpha",5},
 {"string_quotes","quoted","","alpha beta",10},
 {"string_missing","absent","fallback","fallback",8},
 {"string_blank","blank","fallback","",0},
 {"string_limit","long","",NULL,254}
};

int main(int argc,char **argv) {
 char directory[MAX_PATH],path[MAX_PATH],text[1024],buffer[255],*basename;
 HANDLE file;DWORD written;unsigned int i,j,api,value,expected,passed=0;int length;
 (void)argv;
 if(argc!=1)return 10;
 if(!GetCurrentDirectoryA(sizeof(directory),directory))return 11;
 if(!GetTempFileNameA(directory,"rea",0,path))return 12;
 file=CreateFileA(path,GENERIC_WRITE,0,NULL,TRUNCATE_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
 if(file==INVALID_HANDLE_VALUE)return 13;
 strcpy(text,"[OWNED]\r\nzero=0\r\ntwo=2\r\nbig=256\r\nnegative=-1\r\nhex=0x2a\r\nplain=alpha\r\nquoted=\"alpha beta\"\r\nblank=\r\nlong=");
 length=(int)strlen(text);for(j=0;j<300;j++)text[length++]='A';text[length++]='\r';text[length++]='\n';text[length]=0;
 if(!WriteFile(file,text,length,&written,NULL)||written!=(DWORD)length){CloseHandle(file);return 14;}
 CloseHandle(file);
 basename=strrchr(path,'\\');basename=basename?basename+1:path;
 printf("{\"kind\":\"fixture\",\"basename\":\"%s\",\"bytes\":%u,\"ascii_only\":true}\n",basename,(unsigned int)written);
 for(i=0;i<sizeof(numeric)/sizeof(numeric[0]);i++) {
  const struct Numeric *c=&numeric[i];
  /* 0045f508 zero-extends the default BYTE before the API;0045f5f4 keeps DWORD. */
  unsigned int def=c->boolean?(unsigned char)c->fallback:c->fallback;
  api=GetPrivateProfileIntA("OWNED",c->key,def,path);
  value=c->boolean?(api!=0):api;expected=c->boolean?(c->expected!=0):c->expected;
  if(api!=c->expected||value!=expected)return 20+(int)i;
  printf("{\"kind\":\"numeric\",\"case\":\"%s\",\"boolean\":%s,\"default_raw\":%u,\"default_api\":%u,\"api_eax\":%u,\"wrapper_result\":%u,\"passed\":true}\n",
   c->name,c->boolean?"true":"false",c->fallback,def,api,value);passed++;
 }
 for(i=0;i<sizeof(strings)/sizeof(strings[0]);i++) {
  const struct StringCase *c=&strings[i];
  memset(buffer,0xcc,sizeof(buffer));
  api=GetPrivateProfileStringA("OWNED",c->key,c->fallback,buffer,sizeof(buffer),path);
  if(api!=c->length||strlen(buffer)!=c->length||buffer[c->length]!=0)return 40+(int)i;
  if(c->expected){if(strcmp(buffer,c->expected))return 50+(int)i;}
  else for(j=0;j<c->length;j++)if(buffer[j]!='A')return 60;
  printf("{\"kind\":\"string\",\"case\":\"%s\",\"capacity\":255,\"api_count\":%u,\"nul_terminated\":true,\"passed\":true}\n",c->name,api);passed++;
 }
 printf("{\"kind\":\"summary\",\"passed\":%u,\"game_process_access\":false,\"managed_rtl_executed\":false}\n",passed);
 return passed==15?0:70;
}
