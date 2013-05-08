"""
Defines the MEDS class to work with MEDS (Multi Epoch Data Structures)

See docs for the MEDS class for more info

    Copyright (C) 2013, Erin Sheldon, BNL

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import numpy
import fitsio

class MEDS(object):
    """
    Class to work with MEDS (Multi Epoch Data Structures)

    For details of the structure, see
    https://cdcvs.fnal.gov/redmine/projects/deswlwg/wiki/Multi_Epoch_Data_Structure

    One can extract cutouts using get_cutout() and get_mosaic() and
    get_cutout_list()

    One can access all fields from the catalog using [field_name] notation. The
    number of entries is in the .size attribute. Note the actual fields in the
    catalog may change over time.  You can use get_cat() to get the full
    catalog as a recarray.

    The first cutout for an object is always from the coadd.

    public methods
    --------------
    get_cutout(iobj, icutout)
        Get a single cutout for the indicated entry
    get_mosaic(iobj)
        Get a mosaic of all cutouts associated with this coadd object
    get_cutout_list(iobj)
        Get an image list with all cutouts associated with this coadd object
    get_cweight_cutout(iobj, icutout)
        Composite the weight and seg maps, interpolating seg map from the coadd
    get_cweight_mosaic(iobj)
        Composite the weight and seg maps, interpolating seg map from the coadd
        get all maps in a mosaic
    get_cweight_cutout_list(iobj)
        Composite the weight and seg maps, interpolating seg map from the coadd
        get all maps in a list
    get_source_path(iobj, icutout)
        Get the source filename associated with the indicated cutout
    get_sky_path(iobj, icutout)
        Get the source sky filename associated with the indicated cutout
    get_source_info(iobj, icutout)
        Get all info about the source images
    get_cat()
        Get the catalog; extension 1
    get_image_info()
        Get the entire image info structure
    get_meta()
        Get all the metadata
    get_jacobian(self, iobj, icutout)
        Get the jacobian as a dict
    get_jacobian_list(self, iobj)
        Get the list of jacobians for all cutouts for this object.



    examples
    --------
    from deswl import meds
    m=meds.MEDS(filename)

    # number of coadd objects
    num=m.size

    # number of cutouts for object 35
    m['ncutout'][35]

    # get cutout 3 for object 35
    im=m.get_cutout(35,3)

    # get all the cutouts for object 35 as a single image
    mosaic=m.get_mosaic(35)

    # get all the cutouts for object 35 as a list of images
    im=m.get_cutout_list(35)

    # get a cutout for the weight map
    wt=m.get_cutout(35,3,type='weight')

    # get a cutout for the segmentation map
    seg=m.get_cutout(35,3,type='seg')

    # get the source filename for cutout 3 for object 35
    fname=m.get_source_path(35,3)

    # you can access any of the columns in the
    # catalog (stored as a recarray) directly

    # e.g. get the center in the cutout for use in image processing
    row = m['row_cutout'][35]
    col = m['col_cutout'][35]

    # source filename
    fname = m.get_source_path(35,3)

    # or you can just get the catalog to work with
    cat=m.get_cat()
    info=m.get_image_info()
    meta=m.get_meta()


    Fields in main catalog
    -----------------------

     id                 i4       id from coadd catalog
     ncutout            i4       number of cutouts for this object
     box_size           i4       box size for each cutout
     file_id            i4[NMAX] zero-offset id into the file names in the 
                                 second extension
     start_row          i4[NMAX] zero-offset, points to start of each cutout.
     orig_row           f8[NMAX] zero-offset position in original image
     orig_col           f8[NMAX] zero-offset position in original image
     orig_start_row     i4[NMAX] zero-offset start corner in original image
     orig_start_col     i4[NMAX] zero-offset start corner in original image
     cutout_row         f8[NMAX] zero-offset position in cutout imag
     cutout_col         f8[NMAX] zero-offset position in cutout image
     dudrow             f8[NMAX] jacobian of transformation 
                                 row,col->ra,dec tangent plane (u,v)
     dudcol             f8[NMAX]
     dvdrow             f8[NMAX]
     dvdcol             f8[NMAX]


    requirements
    ------------
    numpy
    fitsio https://github.com/esheldon/fitsio
    """
    def __init__(self, filename):
        self._filename=filename
        
        self._fits=fitsio.FITS(filename)

        self._cat=self._fits["object_data"][:]
        self._image_info=self._fits["image_info"][:]
        self._meta=self._fits["metadata"][:]

    def get_cutout(self, iobj, icutout, type='image'):
        """
        Get a single cutout for the indicated entry

        parameters
        ----------
        iobj:
            Index of the object
        icutout:
            Index of the cutout for this object.
        type: string, optional
            Cutout type. Default is 'image'.  Allowed
            values are 'image','weight'

        returns
        -------
        The cutout image
        """
        self._check_indices(iobj, icutout=icutout)

        box_size=self._cat['box_size'][iobj]
        start_row = self._cat['start_row'][iobj,icutout]
        row_end = start_row + box_size*box_size

        extname=self._get_extension_name(type)

        imflat = self._fits[extname][start_row:row_end]
        im = imflat.reshape(box_size,box_size)
        return im

    def get_mosaic(self, iobj, type='image'):
        """
        Get a mosaic of all cutouts associated with this coadd object

        parameters
        ----------
        iobj:
            Index of the object
        type: string, optional
            Cutout type. Default is 'image'.  Allowed
            values are 'image','weight'

        returns
        -------
        An image holding all cutouts
        """

        self._check_indices(iobj)

        ncutout=self._cat['ncutout'][iobj]
        box_size=self._cat['box_size'][iobj]

        start_row = self._cat['start_row'][iobj,0]
        row_end = start_row + box_size*box_size*ncutout

        extname=self._get_extension_name(type)

        mflat=self._fits[extname][start_row:row_end]
        mosaic=mflat.reshape(ncutout*box_size, box_size)

        return mosaic

    def get_cutout_list(self, iobj, type='image'):
        """
        Get an image list with all cutouts associated with this coadd object

        Note each individual cutout is actually a view into a larger
        mosaic of all images.

        parameters
        ----------
        iobj:
            Index of the object
        type: string, optional
            Cutout type. Default is 'image'.  Allowed
            values are 'image','weight'

        returns
        -------
        A list of images hold all cutouts.
        """

        mosaic=self.get_mosaic(iobj,type=type)
        ncutout=self._cat['ncutout'][iobj]
        box_size=self._cat['box_size'][iobj]
        return self._split_mosaic(mosaic, box_size, ncutout)

    def get_cweight_cutout(self, iobj, icutout):
        """
        Composite the weight and seg maps, interpolating seg map from the coadd

        The weight is set to zero outside the region as defined in the coadd

        parameters
        ----------
        iobj:
            Index of the object
        type: string, optional
            Cutout type. Default is 'image'.  Allowed
            values are 'image','weight'

        returns
        -------
        The weight map
        """
        wt=self.get_cutout(iobj, icutout, type='weight')
        coadd_seg=self.get_cutout(iobj, 0, type='seg')
        cwt=self._make_composite_weight(iobj, icutout, wt, coadd_seg)
        return cwt

    def get_cweight_mosaic(self, iobj):
        """
        Composite the weight and seg maps, interpolating seg map from the coadd

        The weight is set to zero outside the region as defined in the coadd

        parameters
        ----------
        iobj:
            Index of the object
        type: string, optional
            Cutout type. Default is 'image'.  Allowed
            values are 'image','weight'

        returns
        -------
        A composite of all weight maps
        """
        wtmosaic=self.get_mosaic(iobj, type='weight')
        coadd_seg=self.get_cutout(iobj, 0, type='seg')

        ncutout=self._cat['ncutout'][iobj]
        box_size=self._cat['box_size'][iobj]

        # shares underlying storage
        wlist = self._split_mosaic(wtmosaic, box_size, ncutout)

        for icutout,wt in enumerate(wlist):
            cwt=self._make_composite_weight(iobj, icutout, wt, coadd_seg)
            wt[:,:] = cwt[:,:]

        return wtmosaic

    def get_cweight_cutout_list(self, iobj):
        """
        Composite the weight and seg maps, interpolating seg map from the coadd

        The weight is set to zero outside the region as defined in the coadd

        parameters
        ----------
        iobj:
            Index of the object
        type: string, optional
            Cutout type. Default is 'image'.  Allowed
            values are 'image','weight'

        returns
        -------
        A list containing all weight maps
        """
        wtmosaic=self.get_cweight_mosaic(iobj)

        ncutout=self._cat['ncutout'][iobj]
        box_size=self._cat['box_size'][iobj]

        # shares underlying storage
        wlist = self._split_mosaic(wtmosaic, box_size, ncutout)
        return wlist

    def get_jacob_as_matrix(self, iobj, icutout):
        """
        Get the jacobian as a numpy matrix

        parameters
        ----------
        iobj:
            Index of the object
        type: string, optional
            Cutout type. Default is 'image'.  Allowed
            values are 'image','weight'

        returns
        -------
        A 2x2 matrix of the jacobian
            dudrow dudcol
            dvdrow dvdcol
        """
        jacob=numpy.matrix( numpy.zeros( (2,2) ), copy=False)

        jacob[0,0] = self['dudrow'][iobj,icutout]
        jacob[0,1] = self['dudcol'][iobj,icutout]
        jacob[1,0] = self['dvdrow'][iobj,icutout]
        jacob[1,1] = self['dvdcol'][iobj,icutout]

        return jacob


    def get_source_info(self, iobj, icutout):
        """
        Get the full source file information for the indicated cutout.

        Includes SE image and sky image

        parameters
        ----------
        iobj: 
            Index of the object
        """
        self._check_indices(iobj, icutout=icutout)
        ifile=self._cat['file_id'][iobj,icutout]
        return self._image_info[ifile]

    def get_source_path(self, iobj, icutout):
        """
        Get the source filename associated with the indicated cutout

        parameters
        ----------
        iobj:
            Index of the object
        icutout:
            Index of the cutout for this object.

        returns
        -------
        The filename
        """

        info=self.get_source_info(iobj, icutout)
        return info['image_path']

    def get_sky_path(self, iobj, icutout):
        """
        Get the source filename associated with the indicated cutout

        parameters
        ----------
        iobj:
            Index of the object
        icutout:
            Index of the cutout for this object.

        returns
        -------
        The filename
        """

        info=self.get_source_info(iobj, icutout)
        return info['sky_path']


    def get_cat(self):
        """
        Get the catalog
        """
        return self._cat

    def get_image_info(self):
        """
        Get all image information
        """
        return self._image_info
    
    def get_meta(self):
        """
        Get all the metadata
        """
        return self._meta

    def get_jacobian(self, iobj, icutout):
        """
        Get the jacobian as a dict keyed by

            dudrow
            dudcol
            dvdcol
            dvdrow

        parameters
        ----------
        iobj:
            Index of the object
        icutout:
            Index of the cutout for this object.
        """
        self._check_indices(iobj,icutout=icutout)
        return {'dudrow':self['dudrow'][iobj,icutout],
                'dudcol':self['dudcol'][iobj,icutout],
                'dvdcol':self['dvdcol'][iobj,icutout],
                'dvdrow':self['dvdrow'][iobj,icutout]}

    def get_jacobian_list(self, iobj):
        """
        Get the list of jacobians for all cutouts
        for this object.

        parameters
        ----------
        iobj:
            Index of the object
        """
        self._check_indices(iobj)
        jlist=[]
        for icutout in xrange(self['ncutout'][iobj]):
            j=self.get_jacobian(iobj, icutout)
            jlist.append(j)

        return jlist


    def _make_composite_weight(self, iobj, icutout, wt, coadd_seg):
        """
        Internal routine to composite the coadd seg onto the weight map

        for the coadd this is easy, but for SE cutouts we need to use the
        jacobian to transform between SE and coadd coordinate systems
        """
        
        cwt=wt.copy()

        coadd_rowcen=self['cutout_row'][iobj,icutout]
        coadd_colcen=self['cutout_col'][iobj,icutout]
        rowcen=self['cutout_row'][iobj,icutout]
        colcen=self['cutout_col'][iobj,icutout]

        segid=coadd_seg[coadd_rowcen,coadd_colcen]

        if icutout==0:
            # this cutout is the coadd
            w=numpy.where(coadd_seg != segid)
            if w[0].size != 0:
                cwt[w] = 0.0
        else:
            rows,cols=numpy.mgrid[0:cwt.shape[0], 0:cwt.shape[1]]
            rows = rows-rowcen
            cols = cols-colcen

            se_jacob=self.get_jacob_as_matrix(iobj, icutout)
            coadd_jacob=self.get_jacob_as_matrix(iobj, 0)

            try:
                cjinv = coadd_jacob.getI()
            except numpy.linalg.linalg.LinAlgError:
                print 'coadd jacob is singular, setting weight to zero'
                cwt[:,:] = 0.0
                return cwt

            # convert pixel coords in SE cutout to u,v
            u = rows*se_jacob[0,0] + cols*se_jacob[0,1]
            v = rows*se_jacob[1,0] + cols*se_jacob[1,1]

            # now convert into pixels for coadd
            crow = coadd_rowcen + u*cjinv[0,0] + v*cjinv[0,1]
            ccol = coadd_colcen + u*cjinv[1,0] + v*cjinv[1,1]

            crow = crow.astype('i8')
            ccol = ccol.astype('i8')

            wbad=numpy.where(   (crow < 0) | (crow >= coadd_seg.shape[0])
                              & (ccol < 0) | (ccol >= coadd_seg.shape[1]) )
            if wbad[0].size != 0:
                cwt[wbad] = 0.0

            # clipping makes the notation easier
            crow = crow.clip(0,coadd_seg.shape[0]-1)
            ccol = ccol.clip(0,coadd_seg.shape[1]-1)
            wbad=numpy.where( coadd_seg[crow,ccol] != segid )
            if wbad[0].size != 0:
                cwt[wbad] = 0.0

        return cwt


    def _get_extension_name(self, type):
        if type=='image':
            return "image_cutouts"
        elif type=="weight":
            return "weight_cutouts"
        elif type=="seg":
            return "seg_cutouts"
        else:
            raise ValueError("bad cutout type '%s'" % type)

    def _split_mosaic(self, mosaic, box_size, ncutout):
        imlist=[]
        for i in xrange(ncutout):
            r1=i*box_size
            r2=(i+1)*box_size
            imlist.append( mosaic[r1:r2, :] )

        return imlist


    def _check_indices(self, iobj, icutout=None):
        if iobj >= self._cat.size:
            raise ValueError("object index should be within "
                             "[0,%s)" % self._cat.size)

        ncutout=self._cat['ncutout'][iobj]
        if ncutout==0:
            raise ValueError("object %s has no cutouts" % iobj)

        if icutout is not None:
            if icutout >= ncutout:
                raise ValueError("requested cutout index %s for "
                                 "object %s should be in bounds "
                                 "[0,%s)" % (icutout,iobj,ncutout))

    def __repr__(self):
        return repr(self._fits[1])
    def __getitem__(self, item):
        return self._cat[item]

    @property
    def size(self):
        return self._cat.size
