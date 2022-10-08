# apply bias correction
from scipy.interpolate import interp1d
import numpy as np

#def biascorrecthist(obs, mod, cluster, QS, modozkey):
def bias_correct_hist(db, cluster, QS, modozkey):
    '''
    Apply bias correction to historical model simulations
    
    * db: debias object
    #* obs: obs object
    #* mod: mod object
    * cluster: int, number of the cluster being debiased
    * QS: quantile edges
    * modozkey: string, var name of model ozone
    '''
    if QS is None:
        QS = np.arange(0,1.001,0.001)
    if db.mod.dadj is None:
        db.mod.setdadj(db.mod.ds[modozkey].copy(deep=True))
    
    myobs = db.obs.df.merge( # add cluster to df
        db.obs.sitedf[['SITE_ID','cluster']],
        on='SITE_ID'
    ) 
    myobs = myobs.query(f'cluster == {cluster}')
    dadj = db.mod.dadj.copy(deep=True)
    cmask = np.equal(db.mod.clusters.values, cluster) # mask for cluster
    tdim = db.mod.ds.date.size # size of time dimension
    cmaskt = cmask[None,:,:].repeat(tdim,0) # match mod time dimension for filtering
    cval = db.mod.ds[modozkey].values[cmaskt] # only values in cluster, flattend
    oq = np.quantile(myobs['ozone'].values, QS, method='linear')
    mq1 = np.quantile(cval, QS, method='linear')
    dmq1 = np.diff(mq1)
    doq = np.diff(oq)
    rq1 = doq/dmq1
    mfx = interp1d(mq1,QS,kind='next') # function to map values to quantiles
    mqn = mfx(cval) # quantile of each value
    qfx = interp1d(QS,range(len(QS)),kind='next') # function to map quantile to indices of QS array
    qidxtmp = qfx(mqn) # quantile indices of each value
    qidx = np.where(qidxtmp==0,1,qidxtmp)-1 # adjusted for fencepost (get rid of 0)
    rqval = rq1[qidx.astype(int)] # ratio bin for each value
    mqval = mq1[qidx.astype(int)] # put each value in its quantile bin
    cjn = rqval*(cval-mqval) # pointwise correction to model vals (eq. 5)
    oqval = oq[qidx.astype(int)] # observation quantile bin based on model quantile
    madj = oqval + cjn # adjusted model values
    
    # fill xarray with correct values
    dadj.values[cmaskt] = madj
    return dadj # DataArray with cells in cluster adjusted



#def bias_correct_future(cfs, cfshist, cfshistraw, region, regmask=None, QS=None):
def bias_correct_future(db, cluster, QS, modozkey):
    '''
    Apply bias correction to projections based on ratio between historical/projection ozone.
    This maintains change in shape of the distribution while applying the correction.
    
    cfs = raw future values, xr.DataArray, shape of (time,lat,lon)
    cfshist = adj historical values, xr.DataArray, shape of (time,lat,lon)
    cfshistraw = raw historical values, xr.DataArray, shape of (time,lat,lon)
    region = string
    regmask = regmask array
    QS = quantile edges
    '''
    
    if QS is None:
        QS = np.arange(0,1.001,0.001)
    if db.modfut.dadj is None:
        db.modfut.setdadj(db.modfut.ds[modozkey].copy(deep=True))
        
    cfs = db.modfut.dadj.copy(deep=True)
    cfshist = db.mod.dadj.copy(deep=True)
    cfshistraw = db.mod.ds[modozkey].copy(deep=True)
    
    cmask = np.equal(db.mod.clusters.values, cluster) # mask for cluster
    tdim = db.modfut.ds.date.size # size of time dimension
    cmaskt = cmask[None,:,:].repeat(tdim,0) # match mod time dimension for filtering 
        
    cval = cfs.values[cmaskt]
    
    cvalhist = cfshist.values[cmaskt]
    
    cvalhistraw = cfshistraw.values[cmaskt]
    
    # differences between raw hist and projection at each quantile
    histrawq = np.quantile(cvalhistraw, QS, method='linear')
    mq = np.quantile(cval, QS, method='linear')
    dxq = mq / histrawq # eq. 7
    
    # add quantile differences to corrected hist distribution
    # should preserve dist shape, still need point correction
    histq = np.quantile(cvalhist, QS, method='linear') #adjusted historical dist quantiles
    mqadj = histq * dxq # eq. 8
    
    dmqadj = np.diff(mqadj) # bin sizes for future adjusted
    dmq = np.diff(mq) # bin sizes for future raw
    rq1 = dmqadj/dmq # ratio
    mfx = interp1d(mq,QS,kind='next') # function to map values to quantiles
    mqn = mfx(cval) # quantile of each value
    qfx = interp1d(QS,range(len(QS)),kind='next') # function to map quantile to indices of QS array
    qidxtmp = qfx(mqn) # quantile indices of each value
    qidx = np.where(qidxtmp==0,1,qidxtmp)-1 # adjusted for fencepost (get rid of 0)
    rqval = rq1[qidx.astype(int)] # ratio bin for each value
    mqval = mq[qidx.astype(int)] # left quantile bin edge for each value
    cjn = rqval*(cval-mqval) # pointwise correction to model vals (eq. 10)
    mqadjval = mqadj[qidx.astype(int)] # observation quantile bin based on model quantile
    madj = mqadjval + cjn # adjusted model values
    
    # fill modvals xarray with correct values
    cfsadj = cfs.copy(deep=True)
    cfsadj.values[cmaskt] = madj
    return cfsadj
