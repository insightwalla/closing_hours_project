import pandas as pd
import streamlit as st

def lambda_for_stop(x):
    '''
    This function is intended to be used with the apply method of a pandas dataframe
    It takes a row of a dataframe and returns a string with the date and the time
    '''
    # if the stop time is 00:00:00, then it means that the shift ended the next day
    # so we need to add 1 day to the date
    start = x['HourStart']
    end = x['HourEnd'] if x['HourEnd'] < 24 else x['HourEnd'] - 24
    if end < start:
        day = x['Shift date'] + pd.Timedelta(days=1)
    else:
        day = x['Shift date']
    return str(day.date()) + ' ' + str(x['Paid/Actual StopTime1'])

def lambda_for_start2(x):
    # if the start hour 2 is None, then merge it with the shift date
    if str(x['HourStart2']) != 'nan':
        return str(x['Shift date'].date()) + ' ' + str(x['Paid/Actual StartTime2'])
    else:
        return ''
    
def lambda_for_stop2(x):
    if str(x['HourEnd2']) != 'nan':
        start = x['HourStart2']
        end = x['HourEnd2'] if x['HourEnd2'] < 24 else x['HourEnd2'] - 24
        if end < start:
            day = x['Shift date'] + pd.Timedelta(days=1)
        else:
            day = x['Shift date']
        return str(day.date()) + ' ' + str(x['Paid/Actual StopTime2'])
    else:
        return ''

def lambda_for_end_minutes(x):
    # check the valid finish time
    if str(x[f'Paid/Actual StopTime1']) != 'nan':
        return int(x[f'Paid/Actual StopTime1'].split(':')[1])
    else:
        return None
    
def lambda_for_end_minutes2(x):
    # check the valid finish time
    if str(x[f'Paid/Actual StopTime2']) != 'nan' and str(x[f'Paid/Actual StopTime2']) != '':
        return int(x[f'Paid/Actual StopTime2'].split(':')[1])
    else:
        return None
    
class Transformation:
    def __init__ (self, data):
        self.data = data

        res_to_check = [
            'Dishoom Shoreditch',
            'Dishoom Covent Garden',
            'Dishoom Kensington',
            'Dishoom Kings Cross',  
            'Dishoom Carnaby',
            'Dishoom Manchester',
            'Dishoom Edinburgh',
            'Dishoom Birmingham',
            'Dishoom Canary Wharf'
        ]
        res_to_rename = {
            'Dishoom Shoreditch': 'D2',
            'Dishoom Covent Garden': 'D1',
            'Dishoom Kensington': 'D6',
            'Dishoom Kings Cross': 'D3',
            'Dishoom Carnaby': 'D4',
            'Dishoom Manchester': 'D7',
            'Dishoom Edinburgh': 'D5',
            'Dishoom Birmingham': 'D8',
            'Dishoom Canary Wharf': 'D9'
        }
        columns_needed = [
            'Home',
            'Shift date',
            'HourStart',
            'HourEnd',
            'HourStart2',
            'HourEnd2',
            'Paid/Actual StartTime1',   
            'Paid/Actual StopTime1',
            'Paid/Actual StartTime2',
            'Paid/Actual StopTime2',
            'First Name',
            'Surname',
            'Division'
        ]
        self.data = self.data[self.data['Home'].isin(res_to_check)]
        # rename home column values to D1, D2, D3, D4, D5, D6, D7, D8, D9
        self.data['Home'] = self.data['Home'].map(res_to_rename)
        
    def tranformation_0(self):
        self.data['Shift date'] = pd.to_datetime(self.data['Shift date'], dayfirst=True)
        # add correct day of the week
        self.data['Day of the week'] = self.data['Shift date'].dt.day_name()
        # add correct closign time based on day of the week -> 23.00 for monday to thursday, 03.00 for friday to sunday
        group_1_closing_schema = {
            'Sunday': 23,
            'Monday': 23,
            'Tuesday': 23,
            'Wednesday': 23,
            'Thursday': 23,
            'Friday': 24,
            'Saturday': 24
        }
        group_2_closing_schema = {
            'Sunday': 23,
            'Monday': 23,
            'Tuesday': 23,
            'Wednesday': 23,
            'Thursday': 24,
            'Friday': 24,
            'Saturday': 24
        }
        group_3_closing_schema = {
            'Sunday': 23,
            'Monday': 23,
            'Tuesday': 23,
            'Wednesday': 23,
            'Thursday': 23,
            'Friday': 23,
            'Saturday': 23
        }

        # assign the closing time to the restaurant
        res_ = {
            'D1': group_1_closing_schema,
            'D2': group_2_closing_schema,
            'D3': group_2_closing_schema,
            'D4': group_1_closing_schema,
            'D5': group_1_closing_schema,
            'D6': group_3_closing_schema,
            'D7': group_1_closing_schema,
            'D8': group_1_closing_schema,
            'D9': group_1_closing_schema,
        }
        self.data['Closing time'] = self.data.apply(lambda x: res_[x['Home']][x['Day of the week']], axis=1)
        #self.data['Closing time'] = self.data['Day of the week'].apply(lambda x: 23 if x in ['Sunday','Monday', 'Tuesday', 'Wednesday'] else 24)
    
    def transformation_1(self):
        '''
        Here we are going to use our lambda functions to modify
        the shift start and end time to a datetime object
        '''
        # merge the times and the dates
        self.data['Paid/Actual StartTime1'] = self.data['Shift date'].astype(str) + ' ' + self.data['Paid/Actual StartTime1'].astype(str)
        self.data['Paid/Actual StopTime1'] = self.data.apply(lambda_for_stop, axis=1)
        self.data['Paid/Actual StartTime2'] = self.data.apply(lambda_for_start2, axis=1)
        self.data['Paid/Actual StopTime2'] = self.data.apply(lambda_for_stop2, axis=1)

    def transformation_2(self):
        '''
        Here we are going to create the end minute column and the finishing hour column,
        at the end we are goign to handle the transformation of the names
        '''
        # create a column with the finishing hour filline the nan of hourend2 with hourend all calling that column 'finishin_hour'
        self.data['finishing_hour'] = self.data['HourEnd2'].fillna(self.data['HourEnd'])
        # if finishing hour > 24 then subtract 24
        #self.data.loc[self.data['finishing_hour'] > 24, 'finishing_hour'] = self.data['finishing_hour'] - 24
        # 3. Create a new column with the names
        self.data['Name'] = self.data['First Name'] + ' ' + self.data['Surname'] 
        self.data.drop(['First Name', 'Surname'], axis=1, inplace=True)

        # create a column with the minute of the end time
        self.data['end_minute'] = self.data.apply(lambda_for_end_minutes, axis=1)
        self.data['end_minute_2'] = self.data.apply(lambda_for_end_minutes2, axis=1)
        self.data.loc[self.data['end_minute_2'].isnull(), 'end_minute_2'] = self.data['end_minute']
        self.data.drop(['end_minute'], axis=1, inplace=True)
        self.data.rename(columns={'end_minute_2': 'end_minute'}, inplace=True)

        # round end minute as 15, 30, 45, 0
        self.data['end_minute'] = self.data['end_minute'].apply(lambda x: 
                                                                    0 if x < 10 else \
                                                                    15 if x < 20 else \
                                                                    30 if x <= 37 else \
                                                                    45 if 38 < x < 60 else \
                                                                    0)

    def transformation_3(self):
        '''
        This is a central transformation, here we are going to create the columns
        for each hour in intervals of 15 minutes (22:00, 22:15, 22:30, 22:45)
        and populate them with 1 or 0 depending if the shift is in that hour.

        To do it we are going to 
        '''
        columns_hours = [22,23,24,25,26,27]
        for hour in columns_hours: 
            # process the hour
            col_new_1 = f'{hour}:00'
            col_new_2 = f'{hour}:15'
            col_new_3 = f'{hour}:30'
            col_new_4 = f'{hour}:45'
            cols_ = [col_new_1, col_new_2, col_new_3, col_new_4]
            # create a new column for that hour + 1
            self.data[cols_] = 0 

            #st.write(data.df)
            #data.df.loc[data.df[hour] > 0, col_new_1] = 1
            #data.df.loc[data.df[hour] > 0, col_new_2] = 1
            #data.df.loc[data.df[hour] > 0, col_new_3] = 1
            #data.df.loc[data.df[hour] > 0, col_new_4] = 1

            def _lambda_for_cells(x):
                '''
                parameters:
                    x: a row of a dataframe
                    hour: the hour that we are processing

                returns:
                    1 or 0 depending if the shift is in that hour
                    
                This function needs to be used inside the loop,
                because it need the 'hour' variable.

                It is used to populate the cells of the hour columns

                ex. hour = 22
                    end_minute = 30
                if the shift start at 22:00 and finish at 23:00
                then the cell values will be:

                the cell '22:00' will be 1
                the cell '22:15' will be 1
                the cell '22:30' will be 1
                the cell '22:45' will be 0
                '''
                # handle last hour
                if x[hour] > 0 and x['finishing_hour'] == hour:
                    if x['end_minute'] == 0:
                        return 1, 0, 0, 0
                    elif x['end_minute'] == 15:
                        return 1, 1, 0, 0
                    elif x['end_minute'] == 30:
                        return 1, 1, 1, 0
                    elif x['end_minute'] == 45:
                        return 1, 1, 1, 1
                
                # handle middle hours
                elif x[hour] > 0 and x['finishing_hour'] > hour:
                    return 1, 1, 1, 1
                else:
                    return 0, 0, 0, 0
                
            self.data[[col_new_1, col_new_2, col_new_3, col_new_4]] = self.data.apply(_lambda_for_cells, axis=1, result_type='expand')
        self.data.drop(columns_hours, axis=1, inplace=True)
    
    def transformation_4(self):
        '''
        This is the last transformation that will be applied to the data,
        to prepare it for the plotting
        '''
        columns_hours = [
                '22:30', '22:45',
                '23:00', '23:15', '23:30', '23:45',
                '24:00', '24:15', '24:30', '24:45',
                '25:00', '25:15', '25:30', '25:45',
                '26:00', '26:15', '26:30', '26:45',
                '27:00', '27:15', '27:30', '27:45'
            ]


        # now need calculate the difference between the closing time and finishing hours
        def lambda_for_time_after_closing(x):
            # case 1 
            if x['finishing_hour'] == x['Closing time']:
                return x['end_minute']
            # case 2
            elif x['finishing_hour'] > x['Closing time']:
                return ((x['finishing_hour'] - x['Closing time'])*60) + x['end_minute']
            # case 3
            elif x['finishing_hour'] < x['Closing time']:
                return 0
            
        self.data['Total_minute_after_close'] = self.data.apply(lambda_for_time_after_closing, axis=1)
        # filter out the shifts that are not after closing time
        #self.data = self.data[self.data['Total_minute_after_close'] > 0]

        columns_hours_new = [
                '22:30', '22:45',
                '23:00', '23:15', '23:30', '23:45',
                '00:00', '00:15', '00:30', '00:45',
                '01:00', '01:15', '01:30', '01:45',
                '02:00', '02:15', '02:30', '02:45',
                '03:00', '03:15', '03:30', '03:45'
            ]
        self.data.rename(columns=dict(zip(columns_hours, columns_hours_new)), inplace=True)
        self.data['Name'] = self.data['Name'] + ' (' + self.data['Division'] + ')'
        # take off row if the all row of columns_hour_new are 0
        #self.data = self.data[(self.data[columns_hours_new] != 0).any(axis=1)]
        
    def transform(self):
        self.tranformation_0()
        self.transformation_1()
        self.transformation_2()
        self.transformation_3()
        self.transformation_4()
        return self.data

'''
These are all the columns that we need to create:

'''
'''
if __name__ == '__main__':
    from Fourth_Analyser import FourthData
    data_pre_mod = pd.read_csv('data/April Rota Data.csv')
    st.write(data_pre_mod)
    data = FourthData('data/April Rota Data.csv').df
    transformation = Transformation(data)
    data = transformation.transform()
    st.write(data)
'''