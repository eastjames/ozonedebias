# main program

from ozonedebias import debiaser


# create debiaser instance
db = debiaser.Debiaser()

# create obs instance from existing file, now an attr of debiaser
db.assign_obs(mda8file='ozonedebias/data/castnet/castnet_mda8.csv')

# detrend castnet obs
db.obs.df = db.obs.detrendit()

# create mod instance, attr of debiaser
basedir '/mnt/raid2/Shared/climate_aq/cesm1_1_2/archive/prod/'
fpath = 'REF.CS30.IC1.1980-2010.runs/REF.CS30.IC1.1980-2010.2000/RESULTS.new/REF.CS30.IC1.1980-2010.2000.AQ.nc'
infile = basedir + fpath
db.assign_mod(file=infile)



