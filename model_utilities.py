from __future__ import division
import sys
sys.path += ['.', '..', '/homes/peterhm/gbd/', '/homes/peterhm/gbd/book']
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

def test_train(model, data_type, replicate):
    ''' splits data into testing and training data sets 
    testing sets have effective sample size = 0 and standard error = inf
    returns the model, the test set indices and the test set indices of the test set
    Parameters
    ----------
    model : data.ModelData
      dismod model
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
    ix = list(model.input_data.index)
    withhold = int(len(model.input_data.index)/4)
    test_ix = random.sample(ix, withhold)
    # change effective sample size and standard error of random selection
    model.input_data.ix[test_ix, 'effective_sample_size'] = 0
    model.input_data.ix[test_ix, 'standard_error'] = pl.inf
    return model, test_ix

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
    # find indices that contain nan for effective sample size 
    nan_ix = list(model.input_data['effective_sample_size'][pl.isnan(model.input_data['effective_sample_size'])==1].index)
    non_nan_ix = list(model.input_data['effective_sample_size'][pl.isnan(model.input_data['effective_sample_size'])==0].index)
    # find effective sample size of entire dataset
    percent = pl.percentile(model.input_data.ix[non_nan_ix,'effective_sample_size'], 10.)
    # replace nan effective sample size with 10th percentile 
    model.input_data.ix[nan_ix, 'effective_sample_size'] = percent
    
    # find indices that are negative for standard error and
    # calculate standard error from effective sample size 
    if (rate_type == 'normal') | (rate_type == 'log_normal'): 
        neg_ix = list(model.input_data['standard_error'][model.input_data['standard_error']<0].index)
        for i,ix in enumerate(neg_ix):
            model.input_data['standard_error'][ix] = pl.sqrt(model.input_data.ix[ix, 'value']*(1-model.input_data.ix[ix, 'value'])/model.input_data.ix[ix, 'effective_sample_size'])

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

    