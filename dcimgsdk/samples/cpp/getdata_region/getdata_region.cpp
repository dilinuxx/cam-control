/**
 @file	getdata_region
 @date	2017-04-06

 @copyright	Copyright (C) 2017-2024 Hamamatsu Photonics K.K.. All rights reserved.

 @brief		Sample code to get the region for data reduction.
 @details	This program gets the region information when the recorded data is extraction data.
 @remarks	dcimg_getdata
 */

#include "../misc/console_dcimg.h"
#include "../misc/common_dcimg.h"

/**
 @brief	Get and show region data.
 @details	This function gets the region data of the specified session and displays the rectangle region.
 @param hdcimg		DCIMG handle
 @param arg		class to manage arguments
 @return	result to get region data. 0 is success
 @sa	dcimg_getparaml, dcimg_setsessionindex, dcimg_getdata
 */
int do_dcimg_getdata_region( HDCIMG hdcimg, const cmdline& arg )
{
	DCIMG_ERR	err;

	int32	iSession;
	if( arg.m_iSession == NOTSET_SESSIONINDEX )
	{
		iSession = 0;	// first session
	}
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

	int32 nView = 0;
	err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_NUMBEROF_VIEW, &nView );
	if( failed(err) )
		nView = 1;

	int	ret = 0;

	// get data of region
	DCIMGDATA_REGION	imgdataregion;
	memset( &imgdataregion, 0, sizeof(imgdataregion) );
	imgdataregion.hdr.size	= sizeof(imgdataregion);
	imgdataregion.hdr.iKind	= DCIMGDATA_KIND__REGION;

	int32 iView;
	for( iView=1; iView<=nView; iView++ )
	{
		imgdataregion.hdr.option	= DCIMGDATA_OPTION__VIEW_1 + (iView-1) * DCIMGDATA_OPTION__VIEW__STEP;

		err = dcimg_getdata( hdcimg, &imgdataregion.hdr );
		if( failed(err) )
		{
			dcimgcon_show_dcimgerr( err, "dcimg_getdata(DCIMGDATA_KIND__REGION)", "View%d", iView );
			ret = 3;
		}
		else
		{
			printf( "View%d:\n", iView );

			if( imgdataregion.type == DCIMGDATA_REGIONTYPE__RECT16ARRAY )
			{
				int32 nCount = imgdataregion.datasize / sizeof(DCIMGDATA_REGIONRECT);
				DCIMGDATA_REGIONRECT* p = (DCIMGDATA_REGIONRECT*)imgdataregion.data;

				int32 i;
				for( i = 0; i < nCount; i++ )
				{
					printf( "region[%d] (%d,%d) - (%d,%d)\n", i, p[i].left, p[i].top, p[i].right, p[i].bottom );
				}
			}
			else
			{
				printf( "dcimg_getdata(DCIMGDATA_KIND__REGION) return unknown data type.\n" );
				ret = 3;
			}
		}
	}

	return ret;
}

int main( int argc, char* argv[] )
{
	printf( "PROGRAM START\n" );

	int	ret = 0;

	cmdline	arg;
	// set argument type
	arg.set_argment_flag( ARGFLAG_NONE, ARGFLAG_ENABLE );

	// set string of target data kind
	arg.set_targetkind( "region data" );

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
			// get region data
			ret = do_dcimg_getdata_region( hdcimg, arg );
		}

		// close DCIMG handle
		dcimg_close( hdcimg );
	}

	printf( "PROGRAM END\n" );
	return ret;	//0:Success, Ohter:Failure
}