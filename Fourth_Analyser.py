'''
This script will read a csv file containing a table that contains all the shifts.

It will create a time series table to that show the number of Employees in each hour of the day.
There are 4 columns that are very important at this stage:
- site_code
- departments
- Start Time 1
- End Time 1
- Start time 2
- End time 2

'''
import time
import streamlit as st

import pandas as pd
# re write 
columns = [
    'Home',
    #'Cost code',
    'Division',
    #'Job Grade',
    'Job Title',
    #'Pay Rate',
    #'Employee Number',
    'First Name',
    'Surname',
    #'Contract',
    'Shift date',
    'Day of the week',
    'Rota/Forecast StartTime1',
    'Rota/Forecast StopTime1',
    'Rota/Forecast StartTime2',
    'Rota/Forecast StopTime2',
    'Rota/Forecast Hours',
    'Paid/Actual StartTime1',
    'Paid/Actual StopTime1',
    'Paid/Actual StartTime2',
    'Paid/Actual StopTime2',
    'Paid/Actual Hours',
    'Worked/T&A StartTime1',
    'Worked/T&A StopTime1',
    'Worked/T&A StartTime2',
    'Worked/T&A StopTime2',
    'Worked/T&A Hours',
    'Contracted Hours'

]
def lambda_for_times(value_):
    '''
    This method will modify the times in the columns to be in the format of hh:mm
    It will be used for each for the Start Time 1, End Time 1, Start Time 2, End Time 2
    '''
    value_ = str(value_)
    if len(value_) == 4:
        value_ = value_[:2] + ':' + value_[2:]
    elif len(value_) == 3:
        value_ = value_[:1] + ':' + value_[1:]
    elif len(value_) == 2:
        value_ = '00:' + value_
    elif len(value_) == 1:
        value_ = '00:0' + value_
    return value_

class FourthData:
    """
    """

    def __init__(self, path):
        self.columns_hours = None
        try:
            self.path = path
            # LOOK AT THE FOLDER
            # TAKE ALL CSV FILES AND PUT THEM IN A LIST
            # CONCATENATE THEM TO ONE DATAFRAME -> DONE
            self.df = pd.read_csv(self.path)
            self.df = self.transform()
        except Exception as exception:
            raise exception

    def cleaning(self):
        '''
        This method will clean the data, drop useless columns and add new columns for Month and Day
        '''
        # drop the columns that are not needed
        self.df = self.df[columns]
        # take off duplicate rows
        self.df.drop_duplicates(inplace=True)
        all_department = self.df['Division'].unique()
        #st.write('All Departments', all_department)
        deps_ = [
                #'FOH Management',
                #'BOH Managers',
                'Expeditor',
                'Servers',
                #'BOH - Senior Chef De Partie',
                #'BOH - Chef De Partie',
                'Hosts',
                'FOH Dev Training',
                'Bartenders',
                #'BOH - Demi Chef De Partie',
                'Bar Support',
                'Food and drinks Runners',
                #'Dishoom at Home - Bar',
                'Cocktail Servers',
                #'Dishoom at Home',
                'FOH training',
                #'BOH Training'
        ]
        # GET ALL restaurant names
        restaurants = self.df['Home'].unique()
        restaurants = [
        'Dishoom Covent Garden',
        'Dishoom Shoreditch',
        'Dishoom Kensington',
        'Dishoom Kings Cross',
        'Dishoom Carnaby',
        'Dishoom Manchester',
        'Dishoom Edinburgh',
        'Dishoom Birmingham',
        #'Dishoom Park Royal - Prep',
        #'Dishoom Islington',
        'Dishoom Canary Wharf',
        #'Dishoom Crouch End',
        #'Dishoom Cambridge',
        #'Dishoom Dulwich',
        #'Dishoom Battersea',
        #'Dishoom Whitechapel',
        #'Dishoom Swiss Cottage',
        #'Dishoom Canning Town',
        #'Dishoom Acton',
        #'Dishoom Brighton',
        #'Dishoom Bermondsey',
        #'Dishoom Wandsworth'
        ]
        # keep only the restaurants that are in the list
        self.df = self.df.loc[self.df['Home'].isin(restaurants)]
        #st.write('All Restaurants', restaurants)

        # take off rows that are not in the departments list
        self.df = self.df.loc[self.df['Division'].isin(deps_)]
        # take off rows that have no data in Start Time 1 and End Time 1
        self.df.dropna(subset=['Paid/Actual StartTime1', 'Paid/Actual StopTime1',
                               'Paid/Actual StartTime2', 'Paid/Actual StopTime2'],
                       inplace=True)
        # drop the columns that are not needed "Job Grade"
        # add month from shift date after converting to datetime
        self.df['Month'] = pd.to_datetime(self.df['Shift date'], dayfirst=True).dt.month
        # add day from shift date after converting to datetime
        self.df['Day'] = pd.to_datetime(self.df['Shift date'], dayfirst=True).dt.day
        return self.df
    
    def transformation_0(self):
        '''
        Here we re-format the times in the columns of (start1, start2, end1, end2)
        We create a new columns for each of them keeping the hour value
        '''
        # Apply the lambda function to the columns that need to be reformatted
        self.df['Paid/Actual StartTime1'] = self.df['Paid/Actual StartTime1'] \
            .apply(lambda_for_times)
        self.df['Paid/Actual StopTime1'] = self.df['Paid/Actual StopTime1'] \
            .apply(lambda_for_times)
        self.df['Paid/Actual StartTime2'] = self.df['Paid/Actual StartTime2'] \
            .apply(lambda_for_times)
        self.df['Paid/Actual StopTime2'] = self.df['Paid/Actual StopTime2'] \
            .apply(lambda_for_times)
        # Add new columns for the hours
        self.df['HourStart'] = self.df['Paid/Actual StartTime1'] \
            .apply(lambda x: int(x.split(':')[0]))
        self.df['HourEnd'] = self.df['Paid/Actual StopTime1'] \
            .apply(lambda x: int(x.split(':')[0]))
        self.df['HourStart2'] = self.df['Paid/Actual StartTime2'] \
            .apply(lambda x: int(x.split(':')[0]))
        self.df['HourEnd2'] = self.df['Paid/Actual StopTime2'] \
            .apply(lambda x: int(x.split(':')[0]))

        # if hour is smaller than 5 then we need to add 24 to it
        self.df.loc[self.df['HourStart'] < 5, 'HourStart'] = self.df['HourStart'] + 24
        self.df.loc[self.df['HourEnd'] < 5, 'HourEnd'] = self.df['HourEnd'] + 24

        if self.df['HourStart2'].astype(str).str != '0':
            self.df.loc[self.df['HourStart2'] < 5, 'HourStart2'] = self.df['HourStart2'] + 24
            self.df.loc[self.df['HourEnd2'] < 5, 'HourEnd2'] = self.df['HourEnd2'] + 24
        else:
            self.df['HourStart2'] = None
            self.df['HourEnd2'] = None

        # if the both start and end are equals then are None
        self.df.loc[self.df['HourStart'] == self.df['HourEnd'], ['HourStart', 'HourEnd']] = [None, None]
        self.df.loc[self.df['HourStart2'] == self.df['HourEnd2'], ['HourStart2', 'HourEnd2']] = [None, None]
        return self.df

    def transformation_1(self):
        '''
        In this transformation we will check the hours that are in the range of the shift
        '''
        # create a set of columns that will be used to create the new table
        self.columns_hours = range(5, 28) # from
        # add columns to the original table
        for hour in self.columns_hours:
            self.df[hour] = 0
            self.df.loc[(self.df['HourStart'] <= hour) & (self.df['HourEnd'] >= hour), hour] = 1
            # now check the second shift - start 2 need to be bigger than 0
            self.df.loc[(self.df['HourStart2'] <= hour) & (self.df['HourEnd2'] >= hour), hour] = 1 
            # if the the hour is > than hour End then we need to make it 0
            self.df.loc[self.df['HourEnd2'] < hour, hour] = 0
        return self.df
    
    def transformation_2(self):
        '''
        '''        
        # data_with_breaks the ones that the hours worked are at least 6
        peak_times = [12, 13, 14, 18, 19, 20, 21]
        allowed_hours = [8, 9, 10, 11, 15, 16, 17, 22, 23, 24]
        data_with_breaks = self.df.loc[self.df['HourEnd'] - self.df['HourStart'] >= 6]
        # data_without_breaks the ones that the hours worked are less than 6
        data_without_breaks = self.df.loc[self.df['HourEnd'] - self.df['HourStart'] < 6]

        # create a break column and initialize it with the middle point between the start and end time
        data_with_breaks['Break'] = (data_with_breaks['HourEnd'] + data_with_breaks['HourStart']) // 2
        # check if the break time is in the peak time
        # get closest hour from allowed hours
        data_with_breaks.loc[data_with_breaks['Break'].isin(peak_times), 'Break'] = data_with_breaks['Break'] \
            .apply(lambda x: min(allowed_hours, key=lambda y: abs(y - x)))

        # now get the hour inside the break column and make that column value 0.66
        for hour in self.columns_hours:
            data_with_breaks.loc[data_with_breaks['Break'] == hour, hour] = 0.66   
        # merge the two dataframes
        df = pd.concat([data_with_breaks, data_without_breaks])     
        return df
            
    def transform(self, verbose = False):
        '''
        Here we call the transformations
        '''
        start = time.time()
        data = self.cleaning()
        data = self.transformation_0()
        data = self.transformation_1()
        #data = self.transformation_2()
        end = time.time()
        if verbose:
            print(f"Transformed data in {end - start} seconds")
        return  data
    