/**
 @file	get_fileinformation.cpp
 @date	2017-04-06

 @copyright Copyright(C) 2017-2024 Hamamatsu Phtonics K.k.. All rights reserved.

 @brief		Sample code to get file information.
 @details	This program gets file information.
 @remarks	dcimg_init
 @remarks	dcimg_open
 @remarks	dcimg_getparaml
 */

#include "../misc/console_dcimg.h"
#include "../misc/common_dcimg.h"

/**
 @brief Get image information of current handle.
 @param hdcimg		DCIMG handle
 @param width		image width
 @param height		image height
 @param rowbytes	image row bytes
 @param pixeltype	image pixle type
 @return	result to get image information
 */
BOOL get_image_information( HDCIMG hdcimg, int32& width, int32& height, int32& rowbytes, int32& pixeltype )
{
	DCIMG_ERR err;

	int32 nWidth;
	// get width
	err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_IMAGE_WIDTH, &nWidth );
	if( failed(err) )
	{
		dcimgcon_show_dcimgerr( err, "dcimg_getparaml(DCIMG_IDPARAML_IMAGE_WIDTH)" ); 
		return FALSE;
	}

	int32 nHeight;
	// get height
	err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_IMAGE_HEIGHT, &nHeight );
	if( failed(err) )
	{
		dcimgcon_show_dcimgerr( err, "dcimg_getparaml(DCIMG_IDPARAML_IMAGE_HEIGHT)" ); 
		return FALSE;
	}

	int32 nRowbytes;
	// get row bytes
	err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_IMAGE_ROWBYTES, &nRowbytes );
	if( failed(err) )
	{
		dcimgcon_show_dcimgerr( err, "dcimg_getparaml(DCIMG_IDPARAML_IMAGE_ROWBYTES)" ); 
		return FALSE;
	}

	int32 nPixeltype;
	// get pixel type
	err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_IMAGE_PIXELTYPE, &nPixeltype );
	if( failed(err) )
	{
		dcimgcon_show_dcimgerr( err, "dcimg_getparaml(DCIMG_IDPARAML_IMAGE_PIXELTYPE)" ); 
		return FALSE;
	}

	width		= nWidth;
	height		= nHeight;
	rowbytes	= nRowbytes;
	pixeltype	= nPixeltype;

	return TRUE;
}

/**
 @brief Show detailed information.
 @param hdcimg			DCIMG handle
 @return	result to show detailed information
 */
BOOL show_detail_information( HDCIMG hdcimg )
{
	DCIMG_ERR err;

    // show file format version
	int32 version = 0;
	err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_FILEFORMAT_VERSION, &version );
	if( failed(err) )
	{
		dcimgcon_show_dcimgerr( err, "dcimg_getparaml(DCIMG_IDPARAML_FILEFORMAT_VERSION)" );
		return FALSE;
	}

	int32 major = (version & 0xFF000000) >> 24;
	int32 minor = (version & 0x00FF0000) >> 16;
	int32 rev	= (version & 0x0000FFFF);

	printf( "File Format version:\t%d.%d.%d\n", major, minor, rev );

	// get number of frames in current file
	int32 nFrame;
	err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_NUMBEROF_FRAME, &nFrame );
	if( failed(err) )
	{
		dcimgcon_show_dcimgerr( err, "dcimg_getparaml(DCIMG_IDPARAML_NUMBEROF_FRAME)" ); 
		return FALSE;
	}

	// get number of views in current file
	int32 nView;
	err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_NUMBEROF_VIEW, &nView );
	if( failed(err) )
	{
		dcimgcon_show_dcimgerr( err, "dcimg_getparaml(DCIMG_IDPARAML_NUMBEROF_VIEW)" ); 
		return FALSE;
	}

	// get image information
	int32 nWidth, nHeight, nRowbyte, nPixelType;
	if( !get_image_information( hdcimg, nWidth, nHeight, nRowbyte, nPixelType ) )
	{
		return FALSE;
	}

	if( nView > 1 )
		printf( "#%d frames(x%d views): ", nFrame, nView );
	else
		printf( "#%d frames: ", nFrame );

	printf( "%d x %d ", nWidth, nHeight );

	switch( nPixelType )
	{
	case DCIMG_PIXELTYPE_MONO8:		printf( "(MONO8) " );	break;
	case DCIMG_PIXELTYPE_MONO16:	printf( "(MONO16) " );	break;
	default:						printf( "(Unknown Pixel Type=%d) ", nPixelType );	break;
	}

	printf( "rowbytes = %d\n", nRowbyte );

	return TRUE;
}

int main( int argc, char* const argv[] )
{
	printf( "PROGRAM START\n" );

	int	ret = 0;

	// check command line arguments
	if( argc < 2 )
	{
		printf( "Error: an argument is necessary to run this program.\n" );
		printf( "usage: get_fileinformation <source DCIMG File>\n" );
		ret = 3;
	}
	else
	if( _stricmp( argv[1], "-h" ) == 0
	 || _stricmp( argv[1], "-help" ) == 0 )
	{
		printf( "usage: get_fileinformation <source DCIMG File>\n" );
		printf( "This tool will show some information of the target DCIMG file.\n" );
		ret = 2;
	}

	if( ret == 0 )
	{
		const char* filename = argv[1];

		// initialize and open
		HDCIMG hdcimg = dcimgcon_init_open( filename );
		if( hdcimg == NULL )
		{
			ret = 3;
		}
		else
		{
			printf( "Information of DCIMG file %s.\n", filename );

			// show detail information
			if( ! show_detail_information( hdcimg ) )
			{
				ret = 3;
			}
	
			// close DCIMG handle
			dcimg_close( hdcimg );
		}
	}

	printf( "PROGRAM END\n" );
	return ret;	//0:Success, Ohter:Failure
}
