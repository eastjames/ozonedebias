# cluster the obs and model

import xarray as xr
import scipy 
from glob import glob
import numpy as np
import pandas as pd

from sklearn import preprocessing
from sklearn import cluster

#datadir = 'data'
#cndir = 'data/castnet'


def prepcols(df, year=2000)
    '''
    Pre df for clustering
    mean, 95%, std at each site for year
    
    * df: has cols [SITE_ID, ozone, lat, lon]
    * year: target year of 'all'
    
    returns: df of aggregate site data
    '''
    sitegb = df.groupby('SITE_ID')
    dfsites = (
        sitegb.first()[['lat','lon']]
        .merge(sitegb.mean()['ozone'])
    )
    ozx = sitegb.quantile(0.95)['ozone'].rename('x95')
    obstd = sitegb.std()['ozone'].rename('std')
    dfsites = dfsites.merge(ozx,on='SITE_ID') # 95th %
    dfsites = dfsites.merge(obstd,on='SITE_ID') #std deviation
    return dfsites

def
