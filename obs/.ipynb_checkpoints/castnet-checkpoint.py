import pandas as pd
import os
import ..detrend


def check_castnet():
    '''
    Check if castnet files exist
    '''
    datadir = '../data/castnet'
    castnetfs = [
        'ozone_columninfo.csv',
        'ozone.csv',
        'ozone_tableinfo.csv'
    ]
    castnetzip = 'ozone.zip'
    hasfiles = True
    for f in castnetfs:
        if os.path.exists(f'{datadir}/{f}'):
             hasfiles = hasfiles & True
        else:
             hasfiles = hasfiles & False
    haszip = os.path.exists(f'{datadir}/{castnetzip}')
    return (haszip, hasfiles)


def get_castnet():
    '''
    download CASTNET if not already there
    https://gaftp.epa.gov/Castnet/CASTNET_Outgoing/data/ozone.zip
    '''
    datadir = '../data/castnet'
    haszip, hasfiles = get_castnet()
    
    if hasfiles: # I have files; do nothing
        return
    
    elif haszip: # I have no files and have zip
        print('Unzipping CASTNET...',end='')
        import zipfile
        with zipfile.ZipFile('ozone.zip', 'r') as zf:
            zf.extractall(datadir)
        print('done!')
            
    else: # I have nothing
        import urllib.request
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context
        print('Downloading CASTNET...',end='')
        myurl = 'https://gaftp.epa.gov/Castnet/CASTNET_Outgoing/data/ozone.zip'
        urllib.request.urlretrieve(myurl,filename='../data/castnet/ozone.zip')
        print('done!')
        print('Unzipping CASTNET...',end='')
        import zipfile
        with zipfile.ZipFile('ozone.zip', 'r') as zf:
            zf.extractall(datadir)
        print('done!')
    

def open_clean_castnet(yearlim=(1980,2010)):
    '''
    clean castnet
    clip to dates and get rid of invalid values
    '''
    datadir = '../data/castnet'
    df = pd.read_csv(f'{datadir}/ozone.csv')
    dftab = pd.read_csv(f'{datadir}/ozone_tableinfo.csv',header=6)
    df['DATE_TIME'] = pd.to_datetime(df['DATE_TIME'])
    timequery = (
        f'(DATE_TIME.dt.year >= {yearlim[0]}) & '
        f'(DATE_TIME.dt.year <= {yearlim[1]})'
    )
    df = df.query(timequery)
    df = df[(df['OZONE_F'].isin(dftab.query('VALIDITY == "Valid"')['CODE']))]
    return df


def tomda8(df):
    '''
    Calculate mda8
    '''
    keepcols = ['SITE_ID','DATE_TIME','ozone']
    df['day'] = df['DATE_TIME'].dt.strftime('%Y%j')
    mda8 = (
        df.groupby('day').rolling(8,6)['OZONE'].mean()
        .groupby('day').max()
        .rename('ozone')
    )
    df = (
        df.groupby('day').first()
        .merge(mda8,on='day')
        .reset_index()[keepcols]
    )
    return df


def pair_sites(df):
    '''
    Add lat/lon info to castnet dataframe
    '''
    datadir = '../data/castnet'
    keepcols = ['SITE_ID','LATITUDE','LONGITUDE']
    dfsites = pd.read_csv(f'{datadir}/Site.csv')[keepcols]
    df = (
        df.merge(dfsites,on='SITE_ID')
        .rename(columns={'LATITUDE':'lat','LONGITUDE':'lon'})
    )
    return df


def detrendit(df):
    '''
    detrend castnet obs to year 2000
    '''
    return detrend.detrender(df)


def savedf(df, fname = 'tmp.csv'):
    datadir = '../data/castnet'
    pd.to_csv(f'{datadir}/{fname})
    

    

def clip():
    '''
    get rid of sites outside domain
    '''
    return dfcastnet


def cluster():
    '''
    apply clustering to castnet sites
    '''
    return dfcastnet