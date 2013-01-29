import sys
sys.path += ['.', '..', '/homes/peterhm/gbd/', '/homes/peterhm/gbd/book'] 
import pylab as pl
import os
import pandas

import dismod3
reload(dismod3)

import model_utilities as mu
reload(mu)

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
        prior_in = build_prior_in() # pandas.DataFrame(columns=['type', 'name', 'lower', 'upper', 'mean', 'std'])
        parameter_in = pandas.DataFrame(columns=['name','value'])
        #data_in.csv = ????
        #sample_out.csv = 
        info_out = pandas.DataFrame(columns=['name','value'])
    # return to working directory
    os.chdir('%s' %cwd)
    # return dataframes to add
    return prior_in, parameter_in, info_out

def empty_data_in(ix):
    return pandas.DataFrame(index=ix, columns=['integrand', 'meas_value', 'meas_stdev', 'sex', 'age_lower', 'age_upper', 'time_lower', 'time_upper', 'm_sub', 'm_region', 'm_super', 'x_sex'], dtype=object)
    
# def data_cov()
    
    
def build_data_in(dm3, data_type):
    # create data_in csv with appropriate fields
    data_in = data(dm3, data_type)
    data_in = data_in.append(data_area(dm3, data_type, model_num), ignore_index=True)
    return data_in

def data(dm3, data_type):
    # create data file
    data_in = empty_data_in(dm3.input_data.index)
    data_in['integrand'] = integrand[data_type]
    data_in['meas_value'] = dm3.input_data['value']
    data_in['sex'] = dm3.input_data['sex']
    data_in['age_lower'] = dm3.input_data['age_start']
    data_in['age_upper'] = dm3.input_data['age_end']
    data_in['time_lower'] = dm3.input_data['year_start']
    data_in['time_upper'] =  dm3.input_data['year_end']
    data_in['x_sex'] = dm3.input_data['sex'].map(dict(male=.5, female=-.5, total=0))
    # find standard error and use it for standard deviation
    dm3 = mu.create_uncertainty(dm3, 'log_normal')
    data_in['meas_stdev'] = dm3.input_data['standard_error']
    return data_in

def data_area(dm3, data_type, model_num):
    # create data hierarchy
    model = mu.load_new_model(model_num, 'all', data_type)
    superregion = set(model.hierarchy.neighbors('all'))
    region = set(pl.flatten([model.hierarchy.neighbors(sr) for sr in model.hierarchy.neighbors('all')]))
    country = set(pl.flatten([[model.hierarchy.neighbors(r) for r in model.hierarchy.neighbors(sr)] for sr in model.hierarchy.neighbors('all')]))
    # create data area levels
    data_in = empty_data_in(dm3.input_data.index)
    for i in dm3.get_data(data_type).index:
        if dm3.input_data.ix[i,'area'] in country:
            data_in['m_sub'] = dm3.input_data.ix[i,'area']
            data_in['m_region'] = model.hierarchy.in_edges(dm3.input_data.ix[i,'area'])[0][0]
            data_in['m_super'] = model.hierarchy.in_edges(model.hierarchy.in_edges(dm3.input_data.ix[i,'area'])[0][0])[0][0]
        elif dm3.input_data.ix[i,'area'] in region:
            data_in['m_region'] = dm3.input_data.ix[i,'area']
            data_in['m_super'] = model.hierarchy.in_edges(dm3.input_data.ix[i,'area'])
        elif dm3.input_data.ix[i,'area'] in superregion:
            data_in['m_super'] = dm3.input_data.ix[i,'area']

def data_cov(dm3, data_type):
    return dm3

