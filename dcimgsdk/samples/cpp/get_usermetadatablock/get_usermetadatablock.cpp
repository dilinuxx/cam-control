/**
 @file	get_usermetadatablock
 @date	2017-04-06

 @copyright	Copyright (C) 2017-2024 Hamamatsu Photonics K.K.. All rights reserved.

 @brief		Sample code to get user meta data block.
 @details	This program accesses the user meta data of FRAME by block. The target data is changed by the directive "USERMETA_DATATYPE".
 @remarks	dcimg_copymetadatablock
 */

#include "../misc/console_dcimg.h"
#include "../misc/common_dcimg.h"

/**
 @def	USERMETA_DATATYPE
 *
 *0:	Data type is text data
 *1:	Data type is binary data
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
 @brief	Get text meta data of all frames in the specified session.
 @details	This function outputs files written text meta data of frame in the specified session with argument.
 @param hdcimg	DCIMG handle
 @param arg	class to manage arguments
 @return	result to get the meta text of frame. 0 is success
 @sa	dcimg_getparaml, dcimg_setsessionindex, dcimg_copymetadatablock
 */
int do_dcimg_metadatablock_text( HDCIMG hdcimg, const cmdline& arg )
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
	DCIMG_USERDATATEXTBLOCK	imgutb;
	memset( &imgutb, 0, sizeof(imgutb) );
	imgutb.hdr.size	= sizeof(imgutb);
	imgutb.hdr.iKind	= DCIMG_METADATAKIND_USERDATATEXT;

	// frame text meta data
	int32 databytes;
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

	int	ret = 0;

	char* userdatatext = new char[ databytes * nFrame ];
	imgutb.userdatatextvalidsize = new int32[ nFrame ];

	if( userdatatext == NULL || imgutb.userdatatextvalidsize == NULL )
	{
		printf( "Error: fail to allocate memory.\n" );
		ret = 2;
	}
	else
	{
		memset( userdatatext, 0, databytes * nFrame );
		memset( imgutb.userdatatextvalidsize, 0, sizeof(*imgutb.userdatatextvalidsize) * nFrame );

		imgutb.userdatatext		= userdatatext;
		imgutb.userdatatextsize	= databytes;
		imgutb.userdatatextmax	= nFrame;

		imgutb.userdatatext_kind	= DCIMG_USERDATAKIND_FRAME;

		err = dcimg_copymetadatablock( hdcimg, &imgutb.hdr );
		if( failed(err) )
		{
			dcimgcon_show_dcimgerr( err, "dcimg_copymetadatablock(DCIMG_METADATAKIND_USERDATATEXT)" );
			ret = 3;
		}
		else
		{
			int32 iFrame;
			for( iFrame = 0; iFrame < imgutb.userdatatextcount; iFrame++ )
			{
				// store each user text meta data
				if( imgutb.userdatatextvalidsize[iFrame] == 0 )
				{
					printf( "Frame%d @ Sesison%d doesn't have text meta data.\n", iFrame, iSession );
				}
				else
				{
					// setup for frame text meta data
					sprintf_s( pDstPathLast, restof_dst, "%d-%d.txt", iSession, iFrame );

					char*	src = userdatatext + databytes * iFrame;
					save_metadata( dstpath, src, imgutb.userdatatextvalidsize[iFrame] );
				}
			}
		}
	}

	if( userdatatext != NULL )					delete userdatatext;
	if( imgutb.userdatatextvalidsize != NULL )	delete imgutb.userdatatextvalidsize;

	return ret;
}

/**
 @brief	Get binary meta data of all frames in the specified session.
 @details	This function outputs files written binary meta data of frame in the specified session with argument.
 @param hdcimg	DCIMG handle
 @param arg	class to manage arguments
 @return	result to get the meta binary of frame. 0 is success
 @sa	dcimg_getparaml, dcimg_setsessionindex, dcimg_copymetadatablock
 */
int do_dcimg_metadatablock_binary( HDCIMG hdcimg, const cmdline& arg )
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
	DCIMG_USERDATABINBLOCK	imgubb;
	memset( &imgubb, 0, sizeof(imgubb) );
	imgubb.hdr.size	= sizeof(imgubb);
	imgubb.hdr.iKind	= DCIMG_METADATAKIND_USERDATABIN;

	// frame binary meta data
	int32 databytes;
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

	int	ret = 0;

	char* userdatabin = new char[ databytes * nFrame ];
	imgubb.userdatabinvalidsize	= new int32[ nFrame ];

	if( userdatabin == NULL || imgubb.userdatabinvalidsize == NULL )
	{
		printf( "Error: fail to allocate memory.\n" );
		ret = 2;
	}
	else
	{
		memset( userdatabin, 0, databytes * nFrame );
		memset( imgubb.userdatabinvalidsize, 0, sizeof(*imgubb.userdatabinvalidsize) * nFrame );

		imgubb.userdatabin		= userdatabin;
		imgubb.userdatabinsize	= databytes;
		imgubb.userdatabinmax		= nFrame;
		
		imgubb.userdatabin_kind	= DCIMG_USERDATAKIND_FRAME;

		err = dcimg_copymetadatablock( hdcimg, &imgubb.hdr );
		if( failed(err) )
		{
			dcimgcon_show_dcimgerr( err, "dcimg_copymetadatablock(DCIMG_METADATAKIND_USERDATABIN)" );
			ret = 3;
		}
		else
		{
			int32 iFrame;
			for( iFrame = 0; iFrame < imgubb.userdatabincount; iFrame++ )
			{
				// store each user binary meta data
				if( imgubb.userdatabinvalidsize[iFrame] == 0 )
				{
					printf( "Frame%d @ Sesison%d doesn't have binary meta data.\n", iFrame, iSession );
				}
				else
				{
					// setup for frame text meta data
					sprintf_s( pDstPathLast, restof_dst, "%d-%d.bin", iSession, iFrame );

					char*	src = userdatabin + databytes * iFrame;
					save_metadata( dstpath, src, imgubb.userdatabinvalidsize[iFrame] );
				}
			}
		}
	}

	if( userdatabin != NULL	)		delete userdatabin;
	if( imgubb.userdatabinvalidsize )	delete imgubb.userdatabinvalidsize;

	return ret;
}

int main( int argc, char* argv[] )
{
	printf( "PROGRAM START\n" );

	int	ret = 0;

	cmdline arg;
	// set argument type
	arg.set_argment_flag( ARGFLAG_NONE, ARGFLAG_ENABLE | ARGFLAG_ABBR );

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
			// access user meta data of FRAME
#if USERMETA_DATATYPE == 0
			// text data
			ret = do_dcimg_metadatablock_text( hdcimg, arg );
#elif USERMETA_DATATYPE == 1
			ret = do_dcimg_metadatablock_binary( hdcimg, arg );
#else
			printf( "directive error!\n" );
			ret = 2;
#endif
		}

		// close DCIMG handle
		dcimg_close( hdcimg );
	}

	printf( "PROGRAM END\n" );
	return ret;	//0:Success, Ohter:Failure
}
