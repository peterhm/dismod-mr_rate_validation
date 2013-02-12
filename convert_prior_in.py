'''This module creates prior_in.csv for dismod_spline'''

import sys
sys.path += ['.', '..', '/homes/peterhm/gbd/', '/homes/peterhm/gbd/book'] 
import pylab as pl
import os
import pandas

import dismod3
reload(dismod3)

import model_utilities as mu
reload(mu)

def build_prior_in(dm3, data_type, model_num):
    # create prior_in csv with appropriate fields
    # create noise parameters
    prior_in = prior_noise(dm3, data_type)
    # create 'knot' from 'level bounds' and 'level values' 
    prior_in = prior_in.append(prior_level(dm3, data_type), ignore_index=True)
    # create 'dknot' from 'increasing' and 'decreasing'
    prior_in = prior_in.append(prior_direction(dm3, data_type), ignore_index=True)
    # create m_sub information
    prior_in = prior_in.append(prior_m_area(dm3, model_num, data_type), ignore_index=True)
    # create covariate prior information
    prior_in = prior_in.append(prior_cov(dm3, data_type), ignore_index=True)
    return prior_in

def empty_prior_in(ix):
    # create an emptry dataset 
    # with columns corresponding to the prior_in.csv
    # and an index of specified length
    return pandas.DataFrame(index=ix, columns=['type', 'name', 'lower', 'upper', 'mean', 'std'], dtype=object)

def prior_noise(dm3, data_type):
    prior_in = empty_prior_in(range(6))
    prior_in['type'] = 'noise'
    # create xi from smoothness (values from ism.py)
    smoothing_dict = {'No Prior':'inf', 'Slightly':.5, 'Moderately': .05, 'Very': .005}
    prior_in.ix[0,'name'] = 'xi'
    prior_in.ix[0,'std'] = 'inf'
    try:
        prior_in.ix[0,'mean'] = smoothing_dict[dm3.parameters[data_type]['smoothness']['amount']]
        prior_in.ix[0,'lower'] = smoothing_dict[dm3.parameters[data_type]['smoothness']['amount']]
        prior_in.ix[0,'upper'] = smoothing_dict[dm3.parameters[data_type]['smoothness']['amount']]
    except KeyError:
        prior_in.ix[0,'mean'] = smoothing_dict['No Prior']
        prior_in.ix[0,'lower'] = smoothing_dict['No Prior']
        prior_in.ix[0,'upper'] = smoothing_dict['No Prior']
    # create tau_zero from data heterogeneity
    hetero_dict = {'No Prior':'inf', 'Slightly':.05, 'Moderately': .05, 'Very': .05}
    prior_in.ix[1,'name'] = 'tau_zero'
    prior_in.ix[1,'mean'] = hetero_dict[dm3.parameters[data_type]['heterogeneity']]
    prior_in.ix[1,'std'] = 'inf'
    prior_in.ix[1,'lower'] = hetero_dict[dm3.parameters[data_type]['heterogeneity']]
    prior_in.ix[1,'upper'] = hetero_dict[dm3.parameters[data_type]['heterogeneity']]
    # create tau_one
    prior_in.ix[2,'name'] = 'tau_one'
    prior_in.ix[2,'mean'] = 0.
    prior_in.ix[2,'std'] = .25
    prior_in.ix[2,'lower'] = '-inf'
    prior_in.ix[2,'upper'] = 'inf'
    # create gamma_* priors
    prior_in.ix[3,'name'] = 'gamma_sub'
    prior_in.ix[4,'name'] = 'gamma_region'
    prior_in.ix[5,'name'] = 'gamma_super'
    prior_in.ix[3:5,'mean'] = .05
    prior_in.ix[3:5,'std'] = .03
    prior_in.ix[3:5,'lower'] = .05
    prior_in.ix[3:5,'upper'] = .5
    return prior_in
    
def prior_level(dm3, data_type):
    # create 'knot' from 'level bounds' and 'level values' 
    prior_in = empty_prior_in(range(len(dm3.parameters[data_type]['parameter_age_mesh'])))
    # fill non-age-dependent variables
    prior_in['type'] = 'knot'
    prior_in['name'] = dm3.parameters[data_type]['parameter_age_mesh']
    prior_in['lower'] = dm3.parameters[data_type]['level_bounds']['lower']
    prior_in['upper'] = dm3.parameters[data_type]['level_bounds']['upper']
    prior_in['std'] = 'inf'
    # fill age-dependent variables (mean)
    for i,a in enumerate(dm3.parameters[data_type]['parameter_age_mesh']):
        if dm3.parameters[data_type]['level_value']['age_before'] < dm3.parameters[data_type]['level_value']['age_after']:
            if (a < dm3.parameters[data_type]['level_value']['age_before']) | (a >= dm3.parameters[data_type]['level_value']['age_after']):
                prior_in.ix[i,'mean'] = dm3.parameters[data_type]['level_value']['value']
        elif dm3.parameters[data_type]['level_value']['age_before'] > dm3.parameters[data_type]['level_value']['age_after']:
            if (a < dm3.parameters[data_type]['level_value']['age_before']) & (a >= dm3.parameters[data_type]['level_value']['age_after']):
                prior_in.ix[i,'mean'] = dm3.parameters[data_type]['level_value']['value']
    # fill remaining mean values 
    prior_in['mean'] = prior_in['mean'].fillna([pl.mean(dm3.get_data(data_type)['value'])])
    return prior_in
    
def prior_direction(dm3, data_type):
    # create 'dknot' from 'increasing' and 'decreasing'
    # note: it is required to have the final age_mesh point missing
    prior_in = empty_prior_in(range(len(dm3.parameters[data_type]['parameter_age_mesh'][:-1])))
    # fill non-age-dependent variables
    prior_in['type'] = 'dknot'
    prior_in['name'] = dm3.parameters[data_type]['parameter_age_mesh'][:-1]
    prior_in['std'] = 'inf'
    if dm3.parameters[data_type]['increasing']['age_start'] !=  dm3.parameters[data_type]['increasing']['age_end']:
        for i,a in enumerate(dm3.parameters[data_type]['parameter_age_mesh'][:-1]):
            if (dm3.parameters[data_type]['increasing']['age_start'] <= a < dm3.parameters[data_type]['increasing']['age_end']):
                prior_in.ix[i,'lower'] = 0.
                prior_in.ix[i,'upper'] = 'inf'
                prior_in.ix[i,'mean'] = 1.
    if dm3.parameters[data_type]['decreasing']['age_start'] !=  dm3.parameters[data_type]['decreasing']['age_end']:
        for i,a in enumerate(dm3.parameters[data_type]['parameter_age_mesh'][:-1]):
            if (dm3.parameters[data_type]['decreasing']['age_start'] <= a < dm3.parameters[data_type]['decreasing']['age_end']):
                prior_in.ix[i,'lower'] = '-inf'
                prior_in.ix[i,'upper'] = 0.
                prior_in.ix[i,'mean'] = -1.
    prior_in['lower'] = prior_in['lower'].fillna('-inf')
    prior_in['upper'] = prior_in['upper'].fillna('inf')
    prior_in['mean'] = prior_in['mean'].fillna(0.)
    return prior_in    
    
def prior_m_area(dm3, model_num, data_type):
    # create 'm_sub'/'m_region' from unique input_data['area']
    prior_in = empty_prior_in(pl.unique(dm3.input_data['area']).index)
    prior_in['name'] = pl.unique(dm3.input_data['area'])
    prior_in['mean'] = 0.
    prior_in['std'] = 1.
    prior_in['lower'] = '-inf'
    prior_in['upper'] = 'inf'
    # create hierarchy
    model = mu.load_new_model(model_num, 'all', data_type)
    superregion = set(model.hierarchy.neighbors('all'))
    region = set(pl.flatten([model.hierarchy.neighbors(sr) for sr in model.hierarchy.neighbors('all')]))
    country = set(pl.flatten([[model.hierarchy.neighbors(r) for r in model.hierarchy.neighbors(sr)] for sr in model.hierarchy.neighbors('all')]))
    # create data area levels
    for i in pl.unique(dm3.input_data['area']).index:
        if dm3.input_data.ix[i,'area'] in country:
            prior_in.ix[i,'type'] = 'm_sub'
        elif dm3.input_data.ix[i,'area'] in region:
            prior_in.ix[i,'type'] = 'm_region'
        elif dm3.input_data.ix[i,'area'] in superregion:
            prior_in.ix[i,'type'] = 'm_super'
    return prior_in
    
def prior_cov(dm3, data_type):
    # define covariates in model
    cov = list(dm3.input_data.filter(like='x_').columns)
    cov.append('x_sex')
    prior_in = empty_prior_in(range(len(cov)))
    prior_in['type'] = 'cov'
    for i,c in enumerate(cov):
        prior_in.ix[i,'name'] = c
        try:
            prior_in.ix[i,'mean'] = dm3.parameters[data_type]['fixed_effects'][c]['mu']
            prior_in.ix[i,'std'] = dm3.parameters[data_type]['fixed_effects'][c]['sigma']
            prior_in['lower'] = '-inf'
            prior_in['upper'] = 'inf'
        except KeyError:
            prior_in['mean'] = 0.
            prior_in['std'] = 1.
            prior_in['lower'] = '-inf'
            prior_in['upper'] = 'inf'
    return prior_in



