// console4.h

// ----------------------------------------------------------------

#ifdef _WIN32

// Windows

#include	<windows.h>

#else // ! _WIN32

#include    <string.h>
#include    <stdint.h>
#include    <ctype.h>

#if defined( LINUX )

// Linux

#include	<stdlib.h>
#include	<pthread.h>

#elif defined( MACOSX ) || __ppc64__ || __i386__ || __x86_64__

// Mac

// No carbon

#include    <time.h>

#endif
#endif // ! _WIN32

// common headers

#include	<stdio.h>

// DCIMG-API headers

#if	defined( LINUX )
#include			"dcimgapi.h"
#else
#include			"../../../inc/dcimgapi.h"
#endif

#if defined( _WIN64 )
#pragma comment(lib,"../../../lib/win64/dcimgapi.lib")
#elif defined(_WIN32)
#pragma comment(lib,"../../../lib/win32/dcimgapi.lib")
#endif

// ----------------------------------------------------------------

// define common macro

#ifndef ASSERT
#define	ASSERT(c)
#endif

// absorb different function

#ifdef _WIN32

#if defined(UNICODE) || defined(_UNICODE)
#define	_T(str)	L##str
#else
#define	_T(str)	str
#endif

#elif defined( MACOSX ) || __ppc64__ || __i386__ || __x86_64__ || defined( LINUX )

#define	_T(str)	str

#endif

// absorb Visual Studio 2005 and later

#if ! defined(_WIN32) || _MSC_VER < 1400

#define	sprintf_s							snprintf
#define	_stricmp(str1, str2)				strncasecmp( str1, str2, strlen(str2) )

#define	BOOL			int
#define	BYTE			uint8_t
#define	WORD			uint16_t
#define	DWORD			uint32_t
#define	LONGLONG		int64_t

#define	MAX_PATH		256
#define	TRUE			1
#define	FALSE			0

inline int fopen_s( FILE** fpp, const char* filename, const char* filemode )
{
	*fpp = fopen( filename, filemode );
	if( fpp == NULL )
		return 1;
	else
		return 0;
}

inline void Sleep( DWORD dwMillseconds )
{
#if defined( MACOSX )
    int usec = dwMillseconds * 1000;
    usleep(usec);
#else // expect defined( LINUX )
	struct timespec t;
	t.tv_sec = dwMillseconds / 1000;
	t.tv_nsec = ( dwMillseconds % 1000 ) * 1000000;
	nanosleep( &t, NULL );
#endif
}

inline void* memcpy_s( void* dst, size_t dstsize, const void* src, size_t srclen )
{
	if( dstsize < srclen )
		memcpy( dst, src, dstsize );
	else
		memcpy( dst, src, srclen );
}

inline char* strcpy_s( char* dst, size_t dstsize, const char* src )
{
	return (char*)memcpy_s( dst, dstsize, src, strlen(src) );
}

#endif

// ----------------------------------------------------------------
