# a debiasing object
#from .obs import ObsGetter, Castnet
#from .model import ModGetter, Camchem
from .obsgetter import ObsGetter, Castnet
from .modgetter import ModGetter, Camchem
from . import clustering
from . import debias

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
        self.modfut = None # modgetter object
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
        
        
        
    def assign_mod(self, kind = 'camchem', file = None, hist = True):
        '''
        assign model data here...
        
        * kind: kind of model, options 'camchem',
        * file: path to model file or list of paths
        * hist: bool, True if mod is historical simulation, False if it 
                is projection simulation.  Default: True
        '''
        if kind == 'camchem':
            if file is None:
                print('\nFile required\n')
            if hist: 
                self.mod = Camchem(file)
            else:
                self.modfut = Camchem(file)
            
            
    def mod_from_existing(self, modgetter, hist = True):
        '''
        assign model data here...
        
        * modgetter: modgetter object
        * hist: bool, True if mod is historical simulation, False if it 
                is projection simulation.  Default: True
        '''
        if hist:
            self.mod = modgetter
        else:
            self.modfut = modgetter
    
    def save_inertia(
            self, 
            outpath = f'{basedir}/data/clustering/inertia.csv',
            ntries = 15
        ):
        '''
        Save out inertia data for plotting
        '''
        self.obs.sitell_to_modij(self.mod) # assign model i,j indices to sites
        self.obs.clipij(self.mod) # clip sites to only those within mod mask
        self.obs.clipt(self.mod) # clip obs to match mod times
        self.obs.detrendit(toyear=2000) # detrend df
        df = clustering.prepcols(self.obs.df) # prepare columns
        df = df.merge(self.obs.sitedf[['i','j','SITE_ID']],on='SITE_ID')# merge with site i,j indices
        clusterby = ['ozone','x95','std','i','j']
        dfstd = clustering.standardize(df, clusterby) # standardize with MinMaxScaler
        #df = clustering.prepcols(self.obs.df)
        #dfstd = clustering.standardize(df)
        clustering.save_inertia_data(dfstd, outpath, ntries)
        
    def cluster_obs(
            self,
            toyear = 2000, 
            clusterby = ['ozone','x95','std','i','j'],
            shuffledata = False,
            samplefrac = 1,
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
        dfclustered = clustering.clusterobs(dfstd, n_clusters, clusterby , shuffledata, samplefrac)
        tmpdf = self.obs.sitedf.reset_index(drop=True).iloc[dfclustered['index']] # reorder in case shuffled
        #tmpdf['cluster'] = dfclustered['cluster']
        tmpdf = tmpdf.merge(dfclustered[['index','cluster']],right_on='index',left_index=True)
        #dfclustered['SITE_ID'] = tmpdf.reset_index().iloc[dfclustered['index']]['SITE_ID'].values
        dfclustered = dfclustered.merge(tmpdf[['index','SITE_ID']],on='index')
        dfclustered = dfclustered.drop(columns='index')
        self.obs.setclusterdf(dfclustered)
        self.obs.setsitedf(tmpdf.drop(columns='index'))
        
    def cluster_mod(
            self,
            clusterby = ['ozone','x95','std','i','j'],
            ozkey = 'O3_SRF_8H_24HMAX'
        ):
        '''
        Cluster model grid cells to obs clusters
        using Nearest Centroid
        
        * clusterby: features of model data to sort on
        '''
        dfm = clustering.prepmod(self.mod.ds, self.mod.usmask,clusterby,ozkey)
        modclusters = clustering.clustermod(dfm, self.obs, clusterby)
        dclusters = (
            self.mod.ds[ozkey]
            .mean('date').where(self.mod.usmask)
            .copy(deep=True)
            .rename('cluster')
        )
        dclusters.values[self.mod.usmask] = modclusters
        self.mod.setclusters(dclusters)

    def corrector(
            self,
            hist = True,
            QS = np.arange(0,1.001,0.001),
            modozkey='O3_SRF_8H_24HMAX',
            clusterlist = None
        ):
        '''
        Recursively call bias corrector for each region
        
        * hist: bool, True if historical correction, False if 
                projection correction. Default: True
        * clusterlist: list of cluster numbers, default is list of
                       unique, non-nan values in self.mod.clusters
        * QS: quantiles, defaults np.arange(0,1.001,0.001)
        * modozkey: name of mod ozone var, O3_SRF_8H_24HMAX
        
        Returns: dataarray of 3d model mda8 o3 with regions corrected based on obsdf
        '''
        if clusterlist is None:
            clusterlist = list(filter(lambda v: v == v, np.unique(self.mod.clusters.values)))
            
        if len(clusterlist) == 0:
            return #self.mod.dsadj
        
        # historical correction
        elif hist: 
            self.mod.setdadj(
                debias.bias_correct_hist(self, clusterlist.pop(), QS, modozkey)
            )
            return self.corrector(hist, QS, modozkey, clusterlist)
        
        # future correction
        else: 
            self.modfut.setdadj(
                debias.bias_correct_future(self, clusterlist.pop(), QS, modozkey)
            )
            return self.corrector(hist, QS, modozkey, clusterlist)