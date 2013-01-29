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

def build_prior_in(dm3, data_type):
    # create prior_in csv with appropriate fields
    # create 'knot' from 'level bounds' and 'level values' 
    prior_in = prior_level(dm3, data_type)
    # create 'dknot' from 'increasing' and 'decreasing'
    prior_in = prior_in.append(prior_direction(dm3, data_type), ignore_index=True)
    return prior_in

def empty_prior_in(ix):
    # create an emptry dataset 
    # with columns corresponding to the prior_in.csv
    # and an index of specified length
    return pandas.DataFrame(index=ix, columns=['type', 'name', 'lower', 'upper', 'mean', 'std'], dtype=object)

def prior_level(dm3, data_type):
    # create 'knot' from 'level bounds' and 'level values' 
    prior_in = empty_prior_in(range(len(dm3.parameters[data_type]['parameter_age_mesh'])))
    # fill non-age-dependent variables
    prior_in['type'] = 'knot'
    prior_in['name'] = dm3.parameters[data_type]['parameter_age_mesh']
    prior_in['lower'] = dm3.parameters[data_type]['level_bounds']['lower']
    prior_in['upper'] = dm3.parameters[data_type]['level_bounds']['upper']
    prior_in['std'] = pl.inf
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
    prior_in['std'] = pl.inf
    if dm3.parameters[data_type]['increasing']['age_start'] !=  dm3.parameters[data_type]['increasing']['age_end']:
        for i,a in enumerate(dm3.parameters[data_type]['parameter_age_mesh'][:-1]):
            if (dm3.parameters[data_type]['increasing']['age_start'] <= a < dm3.parameters[data_type]['increasing']['age_end']):
                prior_in.ix[i,'lower'] = 0.
                prior_in.ix[i,'upper'] = pl.inf
                prior_in.ix[i,'mean'] = 1.
    if dm3.parameters[data_type]['decreasing']['age_start'] !=  dm3.parameters[data_type]['decreasing']['age_end']:
        for i,a in enumerate(dm3.parameters[data_type]['parameter_age_mesh'][:-1]):
            if (dm3.parameters[data_type]['decreasing']['age_start'] <= a < dm3.parameters[data_type]['decreasing']['age_end']):
                prior_in.ix[i,'lower'] = - pl.inf
                prior_in.ix[i,'upper'] = 0.
                prior_in.ix[i,'mean'] = -1.
    prior_in['lower'] = prior_in['lower'].fillna(-pl.inf)
    prior_in['upper'] = prior_in['upper'].fillna(pl.inf)
    prior_in['mean'] = prior_in['mean'].fillna(0.)
    return prior_in    
    
def prior_m_area(dm3):
    areas = dm3.hierarchy.node.keys()