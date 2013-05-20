from __future__ import division
import sys
sys.path += ['.', '..', '/homes/peterhm/gbd/', '/homes/peterhm/gbd/book', '/homes/abie/gbd_dev/gbd/']
import pylab as pl
import pymc as mc
import pandas
import random

import dismod3
reload(dismod3)

def load_new_model(num, area, data_type):
    ''' opens and loads a dismod model number and returns data from Western Europe
    Parameters
    ----------
    num : int
      dismod model number
    area : str
      geographic area that corresponds to dismod3/GBD 2010 hierarchy
    data_type : str
      one of the epidemiologic parameters allowed
      'p', 'i', 'r', 'f', 'pf', 'csmr', 'rr', 'smr', 'X'
    Results
    -------
    model : data.ModelData
      dismod model
    '''
    model = dismod3.data.load('/home/j/Project/dismod/output/dm-%s'%num) 
    model.keep(areas=[area])
    model.input_data = model.get_data(data_type)
    return model

def test_train(data, data_type, rate_type, replicate):
    ''' splits data into testing and training data sets 
    testing sets have effective sample size = 0 and standard error = inf
    returns the model, the test set indices and the test set indices of the test set
    Parameters
    ----------
    data : pandas dataframe
      dataframe of data
    data_type : str
      one of the epidemiologic parameters allowed
      'p', 'i', 'r', 'f', 'pf', 'csmr', 'rr', 'smr', 'X'
    replicate : int
      integer to be added to the seed
    Results
    -------
    model : data.ModelData
      model with testing set that has effective sample size = 0 and standard error = inf
    test_ix : list
      list of indices that correspond to the test data
    '''
    # save seed
    random.seed(1234567 + replicate)
    # choose random selection (25%) of data
    ix = list(data.index)
    withhold = int(len(data.index)/4)
    test_ix = random.sample(ix, withhold)
    if rate_type == 'log_offset':
        # change standard error of random selection
        data.ix[test_ix, 'meas_stdev'] = pl.inf
    else:
        # change effective sample size and standard error of random selection
        data.ix[test_ix, 'effective_sample_size'] = 0
        data.ix[test_ix, 'standard_error'] = pl.inf
    return data, test_ix

def create_uncertainty(model, rate_type):
    '''data without valid uncertainty is given the 10% uncertainty of the data set
    Parameters
    ----------
    model : data.ModelData
      dismod model
    rate_type : str
      a rate model
      'neg_binom', 'binom', 'normal', 'log_norm', 'poisson', 'beta'
    Results
    -------
    model : data.ModelData
      dismod model with measurements of uncertainty for all data
    '''
    # fill any missing covariate data with 0s
    for cv in list(model.input_data.filter(like='x_').columns):
        model.input_data[cv] = model.input_data[cv].fillna([0])
    
    # find indices that are negative for standard error and
    # calculate standard error from effective sample size 
    missing_se = pl.isnan(model.input_data['standard_error']) | (model.input_data['standard_error'] < 0)
    if True in set(missing_se):
        model.input_data['standard_error'][missing_se] = (model.input_data['upper_ci'][missing_se] - model.input_data['lower_ci'][missing_se]) / (2*1.96)
        missing_se_still = pl.isnan(model.input_data['standard_error']) | (model.input_data['standard_error'] < 0)
        if True in set(missing_se_still):
            model.input_data['standard_error'][missing_se_still] = pl.sqrt(model.input_data['value'][missing_se_still]*(1-model.input_data['value'][missing_se_still])/model.input_data['effective_sample_size'][missing_se_still])

    # find indices that contain nan for effective sample size 
    missing_ess = pl.isnan(model.input_data['effective_sample_size'])==1  
    # calculate effective sample size from standard error
    model.input_data['effective_sample_size'][missing_ess] = model.input_data['value'][missing_ess]*(1-model.input_data['value'][missing_ess])/(model.input_data['standard_error'][missing_ess])**2
    
    # find effective sample size of entire dataset
    non_missing_ess_still = pl.isnan(model.input_data['effective_sample_size'])==0 # finds all real numbers
    if False in non_missing_ess_still: 
        percent = pl.percentile(model.input_data['effective_sample_size'][non_missing_ess_still], 10.)
        missing_ess_still = pl.isnan(model.input_data['effective_sample_size'])==1 # finds all nan 
        # replace nan effective sample size with 10th percentile 
        model.input_data['effective_sample_size'][missing_ess_still] = percent
    
    # change values of 0 in lognormal model to 1 observation
    if rate_type == 'log_normal':
        # find indices where values are 0
        zero_val = (model.input_data['value'] == 0)
        # add 1 observation so no values are zero, also change effective sample size
        model.input_data['effective_sample_size'][zero_val] = model.input_data['effective_sample_size'][zero_val] + 1
        model.input_data['value'][zero_val] = 1.0/model.input_data['effective_sample_size'][zero_val]
        # update standard error
        model.input_data['standard_error'][zero_val] = pl.sqrt(model.input_data['value'][zero_val]*(1-model.input_data['value'][zero_val])/model.input_data['effective_sample_size'][zero_val])    
    
    return model

def bias(pred, obs):
    ''' model bias
    Parameters
    ----------
    pred : df
      df of observations from model.vars[data_type]['p_pred'].stats()['mean']
    obs : df
      df of observations from model.vars[data_type]['p_obs'].value
    Results
    -------
    bias : float
      mean bias 
    '''
    pred = pl.array(pred['mean'])
    obs = pl.array(obs['value'])
    bias = pl.mean(obs - pred)
    return bias

def rmse(pred, obs):
    ''' model rmse
    Parameters
    ----------
    pred : df
      df of observations from model.vars[data_type]['p_pred'].stats()['mean']
    obs : df
      df of observations from model.vars[data_type]['p_obs'].value
    Results
    -------
    rmse : float
      mean rmse 
    '''
    n = len(obs.index)
    pred = pl.array(pred['mean'])
    obs = pl.array(obs['value'])    
    rmse = pl.sqrt(sum((obs - pred)**2)/n)
    return rmse
    
def mae(pred, obs):
    ''' model median absolute error
    Parameters
    ----------
    pred : df
      df of observations from model.vars[data_type]['p_pred'].stats()['mean']
    obs : df
      df of observations from model.vars[data_type]['p_obs'].value
    Results
    -------
    mae : float
      mean median absolute error 
    '''
    pred = pl.array(pred['mean'])
    obs = pl.array(obs['value'])    
    mae = pl.median(abs(pred - obs))
    return mae
    
def mare(pred, obs):
    ''' model median absolute relative error
    Parameters
    ----------
    pred : df
      df of observations from model.vars[data_type]['p_pred'].stats()['mean']
    obs : df
      df of observations from model.vars[data_type]['p_obs'].value
    Results
    -------
    mare : float
      mean median absolute relative error, as a percent
    '''
    pred = pl.array(pred['mean'])
    obs = pl.array(obs['value']) 
    mare = pl.median((abs(pred - obs)/obs)*100)
    return mare
    
def pc(pred_ui, obs):
    ''' probability of coverage
    Parameters
    ----------
    pred_ui : df
      df of observations from model.vars[data_type]['p_pred'].stats()['95% HPD interval']
    obs : df
      df of observations from model.vars[data_type]['p_obs'].value
    Results
    -------
    pc : float
      probability of coverage, as a percent 
    '''
    pred_ui = pl.array(pred_ui)
    obs = pl.array(obs['value'])    
    wi_ui = list((obs >= pred_ui[:,0]) & (obs <= pred_ui[:,1])).count(1)
    pc = (100*wi_ui)/len(obs)
    return pc

    