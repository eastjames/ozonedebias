# a debiasing object
#from .obs import ObsGetter, Castnet
#from .model import ModGetter, Camchem
from .obsgetter import ObsGetter, Castnet
from .modgetter import ModGetter, Camchem
from . import clustering

import numpy as np
import os
global basedir
basedir = '/'.join(os.path.abspath(__file__).split('/')[:-1])


class Debiaser:
    '''
    A debias class
    has:
        - model info
        - observation info
    can then perform clustering and debiasing on 
    these things
    '''
    
    def __init__(self):
        self.mod = None # modgetter object
        self.obs = None # obsgetter object
        self.outdir = None # directory to save out files
        
    def assign_obs(self, kind = 'castnet', mda8file = None):
        '''
        assign observation data here...
        assume that file conforms to type requirements
        * kind: type of obs
        * file: optional user supplied file
        '''
        if ( # no file given, check for castnet
            ( kind == 'castnet' ) &
            ( mda8file == None )
        ):
            self.obs = Castnet()
            self.obs.get_castnet()
            self.obs.open_clean_castnet()
            self.obs.tomda8()
            self.obs.pair_sites()
        elif ( # file given
            ( kind == 'castnet' ) &
            ( mda8file != None )
        ):
            self.obs = Castnet()
            self.obs.castnet_from_existing(mda8file)
            self.obs.checkfile() # check the file conforms (empty for now)
        else:
            print('No obs assigned')
            
            
        # do more here? clean/get data?
        # what to do with the file?
        
        
        
    def assign_mod(self, kind = 'camchem', file = None):
        '''
        assign model data here...
        
        * kind: kind of model, options 'camchem',
        * file: path to model file or list of paths
        '''
        if kind == 'camchem':
            if file is None:
                print('\nFile required\n')
            self.mod = Camchem(file)
            
            
    def mod_from_existing(self, modgetter):
        '''
        assign model data here...
        
        modgetter: modgetter object
        '''
        self.mod = modgetter
    
    def save_inertia(
            self, 
            outpath = f'{basedir}/data/clustering/inertia.csv',
            ntries = 15
        ):
        '''
        Save out inertia data for plotting
        '''
        df = clustering.prepcols(self.obs.df)
        dfstd = clustering.standardize(df)
        clustering.save_inertia_data(dfstd, outpath, ntries)
        
    def cluster_obs(
            self,
            toyear = 2000, 
            clusterby = ['ozone','x95','std','i','j'],
            shuffledata = False,
            n_clusters = 7
        ):
        '''
        Cluster obs using kmeans
        
        * toyear: year to detrend to, only sites in that year kept
        * clusterby: cols to cluster on
        * shuffledata: whether to random dearrange df before clustering
        * n_clusters: number of clusters
        '''
        self.obs.sitell_to_modij(self.mod) # assign model i,j indices to sites
        self.obs.clipij(self.mod) # clip sites to only those within mod mask
        self.obs.clipt(self.mod) # clip obs to match mod times
        self.obs.detrendit(toyear=2000) # detrend df
        df = clustering.prepcols(self.obs.df) # prepare columns
        df = df.merge(self.obs.sitedf[['i','j','SITE_ID']],on='SITE_ID')# merge with site i,j indices
        dfstd = clustering.standardize(df, clusterby) # standardize with MinMaxScaler
        dfclustered = clustering.clusterobs(dfstd, n_clusters, clusterby , shuffledata)
        tmpdf = self.obs.sitedf.reset_index(drop=True).iloc[dfclustered['index']] # reorder in case shuffled
        tmpdf['cluster'] = dfclustered['cluster']
        self.obs.sitedf = tmpdf
        
    def cluster_mod(self, clusterby = ['ozone','i','j'], ozkey = 'O3_SRF_8H_24HMAX'):
        '''
        Cluster model grid cells to obs clusters
        using Nearest Centroid
        
        * clusterby: features of model data to sort on
        '''
        dfm = clustering.prepmod(self.mod.ds, self.mod.usmask)
        modclusters = clustering.clustermod(dfm, clusterby)
        dclusters = self.mod.ds[ozkey].mean('date').copy(deep=True).rename('cluster')
        dclusters.values.ravel()[~np.isnan(dclusters.where(usmask).values.flatten())] = mclusters
        self.mod.clusters = dclusters
        
