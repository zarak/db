# -*- coding: utf-8 -*-
"""Prototype for central database in PonyORM."""

from pprint import pprint

from pony import orm
import pandas as pd



#the design

# better be a class?
def get_parser_result(parser_param):
    pass

# database PUT method
def to_database(datapoints):
    pass

# database GET method
def from_database(query_dict):
    pass

def as_user_json(result_dict):
    pass

# write into database
parser_param_1 = dict()
parser_result_1 = get_parser_result(parser_param_1)
to_database(parser_result_1)

# read from database
user_query = dict()
reponse = as_user_json(from_database(user_query))




# boilerplate

db = orm.Database()
db.bind(provider='sqlite', filename=':memory:')

class Datapoint(db.Entity):
     freq = orm.Required(str)
     name = orm.Required(str)     
     date = orm.Required(str)
     value = orm.Required(float)  
     # TODO: make unique key freq, name, date 
     # orm.PrimaryKey(freq, name, date)
     
db.generate_mapping(create_tables=True)

orm.sql_debug(False)

# read from database




# Example setup - mimics state of database before parser import 
with orm.db_session:
     x = Datapoint(date="2014-03-31", freq='q', name="CPI_rog", value=102.3)
     # this datapoint will overlap:
     x = Datapoint(date="2017-03-16", freq='d', name="BRENT", value=50.56)
     # later: things get worse when value is not 50.56 (a revision)

# 1. Import data from parser
# --------------------------

class ParserCaller:    
    """Parent class to get parsing result from individual parser."""
    
    supported_frequencies = 'aqmd' #must overload this 
    supported_variables = ['BRENT'] #must overload this 
    
    # may be properties
    # must overload this 
    @property
    def varnames(self):
        return ['BRENT']      
    
    @property 
    def frequencies(self):
        return ['d']
    
    @property
    def start_date(self):
        return '1999-01-01'

    @property
    def end_date(self):
        return 'today'
    
    def pure_get_data(self, freq, varnames, start, end):
        """Yield ditionaries with datapoints"""
        
        brent = [("2017-03-16", 50.56),
                 ("2017-03-17", 50.58),
                 ("2017-03-20", 50.67)]   
    
        for date, value in brent:
            yield {"date": date,
                   "freq": "d",
                   "name": "BRENT",
                   "value": value}            
    
    def get_data(self, freq, varnames, start=None):
        assert freq in self.frequencies
        for vn in varnames:
            assert varnames in self.varnames
        if start is None:
            start = self.start_date
        end = 'it should be today'    
        return self.pure_get_data(freq, varnames, start, end)
      

def mock_parser_output_2():   

    brent = [("2017-03-16", 50.56),
             ("2017-03-17", 50.58),
             ("2017-03-20", 50.67)]   
    
    for date, value in brent:
        yield {"date": date,
               "freq": "d",
               "name": "BRENT",
               "value": value}
    

def mock_parser_output_1():   
    
    yield {"date": "2015-11-30",
        "freq": "m",
        "name": "CPI_rog",
        "value": 100.8}
    
    yield {"date": "2015-11-30",
        "freq": "m",
        "name": "RUR_EUR_eop",
        "value": 70.39}
    
    yield {"date": "2015-12-31",
        "freq": "m",
        "name": "CPI_rog",
        "value": 100.8}
    
    yield {"date": "2015-12-31",
        "freq": "m",
        "name": "RUR_EUR_eop",
        "value": 79.7}
    
    
# put parcer data inside the database
with orm.db_session:
    for mock_output in [mock_parser_output_1, mock_parser_output_2]: 
        for x in mock_output():
            dp = Datapoint(**x)
        

# 2. Query database
# -----------------
 
user_query = dict(varnames=['CPI_rog', 'RUR_EUR_eop'],  freq='m')
print("\nQuery:", user_query)

@orm.db_session
def query_db(user_query):
    sel = orm.select((p.name, p.date, p.value) for p in Datapoint
                     if p.name in user_query['varnames'] and
                        p.freq==user_query['freq'])

    def as_dict(name, date, value):
        return dict(name=name, date=date, value=value)  

    for tup in sel:
        yield(as_dict(*tup))

print("\nRaw result:")
for d in query_db(user_query):
    print(d)

# make dataframe from records
df = pd.DataFrame(query_db(user_query))
df.date = pd.to_datetime(df.date)        
df = df.pivot(columns='name', values='value', index='date')

# save to json  - using pandas is slow, but this quarantees proper format
df_json = df.to_json()


# 3. User result
# --------------

# user reads json
user_df = pd.read_json(df_json)

# json read properly
ref_df = pd.DataFrame({'CPI_rog': [100.8, 100.8], 'RUR_EUR_eop': [70.39, 79.7]})
ref_df.index =  pd.DatetimeIndex(['2015-11-30', '2015-12-31'])
assert user_df.equals(ref_df)
        
        
# Screen after 
with orm.db_session:    
    res = orm.select((p.name, p.freq, p.date, p.value) for p in Datapoint)[:]
pprint(res)
    
