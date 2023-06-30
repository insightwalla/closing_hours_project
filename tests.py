
'''
author: Roberto Scalas 
date:   2023-05-24 15:37:59.969468
'''

# open the file called 'data/data_for_sales.csv' and read it
import pandas as pd
import streamlit as st

def divide_in_half(data):

    half = len(data) // 2

    data_1 = data.iloc[:half]
    data_2 = data.iloc[half:]

    data_1.to_csv('data/data_1.csv', index=True)
    data_2.to_csv('data/data_2.csv', index=True)

# need to add caching to avoid reading the file twice

columns_for_sales = [
    'ActualCloseTime',
    'Date', 
    'FirstOrderTime', 'FKDayPartID',
    'FKStoreID',
    'TableDescription', 
    'UniqueID', 'Hour_Start_Check', 'Minute_Start_Check',
    'Hour_Close_Check', 'Minute_Close_Check', 'Duration',
    'Minute_Start_Check_rounded', 'Minute_Close_Check_rounded',
    '07:00', '07:15', '07:30', '07:45', '08:00', '08:15',
    '08:30', '08:45', '09:00', '09:15', '09:30', '09:45',
    '10:00', '10:15', '10:30', '10:45', '11:00', '11:15',
    '11:30', '11:45', '12:00', '12:15', '12:30', '12:45',
    '13:00', '13:15', '13:30', '13:45', '14:00', '14:15',
    '14:30', '14:45', '15:00', '15:15', '15:30', '15:45',
    '16:00', '16:15', '16:30', '16:45', '17:00', '17:15',
    '17:30', '17:45', '18:00', '18:15', '18:30', '18:45',
    '19:00', '19:15', '19:30', '19:45', '20:00', '20:15',
    '20:30', '20:45', '21:00', '21:15', '21:30', '21:45',
    '22:00', '22:15', '22:30', '22:45', '23:00', '23:15',
    '23:30', '23:45', '00:00', '00:15', '00:30', '00:45',
    '01:00', '01:15', '01:30', '01:45'
]

@st.cache_data
def open_data():
    data_1 = pd.read_csv('data/data_1.csv')
    data_2 = pd.read_csv('data/data_2.csv')
    # merge the two dataframes
    data = pd.concat([data_1, data_2])
    data = data[columns_for_sales]
    return data

from Fourth_Analyser import FourthData
from prepare_data import Transformation
@st.cache_data
def get_data():
    data = FourthData('data/April Rota Data1.csv').df
    data = Transformation(data).transform()
    return data

data_rota = get_data()