import xarray as xr 
import pandas as pd

# model getter object

#some helper functions
def opener(infs):
    fs = []
    for f in infs:
        d = xr.open_dataset(f)
        fs.append(d)
        print('Remember weird leap year thing!!')
        datemin = 
        datemax = 
        d = d.assign_coords(time=pd.date_range(datemin, datemax))
    dout = xr.concat(fs, dim='time')
    return dout

# end of helper functions

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
        self.ds = None # xr.dataset of data
        self.kind = kind # kind i.e. camchem
        self.datadir = f'data/{kind}'# data dir for this kind
        
        
class Camchem(ModGetter):
    '''
    ModGetter subclass of Camchem model specifically
    '''
    def __init__(self, files):
        '''
        * files: path to CAMChem files to be opened
        '''
        if isinstance(files, list):
            ds = opener(files)
        elif isinstance(files, str):
            ds = opener([files])
        super().__init__(kind='camchem',ds=ds)
    