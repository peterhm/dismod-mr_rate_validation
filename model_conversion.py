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

def build_param_in(dm3, thin, iter, replicate):
    param_in = pandas.DataFrame(index=range(9), columns=['name','value'], dtype=object)
    param_in.ix[0] = 'data_model','gaussian'
    param_in.ix[1] = 'parameter_model','gaussian'
    param_in.ix[2] = 'sample_interval', thin
    param_in.ix[3] = 'num_sample', thin*iter
    param_in.ix[4] = 'watch_interval',50
    param_in.ix[5] = 'random_seed',replicate
    # find eta and zeta values from data
    nonzeros = (dm3.input_data['value'] != 0)
    min_nonzero = min(dm3.input_data['value'][nonzeros])
    if min_nonzero < 1.:
        val = (min_nonzero)**2
    elif dm3.input_data['value'].mean() >= 1.:
        val = 1e-4 
    param_in.ix[6] = 'zeta',val
    param_in.ix[7] = 'eta',val
    # find z_ covariates
    if len(dm3.input_data.filter(like='z_').columns) == 1:
        param_in.ix[8] = 'tau_one_cov',dm3.input_data.filter(like='z_').columns[0]
    else:
        param_in.ix[8] = 'tau_one_cov',
    return param_in

def dm3rep_initialize(model_num, data_type, area, thin, iter, replicate, bare_bones=False):
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
    thin : int
      thinning number for MCMC
    iter : int
      number of iterations in MCMC
    replicate : int
      number for random number
    bare_bones : bool
      True creates minimalist files, False uses DisMod-MR values, default set to False
    Results
    -------
    gets data and builds necessary files
    .. Note :: If bare_bones is False, parameter files must be filled.
    '''
    ds_loc = '/homes/peterhm/dismod_spline-20130115/build'
    cwd = os.getcwd()
    os.chdir('%s' %ds_loc)
    # creates necessary files
    if bare_bones == True: 
        # creates data
        os.system('bin/get_data.py %s' %model_num)
    else:
        # load data structure
        dm3 = mu.load_new_model(model_num, area, data_type)
        # create required files
        data_in = c_data.build_data_in(dm3, data_type, model_num)
        prior_in = c_prior.build_prior_in(dm3, data_type, model_num)
        parameter_in = build_param_in(dm3, thin, iter, replicate)
        # save files
        os.system('mkdir fit/%s' %model_num)
        data_in.to_csv(ds_loc + '/fit/%s/data_in.csv'%(model_num),index=False)
        prior_in.to_csv(ds_loc + '/fit/%s/prior_in.csv'%(model_num),index=False)
        parameter_in.to_csv(ds_loc + '/fit/%s/parameter_in.csv'%(model_num),index=False)
    # return to working directory
    os.chdir('%s' %cwd)
    

