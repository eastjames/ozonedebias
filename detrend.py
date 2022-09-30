from scipy import signal
import pandas as pd


def detrender(df, ozkey='ozone', toyear=2000):
    '''
    Detrend CASTNET based on mean in a particular year
    Apply that year mean at each site and only include
    sites that existed in that year.
    
    * df: castnet dataframe with cols lat,lon,SITE_ID,ozone,DATE_TIME
    * ozkey: (str) in case ozone has different name
    * toyear: year to detrend to, or 'all'
    
    returns: dataframe, detrended to toyear, with only sites that
             existed in that year
    '''
    
    if toyear == 'all':
        myyear = pd.date_range('1987-01-01','2010-12-31')
    else:
        myyear = pd.date_range(f'{toyear}-01-01', f'{toyear}-12-31')
    keepcols = ['SITE_ID','lat','lon']
    dfsites = df[df['DATE_TIME'].isin(myyear)][keepcols].groupby('SITE_ID').first()
    dfyr = df[df['SITE_ID'].isin(dfsites.index)] # subset only sites exist in myyear
    dfdetrend = dfyr.copy(deep=True)
    
    for sid in dfsites.index: # loop over all sites in myyear
        origdat = dfdetrend.query(f'SITE_ID=="{sid}"') # subset of data at site
        detrendmean = origdat[origdat['DATE_TIME'].dt.year.isin([toyear])][ozkey].mean() # subset of data at site
        dfdetrend.loc[dfdetrend['SITE_ID']==sid, ozkey] = signal.detrend(origdat[ozkey])+detrendmean # detrend that site
        dfdetrend.loc[dfdetrend[ozkey] < 0, ozkey] = 0 # set negative values to 0
        
    return dfdetrend