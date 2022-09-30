import pandas as pd
import os
from .detrend import detrender
import numpy as np

class ObsGetter:
    '''
    obsgetter class
    has a kind, right now only "castnet"
    df has columns ['SITE_ID','DATE_TIME','lat','lon','ozone']
    '''
    def __init__(self,kind):
        #self.file = file
        self.df = None # data frame of data
        self.sitedf = None # data frame of site data
        self.kind = kind # kind i.e. castnet
        self.datadir = f'data/{kind}'# data dir for this kind
        
    def tomda8(self,update=True):
        '''
        Calculate mda8
        * update: bool, whether to update class df
        '''
        #df = self.df.copy(deep=True)
        df = self.df
        keepcols = ['SITE_ID','DATE_TIME','ozone']
        #df['day'] = df['DATE_TIME'].dt.strftime('%Y%j')
        df['day'] = df['DATE_TIME'].dt.year*1000 + df['DATE_TIME'].dt.dayofyear
        gbd = df.groupby(['day','SITE_ID'])
        mda8 = (
            gbd.rolling(8,6)['OZONE'].mean()
            .groupby(['day','SITE_ID']).max()
            .rename('ozone').reset_index()
        )
        df = (
            gbd.first()
            .merge(mda8,on=['day','SITE_ID'])
            .reset_index()[keepcols].dropna()
        )
        if update:
            self.df = df
        return df
        
    
    
    def pair_sites(self, sitefile=None, update=True):
        '''
        Add lat/lon info to castnet dataframe
        * sitefile: optional, supply own sitefile
        * update: bool, whether to update class df, default true
        '''
        if sitefile == None:
            print('No sitefile given, using CASTNET sites')
            sitefile = f'{self.datadir}/Site.csv'
        keepcols = ['SITE_ID','LATITUDE','LONGITUDE']
        dfsites = pd.read_csv(sitefile)[keepcols]
        df = self.df.copy(deep=True)
        df = (
            df.merge(dfsites,on='SITE_ID')
            .rename(columns={'LATITUDE':'lat','LONGITUDE':'lon'})
            .dropna()
        )
        if update:
            self.sitedf = (
                df.groupby(['SITE_ID'])
                .first()[['SITE_ID','lat','lon']]
            )
            self.df = df
        return df
    
    
    def castnet_from_existing(self, file):
        '''
        Open an already prepared castnet MDA8 file
        Performs simple tests
        '''
        tmpdf = pd.read_csv(file,index_col=0)
        tmpdf['DATE_TIME'] = pd.to_datetime(tmpdf['DATE_TIME'])
        
        # test that all columns are there
        mycols = ['SITE_ID','DATE_TIME','ozone','lat','lon']
        assert tmpdf.columns.isin(mycols).all()
        
        # test that it is daily (not hourly) values
        tmpdf['days'] = tmpdf['DATE_TIME'].dt.year*1000 + tmpdf['DATE_TIME'].dt.dayofyear
        assert ~tmpdf[['days','SITE_ID']].duplicated().all()
        
        self.df = tmpdf[mycols].dropna()


    def detrendit(self,ozkey='ozone',toyear=2000):
        '''
        detrend castnet obs to year 2000
        '''
        return detrender(self.df,ozkey='ozone',toyear=2000)
    
    def _updatesites(self):
        '''
        update the site df
        '''
        if self.sitedf is None:
            self.sitedf = (
                self.df.groupby(['SITE_ID'])
                .first()[['lat','lon']]
                .reset_index()
            )
    
    def savedf(self, fname = 'tmp.csv'):
        self.df.to_csv(f'{self.datadir}/{fname}')
        
    def sitell_to_modij(self, mod):
        '''
        convert site lat/lon to
        i,j indices on the model grid
        Note -- assumes CAM Chem grid
        * mod: ModGetter object
        '''
        self._updatesites()
        self.sitedf['i'] = (
            (np.abs(
                mod.ds.lon.values - 
                #(self.sitedf['lon'].values[:,None]-180)%360
                (self.sitedf['lon'].values[:,None])%360
            )).argmin(1)
        )
        self.sitedf['j'] = (
            (np.abs(
                mod.ds.lat.values - 
                self.sitedf['lat'].values[:,None]
            )).argmin(1)
        )
    
    def clipij(self, mod):
        '''
        get rid of sites outside domain
        * mod: ModGetter object
        '''
        modij = np.stack(
            np.where(mod.usmask)[::-1], axis=1
        )
        
        obsij = np.stack(
            [self.sitedf['i'], self.sitedf['j']], axis=1
        )
        
        inmod = np.stack(
            [np.in1d(obsij[:,0], modij[:,0]),
            np.in1d(obsij[:,1], modij[:,1])],
            axis=1
        ).all(1)
        
        self.sitedf = self.sitedf[inmod]
        self.df = self.df.merge(self.sitedf[['SITE_ID']],on='SITE_ID')
    
    
    def cluster(self):
        '''
        apply clustering to castnet sites
        '''
        # Not yet implemented
        # Need code from Bezier
        #return dfcastnet
        pass
            

    
        
class Castnet(ObsGetter):
    '''
    castnet specific ops for the obsgetter
    '''
    def __init__(self):
        super().__init__(kind='castnet')
        
    def checkfile(self):
        print('checkfile() not implemented')
        pass

    def check_castnet(self):
        '''
        Check if castnet files exist
        '''
        castnetfs = [
            'ozone_columninfo.csv',
            'ozone.csv',
            'ozone_tableinfo.csv'
        ]
        castnetzip = 'ozone.zip'
        hasfiles = True
        for f in castnetfs:
            if os.path.exists(f'{self.datadir}/{f}'):
                 hasfiles = hasfiles & True
            else:
                 hasfiles = hasfiles & False
        haszip = os.path.exists(f'{self.datadir}/{castnetzip}')
        return (haszip, hasfiles)
    
    
    def get_castnet(self):
        '''
        download CASTNET if not already there
        https://gaftp.epa.gov/Castnet/CASTNET_Outgoing/data/ozone.zip
        '''
        haszip, hasfiles = self.check_castnet()
        
        if hasfiles: # I have files; do nothing
            print('CASTNET files are here')
            return
        
        elif haszip: # I have no files and have zip
            print('Unzipping CASTNET...',end='')
            import zipfile
            with zipfile.ZipFile('ozone.zip', 'r') as zf:
                zf.extractall(self.datadir)
            print('done!')
                
        else: # I have nothing
            import urllib.request
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
            print('Downloading CASTNET...',end='')
            myurl = 'https://gaftp.epa.gov/Castnet/CASTNET_Outgoing/data/ozone.zip'
            urllib.request.urlretrieve(myurl,filename=f'{self.datadir}/ozone.zip')
            print('done!')
            print('Unzipping CASTNET...',end='')
            import zipfile
            with zipfile.ZipFile(f'{self.datadir}/ozone.zip', 'r') as zf:
                zf.extractall(self.datadir)
            print('done!')
        
    
    def open_clean_castnet(self,castnetfile=None,yearlim=(1980,2010)):
        '''
        open raw EPA CASTNET file
        clean castnet
        clip to dates and get rid of invalid values
        '''
        if castnetfile == None:
            castnetfile = f'{self.datadir}/ozone.csv'
        df = pd.read_csv(castnetfile)
        dftab = pd.read_csv(f'{self.datadir}/ozone_tableinfo.csv',header=6)
        df['DATE_TIME'] = pd.to_datetime(df['DATE_TIME'])
        timequery = (
            f'(DATE_TIME.dt.year >= {yearlim[0]}) & '
            f'(DATE_TIME.dt.year <= {yearlim[1]})'
        )
        df = df.query(timequery)
        self.df = df[(df['OZONE_F'].isin(dftab.query('VALIDITY == "Valid"')['CODE']))]
        return self.df
    
    
