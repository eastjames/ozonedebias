# A CAM-Chem gridded class
# use xarray accessor?

import xarray as xr

@xr.register_dataset_accessor('cluster')
class Clusterer:
    '''
    An xarray accessor to apply clustering to CAM-Chem model
    '''
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def preprocess(self):
        '''
        Preprocess the data
        Scale data so it is all comparable using MinMaxScaler
        '''
        
    def cluster(self, obsdf):
        '''
        Cluster the data based on existing clusters
        for obs, location, and ozone value with NearestCentroid
        
        * obsdata: dataframe of obs with clusters
        
        returns: this xarray object with new cluster variable
        '''
        return 
    
    
@xr.register_dataset_accessor('debias')
class Debiaser:
    '''
    An xarray accessor to apply debiasing to CAM-Chem model
    '''
    def __init__(self, xarray_obj):
        self._obj = xarray_obj
        
    #def ???