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

integrand = {'p': 'prevalence', 
             'i': 'incidence', 
             'r': 'remission', 
             'f': 'r_excess', 
             'pf': 'r_prevalence', 
             'csmr': 'r_specific', 
             'm_all': 'r_all'
             'm_with': 'r_with'
             'm': 'r_other'
             'smr': 'r_standard', 
             'rr': 'relative_risk', 
             'X': 'duration'}

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
    if default == True: os.system('bin/fit.sh %s %s' %(model_num, integrand[data_type])) # creates brad's default files
    else:
        # load data structure
        dm3 = mu.load_new_model(model_num, area, data_type)
        # create required files
        prior_in = c_prior.build_prior_in() 
        parameter_in = pandas.DataFrame(columns=['name','value'])
        #data_in.csv = ????
        #sample_out.csv = 
        info_out = pandas.DataFrame(columns=['name','value'])
    # return to working directory
    os.chdir('%s' %cwd)
    # return dataframes to add
    return prior_in, parameter_in, info_out

