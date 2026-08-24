/**
 @file	get_usermetadata.cpp
 @date	2017-04-06

 @copyright	Copyright (C) 2017-2024 Hamamatsu Photonics K.K.. All rights reserved

 @brief		Sample code to get user mata data.
 @details	This program accesses the user meta data. The target data is changed by the directive "USERMETA_DATATYPE".
 @remarks	dcimg_copymetadata
 */

#include "../misc/console_dcimg.h"
#include "../misc/common_dcimg.h"

/**
 @def	USERMETA_DATATYPE
 *
 *0:	Data type is text data.
 *1:	Data type is binary data.
 */
#define USERMETA_DATATYPE	0

/**
 @brief Write data to specified file.
 @param dstpath	specified file path
 @param src		pointer of data
 @param srcbytes	data size
 @return	result to write data. 0 is success
 */
int save_metadata( const char* dstpath, const void* src, int srcbytes )
{
	FILE*	fp;
	int err = fopen_s( &fp, dstpath, "w" );
	if( err != 0 )
	{
		printf( "Fail to open destination file %s.\n", dstpath );
		return 2;
	}

	fwrite( src, srcbytes, 1, fp );

	fclose( fp );

	return 0;
}

/**
 @brief	Get text meta data specified by argument.
 @details	This function outputs file written text meta data specified location with argument.
 @param hdcimg		DCIMG handle
 @param arg		class to manage arguments
 @return	result to get meta text. 0 is success
 @sa	dcimg_getparaml, dcimg_setsessionindex, dcimg_copymetadata
 */
int do_dcimg_metatext( HDCIMG hdcimg, const cmdline& arg )
{
	DCIMG_ERR	err;

	int32 iSession;
	if( arg.m_iSession == NOTSET_SESSIONINDEX )
		iSession = 0;	// firest session
	else
	{
		// get number of sessions
		int32 nSession;
		err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_NUMBEROF_SESSION, &nSession );
		if( failed(err) )
		{
			dcimgcon_show_dcimgerr( err, "dcimg_getparaml(DCIMG_IDPARAML_NUMBEROF_SESSION)" );
			return 3;
		}

		if( arg.m_iSession >= nSession )
		{
			printf( "Number of sessions in the specified file is %d.\n", nSession );
			printf( "But session index specified in the argument was %d do it was out of range.\n", arg.m_iSession );
			return 2;
		}

		// change current session;
		err = dcimg_setsessionindex( hdcimg, arg.m_iSession );
		if( failed(err) )
		{
			dcimgcon_show_dcimgerr( err, "dcimg_setsessionindex()", "index=%d", arg.m_iSession );
			return 3;
		}

		iSession = arg.m_iSession;
	}

	// make destination path
	char dstpath[ MAX_PATH ];
	strcpy_s( dstpath, sizeof(dstpath), arg.m_path );

	char* pDstPathLast = get_extension( dstpath );
	int	restof_dst = (int)(sizeof(dstpath) - (pDstPathLast - dstpath));

	// parameter for getting text meta data
	DCIMG_USERDATATEXT	imgusrtxt;
	memset( &imgusrtxt, 0, sizeof(imgusrtxt) );
	imgusrtxt.hdr.size	= sizeof(imgusrtxt);
	imgusrtxt.hdr.iKind	= DCIMG_METADATAKIND_USERDATATEXT;

	int32 databytes;

	if( arg.m_iSession == NOTSET_SESSIONINDEX && arg.m_iFrame == NOTSET_FRAMEINDEX )
	{
		// file meta data
		err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_SIZEOF_USERDATATEXT_FILE, &databytes );
		if( failed(err) )
		{
			dcimgcon_show_dcimgerr( err, "dcimg_getparaml(DCIMG_IDPARAML_SIZEOF_USERDATATEXT_FILE)" );
			return 3;
		}
		if( databytes == 0 )
		{
			printf( "SIZEOF_USERDATATEXT_FILE is %d. This means no text file meta data.\n", databytes );
			return 3;
		}

		// setup for file text meta data.
		imgusrtxt.hdr.option	= DCIMG_USERDATAKIND_FILE;
		sprintf_s( pDstPathLast, restof_dst, ".txt" );
	}
	else
	if( arg.m_iSession != NOTSET_SESSIONINDEX && arg.m_iFrame == NOTSET_FRAMEINDEX )
	{
		// session meta data
		err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_SIZEOF_USERDATATEXT_SESSION, &databytes );
		if( failed(err) )
		{
			dcimgcon_show_dcimgerr( err, "dcimg_getparaml(DCIMG_IDPARAML_SIZEOF_USERDATATEXT_SESSION)" );
			return 3;
		}
		if( databytes == 0 )
		{
			printf( "SIZEOF_USERDATATEXT_SESSION is %d. This means no text session meta data.\n", databytes );
			return 3;
		}

		// setup for session text meta data
		imgusrtxt.hdr.option	= DCIMG_USERDATAKIND_SESSION;
		sprintf_s( pDstPathLast, restof_dst, "%d.txt", iSession );
	}
	else
	{
		// frame meta data
		err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_MAXSIZE_USERDATATEXT, &databytes );
		if( failed(err) )
		{
			dcimgcon_show_dcimgerr( err, "dcimg_getparaml(DCIMG_IDPARAML_MAXSIZE_USERDATATEXT)" );
			return 3;
		}
		if( databytes == 0 )
		{
			printf( "MAXSIZE_USERDATATEXT is %d. This means no text frame meta data for specified session.\n", databytes );
			return 3;
		}

		// get number of frames
		int32 nFrame;
		err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_NUMBEROF_FRAME, &nFrame );
		if( failed(err) )
		{
			dcimgcon_show_dcimgerr( err, "dcimg_getparaml(DCIMG_IDPARAML_NUMBEROF_FRAME)" );
			return 3;
		}

		if( arg.m_iFrame >= nFrame )
		{
			printf( "Number of frames in the specified session is %d.\n", nFrame );
			printf( "But frame index specified in the argument was %d so it was out of range.\n", arg.m_iFrame );
			return 2;
		}

		// setup for frame text meta data
		imgusrtxt.hdr.option = DCIMG_USERDATAKIND_FRAME;
		imgusrtxt.hdr.iFrame	= arg.m_iFrame;
		sprintf_s( pDstPathLast, restof_dst, "%d-%d.txt", iSession, arg.m_iFrame );
	}

	// access to user text meta data
	imgusrtxt.text	= new char[ databytes ];
	if( imgusrtxt.text == NULL )
	{
		printf( "Error: fail to allocate %d bytes.\n", databytes );
		return 3;
	}

	int ret = 0;

	imgusrtxt.text_len = databytes;
	err = dcimg_copymetadata( hdcimg, &imgusrtxt.hdr );
	if( failed(err) )
	{
		dcimgcon_show_dcimgerr( err, "dcimg_copymetadata()", "iKind=0x%08x, option=0x%08x", imgusrtxt.hdr.iKind, imgusrtxt.hdr.option );
		return 3;
	}
	else
	{
		if( imgusrtxt.text_len == 0 )
		{
			if( imgusrtxt.hdr.option == DCIMG_USERDATAKIND_FRAME )
			{
				printf( "DCIMG_USERDATATEXT.text_len is %d. This means no text meta data for specified frame.\n", imgusrtxt.text_len );
			}
			else
			{
				printf( "unreach error\n" );
			}

			ret = 3;
		}
		else
		{
			ret = save_metadata( dstpath, imgusrtxt.text, imgusrtxt.text_len );
			printf( "Code page is %d. Data size is %d bytes.\n", imgusrtxt.codepage, imgusrtxt.text_len );
		}
	}

	delete imgusrtxt.text;

	return ret;
}

/**
 @brief	Get binary meta data specified by argument
 @details	This function outputs file written binary meta data specified location with argument
 @param hdcimg		DCIMG handle
 @param arg		class to manage arguments
 @return	result to get binary text. 0 is success
 @sa	dcimg_getparaml, dcimg_setsessionindex, dcimg_copymetadata
 */
int do_dcimg_metabinary( HDCIMG hdcimg, const cmdline& arg )
{
	DCIMG_ERR	err;

	int32 iSession;
	if( arg.m_iSession == NOTSET_SESSIONINDEX )
		iSession = 0;	// firest session
	else
	{
		// get number of sessions
		int32 nSession;
		err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_NUMBEROF_SESSION, &nSession );
		if( failed(err) )
		{
			dcimgcon_show_dcimgerr( err, "dcimg_getparaml(DCIMG_IDPARAML_NUMBEROF_SESSION)" );
			return 3;
		}

		if( arg.m_iSession >= nSession )
		{
			printf( "Number of sessions in the specified file is %d.\n", nSession );
			printf( "But session index specified in the argument was %d do it was out of range.\n", arg.m_iSession );
			return 2;
		}

		// change current session;
		err = dcimg_setsessionindex( hdcimg, arg.m_iSession );
		if( failed(err) )
		{
			dcimgcon_show_dcimgerr( err, "dcimg_setsessionindex()", "index=%d", arg.m_iSession );
			return 3;
		}

		iSession = arg.m_iSession;
	}

	// make destination path
	char dstpath[ MAX_PATH ];
	strcpy_s( dstpath, sizeof(dstpath), arg.m_path );

	char* pDstPathLast = get_extension( dstpath );
	int	restof_dst = (int)(sizeof(dstpath) - (pDstPathLast - dstpath));

	// parameter for getting binary meta data
	DCIMG_USERDATABIN	imgusrbin;
	memset( &imgusrbin, 0, sizeof(imgusrbin) );
	imgusrbin.hdr.size	= sizeof(imgusrbin);
	imgusrbin.hdr.iKind	= DCIMG_METADATAKIND_USERDATABIN;

	int32 databytes;

	if( arg.m_iSession == NOTSET_SESSIONINDEX && arg.m_iFrame == NOTSET_FRAMEINDEX )
	{
		// file meta data
		err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_SIZEOF_USERDATABIN_FILE, &databytes );
		if( failed(err) )
		{
			dcimgcon_show_dcimgerr( err, "dcimg_getparaml(DCIMG_IDPARAML_SIZEOF_USERDATABIN_FILE)" );
			return 3;
		}
		if( databytes == 0 )
		{
			printf( "SIZEOF_USERDATABIN_FILE is %d. This means no binary file meta data.\n", databytes );
			return 3;
		}

		// setup for file binary meta data.
		imgusrbin.hdr.option	= DCIMG_USERDATAKIND_FILE;
		sprintf_s( pDstPathLast, restof_dst, ".bin" );
	}
	else
	if( arg.m_iSession != NOTSET_SESSIONINDEX && arg.m_iFrame == NOTSET_FRAMEINDEX )
	{
		// session meta data
		err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_SIZEOF_USERDATABIN_SESSION, &databytes );
		if( failed(err) )
		{
			dcimgcon_show_dcimgerr( err, "dcimg_getparaml(DCIMG_IDPARAML_SIZEOF_USERDATABIN_SESSION)" );
			return 3;
		}
		if( databytes == 0 )
		{
			printf( "SIZEOF_USERDATABIN_SESSION is %d. This means no binary session meta data.\n", databytes );
			return 3;
		}

		// setup for session binary meta data
		imgusrbin.hdr.option	= DCIMG_USERDATAKIND_SESSION;
		sprintf_s( pDstPathLast, restof_dst, "%d.bin", iSession );
	}
	else
	{
		// frame meta data
		err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_MAXSIZE_USERDATABIN, &databytes );
		if( failed(err) )
		{
			dcimgcon_show_dcimgerr( err, "dcimg_getparaml(DCIMG_IDPARAML_MAXSIZE_USERDATABIN)" );
			return 3;
		}
		if( databytes == 0 )
		{
			printf( "MAXSIZE_USERDATABIN is %d. This means no binary frame meta data for specified session.\n", databytes );
			return 3;
		}

		// get number of frames
		int32 nFrame;
		err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_NUMBEROF_FRAME, &nFrame );
		if( failed(err) )
		{
			dcimgcon_show_dcimgerr( err, "dcimg_getparaml(DCIMG_IDPARAML_NUMBEROF_FRAME)" );
			return 3;
		}

		if( arg.m_iFrame >= nFrame )
		{
			printf( "Number of frames in the specified session is %d.\n", nFrame );
			printf( "But frame index specified in the argument was %d so it was out of range.\n", arg.m_iFrame );
			return 2;
		}

		// setup for frame binary meta data
		imgusrbin.hdr.option = DCIMG_USERDATAKIND_FRAME;
		imgusrbin.hdr.iFrame	= arg.m_iFrame;
		sprintf_s( pDstPathLast, restof_dst, "%d-%d.bin", iSession, arg.m_iFrame );
	}

	// access to user binary meta data
	imgusrbin.bin	= new char[ databytes ];
	if( imgusrbin.bin == NULL )
	{
		printf( "Error: fail to allocate %d bytes.\n", databytes );
		return 3;
	}

	int ret = 0;

	imgusrbin.bin_len = databytes;
	err = dcimg_copymetadata( hdcimg, &imgusrbin.hdr );
	if( failed(err) )
	{
		dcimgcon_show_dcimgerr( err, "dcimg_copymetadata()", "iKind=0x%08x, option=0x%08x", imgusrbin.hdr.iKind, imgusrbin.hdr.option );
		return 3;
	}
	else
	{
		if( imgusrbin.bin_len == 0 )
		{
			if( imgusrbin.hdr.option == DCIMG_USERDATAKIND_FRAME )
			{
				printf( "DCIMG_USERDATATEXT.text_len is %d. This means no text meta data for specified frame.\n", imgusrbin.bin_len );
			}
			else
			{
				printf( "unreach error\n" );
			}

			ret = 3;
		}
		else
		{
			ret = save_metadata( dstpath, imgusrbin.bin, imgusrbin.bin_len );
			printf( "Data size is %d bytes.\n", imgusrbin.bin_len );
		}
	}

	delete imgusrbin.bin;

	return ret;
}

int main( int argc, char* argv[] )
{
	printf( "PROGRAM START\n" );

	int	ret = 0;

	cmdline arg;
	// set argument type
	arg.set_argment_flag( ARGFLAG_ENABLE | ARGFLAG_ABBR, ARGFLAG_ENABLE | ARGFLAG_ABBR );

	// set string of target data kind
	arg.set_targetkind( "user meta data" );

	// check command line arguments
	ret = arg.set_arg( argc, argv );
	if( ret == 0 )
	{
		// initialize and open
		HDCIMG hdcimg = dcimgcon_init_open( arg.m_path );
		if( hdcimg == NULL )
		{
			ret = 3;
		}
		else
		{
			// access user meta data
#if USERMETA_DATATYPE == 0
			// text data
			ret = do_dcimg_metatext( hdcimg, arg );
#elif USERMETA_DATATYPE == 1
			// binary data
			ret = do_dcimg_metabinary( hdcimg, arg );
#else
			printf( "directive error!\n" );
			ret = 2;
#endif
			// close DCIMG handle
			dcimg_close( hdcimg );
		}
	}

	printf( "PROGRAM END\n" );
	return ret;	//0:Success, Ohter:Failure
}
