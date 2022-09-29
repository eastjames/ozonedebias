# main program

from .obs import castnet

castnet.get_castnet() # check for file and download if needed
df = castnet.openclean_castnet(yearlim=(1980,2010))
df = (
    df.pipe(castnet.tomda8)
    .pipe(castnet.pair_sites)
    .pipe(castnet.detrendit)
)

# open model file(s)? with xarray

# clip