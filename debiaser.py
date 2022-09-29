# a debiasing object
from .obs import ObsGetter, Castnet
from .model import ModelGetter, Camchem

class Debiaser
    '''
    A debias instance
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
            self.obs.check_file() # check the file conforms (empty for now)
        else:
            print('No obs assigned')
            
            
        # do more here? clean/get data?
        # what to do with the file?
        
        
        
    def assign_mod(self, kind = 'camchem', file = None):
        '''
        assign model data here...
        '''
        if kind == 'camchem':
            self.mod == Camchem()
        