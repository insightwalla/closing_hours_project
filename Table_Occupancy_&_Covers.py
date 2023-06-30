import streamlit as st
st.set_page_config(layout="wide")
import pandas as pd
from google_big_query import GoogleBigQuery, TransformationGoogleBigQuery
import plotly.graph_objects as go
from plotly.subplots import make_subplots


if __name__ == "__main__":
    googleconnection = GoogleBigQuery(key_path = "key.json")
    query = 'SELECT * FROM `sql_server_on_rds.Dishoom_dbo_dpvHstCheckSummary` LIMIT 100'
    #query_2 creates a month column from the date column and filter to keep only September
    month = st.sidebar.number_input('Month', min_value=1, max_value=12, value=1, step=1)
    year = st.sidebar.number_input('Year', min_value=2019, max_value=2023, value=2022, step=1)
    store_id = st.sidebar.multiselect('Store ID', 
                                        options=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15],
                                        default=[1])

    query= f'''
            SELECT *,
            EXTRACT(MONTH FROM DateOfBusiness) AS Month
            FROM `sql_server_on_rds.Dishoom_dbo_dpvHstCheckSummary`
            WHERE EXTRACT(MONTH FROM DateOfBusiness) = {month} AND EXTRACT(YEAR FROM DateOfBusiness) = {year}
                AND FKStoreID IN ({','.join([str(i) for i in store_id])})
            '''
    df = googleconnection.query(query = query, as_dataframe = True)

    df = TransformationGoogleBigQuery(df).df
    st.write(df)
    
    # take off duration > 360
    df = df[df['Duration'] < 360]

    # split by daypart FKDayPartID
    df_breakfast = df[df['FKDayPartID'] == 1]
    df_lunch = df[df['FKDayPartID']     == 2]
    df_dinner = df[df['FKDayPartID']    == 3]
    df_late = df[df['FKDayPartID']      == 4]

    # for each of these get average duration
    breakfast_duration = df_breakfast['Duration'].mean()
    lunch_duration = df_lunch['Duration'].mean()
    dinner_duration = df_dinner['Duration'].mean()
    late_duration = df_late['Duration'].mean()

    st.write(f'Breakfast duration: {breakfast_duration}')
    st.write(f'Lunch duration: {lunch_duration}')
    st.write(f'Dinner duration: {dinner_duration}')
    st.write(f'Late duration: {late_duration}')