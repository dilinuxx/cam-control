/**
 @file	getdata_sensorparam.cpp
 @date	2017-04-06

 @copyright	Copyright (C) 2017-2024 Hamamatsu Photonics K.K.. All rights reserved.

 @brief		Sample code to get sensor information of image.
 @details	This program gets and display the sensor setting on recorded.
 @remarks	dcimg_getdata
 */

#include "../misc/console_dcimg.h"
#include "../misc/common_dcimg.h"

/**
 @brief	Get and show sensor setting.
 @details	This function gets the sensor setting of specified session and displays binning and subarray information.
 @param hdcimg		DCIMG handle
 @param arg		class to manage arguments
 @return	result to get sensor setting. 0 is success
 @sa	dcimg_getparaml, dcimg_setsessionindex, dcimg_getdata
 */
int do_dcimg_getdata_sensorparam( HDCIMG hdcimg, const cmdline& arg )
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

	int32 nView;
	err = dcimg_getparaml( hdcimg, DCIMG_IDPARAML_NUMBEROF_VIEW, &nView );
	if( failed(err) )
		nView = 1;

	int	ret = 0;

	// get data of sensor setting
	DCIMGDATA_SENSORPARAM	imgdatasensorparam;
	memset( &imgdatasensorparam, 0, sizeof(imgdatasensorparam) );
	imgdatasensorparam.hdr.size		= sizeof(imgdatasensorparam);
	imgdatasensorparam.hdr.iKind	= DCIMGDATA_KIND__SENSORPARAM;

	int iView;
	for( iView=0; iView<nView; iView++ )
	{
		imgdatasensorparam.hdr.option	= DCIMGDATA_OPTION__VIEW_1 + DCIMGDATA_OPTION__VIEW__STEP * iView;

		err = dcimg_getdata( hdcimg, &imgdatasensorparam.hdr );
		if( failed(err) )
		{
			dcimgcon_show_dcimgerr( err, "dcimg_getdata(DCIMGDATA_KIND__SENSORPARAM)" );
			ret = 3;
		}
		else
		{
			printf( "----- View%d -----\n", iView + 1 );
			printf( "binning: %d\n",			imgdatasensorparam.binning );
			printf( "horizontal offset: %d\n",	imgdatasensorparam.sensorhpos );
			printf( "horizontal size: %d\n",	imgdatasensorparam.sensorhsize );
			printf( "vertical offset: %d\n",	imgdatasensorparam.sensorvpos );
			printf( "vertical size: %d\n",		imgdatasensorparam.sensorvsize );
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
	arg.set_targetkind( "sensor information of image" );

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
			// get sensor setting information
			ret = do_dcimg_getdata_sensorparam( hdcimg, arg );
		}

		// close DCIMG handle
		dcimg_close( hdcimg );
	}


	printf( "PROGRAM END\n" );
	return ret;	//0:Success, Ohter:Failure
}