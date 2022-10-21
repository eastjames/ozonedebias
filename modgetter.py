import xarray as xr 
import pandas as pd
import os
import numpy as np
# model getter object

global basedir
basedir = '/'.join(os.path.abspath(__file__).split('/')[:-1])

###
# some helper functions
###

def open_camchem(fpat, varkey=['O3_SRF_8H_24HMAX'], mjjas=True):
    '''
    * fpat: full filepath to camchem file (string)
    * varkey: variable names to extract 
        from camchem file (string or list of strings)
    * mjjas: If True, extract summertime dates only
    '''
    myyear = fpat.split('.')[-3]
    if myyear == 'AQ':
        myyear = fpat.split('.')[-4]
    try:
        ds = xr.open_dataset(fpat)[varkey]
    except KeyError:
        warnings.warn(
            f'\n*WARNING* Missing {varkey} for '
            f'{fpat.split("/")[-1]}, skipping this file'
        )
        return None
    dt = pd.to_datetime(ds.date.values,format='%Y%m%d')
    dates = pd.date_range(
        f'{myyear}-{dt.min():%m}-{dt.min():%d}',
        f'{myyear}-{dt.max():%m}-{dt.max():%d}'
    )
    if dates.is_leap_year.all():
        dates = pd.DatetimeIndex(
            data = [t for t in dates if (t.month!=2 or t.day!=29)]
        )
    ds['date'] = dates
    if mjjas:
        ds = ds.sel(
            date = pd.date_range(
                f'{dates.year[0]}-05-01',
                f'{dates.year[0]}-09-30'
            )
        )
    ds.attrs['filepath'] = fpat
    return ds


def opener(infs):
    '''
    open and concatenate camchem files
    '''
    fs = []
    for f in infs:
        d = open_camchem(f)
        fs.append(d)
    dout = xr.concat(fs, dim='date')
    return dout






###
# end of helper functions
###



class ModGetter:
    '''
    class to hold model info,data, and fxns
    Different from obs because it is many
    files, not just one file...
    
    Make it so it can open up any number of 
    files over any time frame and function 
    the same
    '''
    
    def __init__(self,kind,ds):
        self.ds = ds # xr.dataset of data
        self.dadj = None
        self.kind = kind # kind i.e. camchem
        self.datadir = f'data/{kind}'# data dir for this kind
        self.clusters = None
        
    def setdadj(self,dadj):
        self.dadj = dadj

    def setclusters(self,ds):
        self.clusters = ds
        
    def normt(self, modkey='date'):
        '''
        normalize model date
        '''
        modidx = self.ds.indexes[modkey].normalize()
        self.ds[modkey] = modidx
        
        
        
class Camchem(ModGetter):
    '''
    ModGetter subclass of Camchem model specifically
    '''
    def __init__(self, files, modtkey='date'):
        '''
        * files: path to CAMChem files to be opened
        * modtkey: name of date dimension
        '''
        if isinstance(files, list):
            ds = opener(files)
        elif isinstance(files, str):
            ds = opener([files])
        super().__init__(kind='camchem',ds=ds)
        self.normt(modtkey)
        
    def make_us_mask(self):
        pass
    
    def get_nca_region_masks(self):
        '''
        return mask for NCA regions
        with keys regnames
        '''
        # file with U.S. gridcells:
        usf = f'{basedir}/data/masks/weights-nca-regions-1.9x2.5.nc'
        regwgt = xr.open_dataset(usf)
        regnames = [
            'Southwest','GreatPlains',
            'Midwest','Northeast',
            'Northwest','Southeast'
        ]
        # each cell is assigned 1 and only 1 region:
        # max wgt determines region assignment
        rmidx = np.ma.masked_where( 
            regwgt.wgt.sum('region')==0,
            regwgt.wgt.argmax('region')
        ) + 1
        rmidx = np.where(rmidx.mask,0,rmidx)
        rm = {}
        for i,r in enumerate(regnames):
            rm[r] = (rmidx==(i+1))
        return rm
        
    
    #def make_nca_region_mask(self):
    def make_us_mask(self):
        
        # Make US mask
        rm = self.get_nca_region_masks()
        usmasktmp = np.zeros(rm['Southwest'].shape)
        for r in rm.keys():
            usmasktmp = usmasktmp + rm[r]
        usmask = usmasktmp.astype(bool) 
        rm['US'] = usmask    
        self.usmask = usmask
