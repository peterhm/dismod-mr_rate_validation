import sys
sys.path += ['.', '..', '/homes/peterhm/gbd/', '/homes/peterhm/gbd/book'] 
import pylab as pl
import os
import pandas

import dismod3
reload(dismod3)

import model_utilities as mu
reload(mu)

import convert_prior_in as c_prior
reload(c_prior)
import convert_data_in as c_data
reload(c_data)



def dm3rep_initialize(model_num, data_type, area, default=False):
    '''
    Parameters
    ----------
    model_num : int
      dismod model number
    data_type : str
      one of the epidemiologic parameters allowed
      'p', 'i', 'r', 'f', 'pf', 'csmr', 'rr', 'smr', 'X'
    area : str
      level of heirarchy to keep
    default : bool
      True creates minimalist files, False uses DisMod-MR values, default set to False
    Results
    -------
    gets data and builds necessary files
    .. Note :: If default is False, parameter files must be filled.
    '''
    cwd = os.getcwd()
    os.chdir('/homes/peterhm/dismod_spline-20130115/build')
    # creates data
    os.system('bin/get_data.py %s' %model_num)
    # creates necessary files
    if default == True: os.system('bin/fit.sh %s %s' %(model_num, c_data.convert_data_type(data_type))) # creates brad's default files
    else:
        # load data structure
        dm3 = mu.load_new_model(model_num, area, data_type)
        # create required files
        prior_in = c_prior.build_prior_in(dm3, data_type, model_num)
        #prior_in.to_csv()
        parameter_in = pandas.DataFrame(columns=['name','value'])
        data_in = c_data.build_data_in(dm3, data_type, model_num)
        data_in.to_csv('/homes/peterhm/dismod_spline-20130115/data/dm-%s'%(model_num))
        #sample_out.csv = 
        info_out = pandas.DataFrame(columns=['name','value'])
    # return to working directory
    os.chdir('%s' %cwd)
    # return dataframes to add
    return prior_in, parameter_in, info_out

