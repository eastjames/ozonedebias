# ozonedebias

Quantile-mapping ozone de-biasing in a CTM with surface observations, over the U.S. Clusters sites and observations using Kmeans clustering and applies bias correction in clusters.


### Currently available observation networks to use:
* CASTNET

### Currently available models to de-bias:
* CAM-Chem

### Simple use case
Download CASTNET data and cluster
```python
from ozonedebias import debiaser, modgetter, obsgetter

castnet = obsgetter.Castnet()
castnet.get_castnet() # download obs
castnet.open_clean_castnet() # open and clean
castnet.tomda8() # transform hourly to mda8
castnet.pair_sites() # pair site data

# save to csv:
castnet.df.to_csv('path/to/file/castnet_mda8.csv')

db = debiaser.Debiaser() # instantiate debiaser object

# assign obs from mda8 file
db.assign_obs(mda8file='~/ozonedebias/data/castnet/castnet_mda8.csv')

# alternatively, skip Castnet object step and simply:
db.assign_obs(kind = 'castnet') # this will download castnet if needed

# instantiate Camchem object, must have required vars 
mf = modgetter.Camchem('path/to/camchem/files/file.nc') # can also supply list of files

# assign mod data to debiaser from existing object
db.mod_from_existing(mf)

# or, assign directly from file(s)
db.assign_mod(kind = 'camchem', file = 'path/to/camchem/files/file.nc')

# for U.S. mask
db.mod.make_nca_region_mask()

# Apply Kmeans clustering to obs
clusterby = ['ozone','i','j']
db.cluster_obs(
    toyear = 2000,
    clusterby = clusterby,
    shuffledata = False,
    samplefrac = 1,
    n_clusters = 6 # you must choose
)

# Sort model grid cells to obs clusters based on same criteria
# using scikit-learn NearestCentroid
db.cluster_mod(
    clusterby
)

# apply quantile mapping bias correction
db.corrector()

# Now access observations
db.obs.df

# gridded, bias corrected fields
db.mod.dadj

# gridded original data
db.mod.ds

# obs clusters
db.obs.clusterdf

# gridded model clusters
db.mod.clusters

```

### What's here?

```
ozonedebias
|
`--- models/
|    |
|    `---camchem.py # not used right now
|
`--- obs/
|    |
|    `---castnet.py # not used right now
|
`--- data/
|    |
|    `--- castnet/ # data stored
|    |
|    `--- masks/ # region masks, just U.S. right now
|   
`--- debiaser.py # Debiaser class
|   
`--- obsgetter.py # Obsgetter and Castnet classes
|   
`--- modgetter.py # Modgetter and Camchem classes
|   
`--- clustering.py # clustering helper functions
|
`--- debias.py # debiasing helper functions
|
`--- detrend.py # detrending helper functions
|
`--- test.py # not used right now


```

