'''This module creates data_in.csv for dismod_spline'''

import sys
sys.path += ['.', '..', '/homes/peterhm/gbd/', '/homes/peterhm/gbd/book'] 
import pylab as pl
import os
import pandas

import dismod3
reload(dismod3)

import model_utilities as mu
reload(mu)

def convert_data_type(data_type):
    integrand = {'p': 'prevalence', 
                 'i': 'incidence', 
                 'r': 'remission', 
                 'f': 'r_excess', 
                 'pf': 'r_prevalence', 
                 'csmr': 'r_specific', 
                 'm_all': 'r_all',
                 'm_with': 'r_with',
                 'm': 'r_other',
                 'smr': 'r_standard', 
                 'rr': 'relative_risk', 
                 'X': 'duration'}
    return integrand[data_type]

def empty_data_in(ix):
    return pandas.DataFrame(index=ix, columns=['integrand', 'meas_value', 'meas_stdev', 'sex', 'age_lower', 'age_upper', 'time_lower', 'time_upper', 'm_sub', 'm_region', 'm_super', 'x_sex'], dtype=object)
    
def build_data_in(dm3, data_type, model_num):
    # find standard error and use it for standard deviation
    dm3 = mu.create_uncertainty(dm3, 'log_normal')
    # create data file
    data_in = empty_data_in(dm3.input_data.index)
    # add covariates
    cov = dm3.input_data.filter(like='x_')
    data_in = data_in.join(pandas.DataFrame(cov,columns=['']))
    cov_z = dm3.input_data.filter(like='z_')
    if len(cov_z.columns) != 0:
        data_in = data_in.join(pandas.DataFrame(cov_z,columns=['']))
    # add data
    data_in['integrand'] = convert_data_type(data_type)
    data_in['meas_value'] = dm3.input_data['value']
    data_in['meas_stdev'] = dm3.input_data['standard_error']
    data_in['sex'] = dm3.input_data['sex']
    data_in['age_lower'] = dm3.input_data['age_start']
    data_in['age_upper'] = dm3.input_data['age_end'] + 1.0
    data_in['time_lower'] = dm3.input_data['year_start']
    data_in['time_upper'] =  dm3.input_data['year_end'] + 1.0
    data_in['x_sex'] = dm3.input_data['sex'].map(dict(male=.5, female=-.5, total=0))
    # create data hierarchy
    model = mu.load_new_model(model_num, 'all', data_type)
    superregion = set(model.hierarchy.neighbors('all'))
    region = set(pl.flatten([model.hierarchy.neighbors(sr) for sr in model.hierarchy.neighbors('all')]))
    country = set(pl.flatten([[model.hierarchy.neighbors(r) for r in model.hierarchy.neighbors(sr)] for sr in model.hierarchy.neighbors('all')]))
    # create data area levels
    for i in dm3.input_data.index:
        if dm3.input_data.ix[i,'area'] in country:
            data_in.ix[i,'m_sub'] = dm3.input_data.ix[i,'area']
            data_in.ix[i,'m_region'] = model.hierarchy.in_edges(dm3.input_data.ix[i,'area'])[0][0]
            data_in.ix[i,'m_super'] = model.hierarchy.in_edges(model.hierarchy.in_edges(dm3.input_data.ix[i,'area'])[0][0])[0][0]
        elif dm3.input_data.ix[i,'area'] in region:
            data_in.ix[i,'m_region'] = dm3.input_data.ix[i,'area']
            data_in.ix[i,'m_super'] = model.hierarchy.in_edges(dm3.input_data.ix[i,'area'])[0][0]
        elif dm3.input_data.ix[i,'area'] in superregion:
            data_in.ix[i,'m_super'] = dm3.input_data.ix[i,'area']
    return data_in