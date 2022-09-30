# cluster the obs and model

import xarray as xr
import scipy 
from glob import glob
import numpy as np
import pandas as pd
import os

from sklearn import preprocessing
from sklearn import cluster
from sklearn.neighbors import NearestCentroid

global basedir
basedir = '/'.join(os.path.abspath(__file__).split('/')[:-1])

#datadir = 'data'
#cndir = 'data/castnet'


def prepcols(df):
    '''
    Pre df for clustering
    mean, 95%, std at each site for year
    
    * df: has cols [SITE_ID, ozone, lat, lon]
    #* year: target year of 'all'
    
    returns: df of aggregate site data
    '''
    sitegb = df.groupby('SITE_ID')
    dfsites = (
        sitegb.first()[['lat','lon']]
        .merge(sitegb.mean()[['ozone']],on='SITE_ID')
    )
    ozx = sitegb.quantile(0.95)['ozone'].rename('x95')
    obstd = sitegb.std()['ozone'].rename('std')
    dfsites = dfsites.merge(ozx,on='SITE_ID') # 95th %
    dfsites = dfsites.merge(obstd,on='SITE_ID') #std deviation
    return dfsites


def standardize(df, keepcols = ['ozone','x95','std','i','j']):
    '''
    Standardize the data for clustering
    assumes "prepcols()" done
    Uses MinMax() scaler
    
    * df: includes cols ['ozone','x95','std','i','j']
    * keepcols: cols to standardize
    '''
    dfminmax = pd.DataFrame() #minmax scaler
    for d,n in zip([df[k].to_numpy()[:,None] for k in keepcols], keepcols):
        #scaler = preprocessing.StandardScaler() # standard scaler
        #dfstd[n] = scaler.fit_transform(d).squeeze()
        minmax = preprocessing.MinMaxScaler() #minmax scaler
        dfminmax[n] = minmax.fit_transform(d).squeeze()
    return dfminmax



def clusterobs(df, n_clusters, clusterby, random, samplefrac):
    '''
    Cluster with kmeans clustering
    
    * df: prepped and standardized dataframe
    * n_clusters: int, number of clusters
    * clusterby: list, features to cluster by, must be column names in df
    * random: bool, whether to shuffle dataframe data before clustering
    '''

    kmeans = cluster.KMeans(n_clusters,init='k-means++',random_state=1)
    if random:
        dfs = df.sample(frac=samplefrac).reset_index(drop=False)
    else:
        dfs = df.reset_index(drop=False)
    dfs['cluster']= kmeans.fit_predict(dfs[clusterby])
    
    return dfs

def prepmod(ds, usmask, clusterby = ['ozone','x95','std','i','j'], ozkey='O3_SRF_8H_24HMAX'):
    '''
    Prep model data for clustering
    * ds: dataset with lon, lat
    
    returns: data frame of standardized model data
    '''
    ic = np.arange(ds.lon.size)
    jc = np.arange(ds.lat.size)
    iic,jjc=np.meshgrid(ic,jc)
    #iius = iic[usmask][:,None]
    #jjus = jjc[usmask][:,None]
    
    dprep = dict()
    dprep['i'] = iic[usmask][:,None]
    dprep['j'] = jjc[usmask][:,None]
    dprep['ozone'] = ds[ozkey].mean('date').values[usmask][:,None]
    dprep['x95'] = ds[ozkey].quantile(0.95,'date').values[usmask][:,None]
    dprep['std'] = ds[ozkey].std('date').values[usmask][:,None]
    #dsm = ds['O3_SRF_8H_24HMAX'].mean('date').where(usmask)
    #dsm1d = dsm.values[~np.isnan(dsm)][:,None]
    
    dfm = pd.DataFrame()
    for k,v in dprep.items():
        if k in clusterby:
            scaler = preprocessing.MinMaxScaler()
            dfm[k] = scaler.fit_transform(v).squeeze()
            
    #for d,n in zip([dsm1d, jjus, iius],['ozone','j','i']):
        #scaler = preprocessing.MinMaxScaler()
        #dfm[n] = scaler.fit_transform(d).squeeze()
        
    return dfm

def clustermod(df, obs, clusterby):
    '''
    Cluster model grid cells to obs clusters
    using Nearest Centroid
    
    * df: dataframe of model values, standardized
    * obs: obs object
    * clusterby: features of model data to sort on
    '''
    
    clf = NearestCentroid()
    # fit to obs
    #clf.fit(obs.sitedf[clusterby].values, obs.sitedf['cluster'].values)
    clf.fit(obs.clusterdf[clusterby].values, obs.clusterdf['cluster'].values)
    # sort mod
    mclusters = clf.predict(df[clusterby].values)
    return mclusters
    

def save_inertia_data(df, outpath = f'{basedir}/data/clustering/inertia.csv', ntries=15):
    '''
    Save data needed to created "elbow plot"
    * df: dataframe of standardized data
    * outpath: where to save data
    * ntries: number of clusters to test
    '''
    import itertools
    dinertia = dict()
    tmpl = ['x95','ozone','std']
    trynclusters = np.arange(1,ntries+1)
    for nn in range(1,4):
        for i in itertools.combinations(tmpl,nn):
            print(i)
            mykey = '-'.join(list(i))
            dinertia[mykey]=[]
            for nc in trynclusters:
                clusterby=list(i)+['i','j']#'x95',
                kmeans = cluster.KMeans(n_clusters=nc,init='k-means++')
                #kmeans.fit_predict(dfstd[clusterby])
                kmeans.fit_predict(df[clusterby])
                dinertia[mykey].append(kmeans.inertia_)
    outdir = '/'.join(outpath.split('/')[:-1])
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    dfout = pd.DataFrame(dinertia).to_csv(outpath)