import streamlit as st
st.set_page_config(layout="wide")
import pandas as pd
from prepare_data import Transformation
from Fourth_Analyser import FourthData
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from tests import open_data


class UI_For_Daily_View:
    DEFAULTS_COLUMNS_HOURS = [

                '22:30', '22:45',
                '23:00', '23:15', '23:30', '23:45',
                '00:00', '00:15', '00:30', '00:45',
                '01:00', '01:15', '01:30', '01:45',
                '02:00', '02:15', '02:30', '02:45',
                '03:00', '03:15', '03:30', '03:45'
            ]
    
    def __init__(self, data, columns_hours_to_display= None):
        self.data = data
        self.unique_division = self.data['Division'].unique()
        self.unique_restaurant = self.data['Home'].unique()
        self.unique_days_of_week = self.data['Day of the week'].unique()
        self.division = None
        self.restaurant = None
        self.day_of_the_week = None
        self.start_date = None
        self.end_date = None
        self.week = None
        self.columns_hours_to_display = self.DEFAULTS_COLUMNS_HOURS  if columns_hours_to_display is None else columns_hours_to_display
        self.data_for_sales = open_data()
        self.run()
    
    def transformation0(self):
        '''
        Since some of the data is not correct, I will transform the data to make it correct
        modifying the format of the date, and adding the month, day, and year
        '''
        # add month column, day, and year
        self.data['Month'] = self.data['Shift date'].dt.month
        self.data['Day'] = self.data['Shift date'].dt.day
        self.data['Year'] = self.data['Shift date'].dt.year
        # if month isn't 4 then that is the day
        self.data['Day'] = self.data.apply(lambda x: x['Day'] if x['Month'] == 4 else x['Month'], axis=1)
        # set all month to 4
        self.data['Month'] = 4
        # now set the date to the correct format
        self.data['Shift date'] = pd.to_datetime(self.data[['Day', 'Month', 'Year']])
        # drop the columns
        self.data.drop(columns=['Month', 'Day', 'Year'], inplace=True)
        unique_shift_dates = self.data['Shift date'].unique()
        unique_shift_dates = pd.to_datetime(unique_shift_dates, dayfirst=True)
        unique_shift_dates =  sorted(unique_shift_dates)
        self.unique_shift_dates =unique_shift_dates
        #st.stop()
        self.data_for_sales['Date'] = pd.to_datetime(self.data_for_sales['Date'])


    def create_sidebar(self):
        self.transformation0()
        self.division = st.sidebar.multiselect('Division', self.unique_division, key = 'division_daily_view')
        self.restaurant = st.sidebar.multiselect('Restaurant', self.unique_restaurant, default=self.unique_restaurant[0], key = 'restaurant_daily_view')
        self.start_date = self.unique_shift_dates[0]#st.sidebar.date_input('Start date', self.unique_shift_dates[0], min_value=self.unique_shift_dates[0], max_value=self.unique_shift_dates[-1])
        self.end_date = self.unique_shift_dates[-1]#st.sidebar.date_input('End date', self.unique_shift_dates[-1], min_value=self.unique_shift_dates[0], max_value=self.unique_shift_dates[-1])
        self.date = st.date_input('Select a date', self.unique_shift_dates[0], min_value=self.unique_shift_dates[0], max_value=self.unique_shift_dates[-1], key = 'date_daily_view')
        self.date = pd.to_datetime(self.date)
    
    def filter_data(self):
        '''
        I could modify this class to give back the inputs values,
        depending on the values I will create a different chart.

        Example.
        if the restaurant is empty and the division is not empty, I will create a chart with the average for each division
        if the restaurant is not empty and the division is empty, I will create a chart with the average for each restaurant
        '''
        if self.division != []:
            self.data = self.data[self.data['Division'].isin(self.division)]
        if self.restaurant != []:
            # data for rota
            self.data = self.data[self.data['Home'].isin(self.restaurant)]
            message = '-'.join(self.restaurant)
            st.write(f'**{message}**')
            # data for sales
            res_ids = [int(el[1]) for el in self.restaurant]
            self.data_for_sales = self.data_for_sales[self.data_for_sales['FKStoreID'].isin(res_ids)]
       
        
        self.start_date = pd.to_datetime(self.start_date)
        self.end_date = pd.to_datetime(self.end_date)
        self.data = self.data[(self.data['Shift date'] >= self.start_date) & (self.data['Shift date'] <= self.end_date)]
        
        #st.write(self.data)

    def transformationSalesData(self):
        self.year = 2023
        self.month = 4
        
        from google_big_query import GoogleBigQuery, TransformationGoogleBigQuery

        googleconnection = GoogleBigQuery(key_path = "key.json")
        res_to_rename = {
            'D1': 1,
            'D2': 2,
            'D3': 3,
            'D4': 4,
            'D5': 5,
            'D6': 6,
            'D7': 7,
            'D8': 8,
            'D9': 9,
        }
        # the other way is to use the restaurant name
        query = f'''
                SELECT *,
                FROM `sql_server_on_rds.Dishoom_dbo_dpvHstCheckSummary`
                WHERE EXTRACT(YEAR FROM DateOfBusiness) = {self.year} AND EXTRACT(MONTH FROM DateOfBusiness) = {self.month}  
                '''
        if self.restaurant != []:
            restaurants = [res_to_rename[res] for res in self.restaurant]
            st.write(restaurants)
            query = query + f' AND FKStoreID IN ({",".join([str(res) for res in restaurants])})'
        st.write(query)
        df = googleconnection.query(query = query, as_dataframe = True)

        st.write('Data is been Fetched from Google Big Query')
        df = TransformationGoogleBigQuery(df, plot = False).df
        st.write('Data is been Trnasformed')

        #st.write(df)

        self.data_for_sales = df
        # change name from DateOfBusiness to Date
        self.data_for_sales.rename(columns={'DateOfBusiness': 'Date'}, inplace=True)

    def create_daily_heatmap(self):
        # transform date column to datetime
        date_for_sales = self.date.date()
        data_for_sales = self.data_for_sales.copy()
        data_for_sales['Date'] = data_for_sales['Date'].apply(lambda x: x.date())
        data_for_sales = data_for_sales[data_for_sales['Date'] == date_for_sales]
        
        #st.write(data_for_sales)
        # add columns that are onlyh in the columns_hours_to_display
        for col in self.columns_hours_to_display:
            if col not in data_for_sales.columns:
                #st.write(col)
                data_for_sales[col] = 0
        data_for_sales = data_for_sales[self.columns_hours_to_display]
        
        day_name = self.date.day_name() # 'numpy.datetime64' object has no attribute 'day_name'
        group_1_closing_schema = {
            'Sunday': 2,
            'Monday': 2,
            'Tuesday': 2,
            'Wednesday': 2,
            'Thursday': 2,
            'Friday': 6,
            'Saturday': 6
        }
        group_2_closing_schema = {
            'Sunday': 2,
            'Monday': 2,
            'Tuesday': 2,
            'Wednesday': 2,
            'Thursday': 6,
            'Friday': 6,
            'Saturday': 6
        }
        group_3_closing_schema = {
            'Sunday': 2,
            'Monday': 2,
            'Tuesday': 2,
            'Wednesday': 2,
            'Thursday': 2,
            'Friday': 2,
            'Saturday': 2
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
        if self.restaurant != []:
            # check if all restaurant have the same closing time
            if len(set([res_[res][day_name] for res in self.restaurant])) != 1:
                st.write('Restaurants have different closing time')
                closing_time = 2 if day_name in ['Sunday', 'Monday', 'Tuesday', 'Wednesday'] else 6
            else:
                st.write('Restaurants have the same closing time')
                closing_time = res_[self.restaurant[0]][day_name]

        # filter the data
        df_date = self.data[self.data['Shift date'] == self.date]
        # keep only rows that sums greater than 0
        df_date = df_date[df_date[self.columns_hours_to_display[closing_time:]].sum(axis=1) > 0]
        df_date.sort_values(by=['Division'], inplace=True)
        total = df_date['Total_minute_after_close'].sum()
        #st.write(f'Total: {total} minutes')
        average_across_all = total / len(df_date)
        #st.write(f'Average: {average_across_all:.2f} minutes')

        # create a heatmap, x axis is the hours, y axis is the 1 or 0
        with st.expander(f'{self.date.date()} - {self.date.day_name()} - Average Time: {average_across_all:.0f} minutes', expanded=True):
            # for each division create a chart with the average
            unique_division = df_date['Division'].unique()

            dataframe_for_average = []
            for _, division in enumerate(unique_division):
                data = df_date[df_date['Division'] == division]
                # using the column "Total_minute_after_close' get the average
                average = data['Total_minute_after_close'].mean()
                # add the average to the dataframe
                dataframe_for_average.append([division, average])
                # create a chart with the average

            # now create a dataframe with the average
            df_average = pd.DataFrame(dataframe_for_average, columns=['Division', 'Average'])
            df_average.sort_values(by=['Average'], inplace=True)
            
            # create a chart with the average
            fig1 = go.Figure(data = go.Heatmap(
                            z=df_average['Average'].values.reshape(1,-1),
                            x=df_average['Division'].values,
                            y=['Average'],
                            text = df_average['Average'].values.reshape(1,-1),
                            hoverinfo='text',
                            textsrc='z',
                            texttemplate='%{text:.0f} min',
                            colorscale='Viridis', coloraxis="coloraxis"))
            fig1.update_layout(showlegend=False,
                            coloraxis_showscale=False,
                            xaxis_tickangle=45,
                            yaxis_tickangle=-45,
                            height= 200)
            # set title to the chart
            fig1.update_layout(title=f'Average: {average_across_all:.2f} minutes')
            st.plotly_chart(fig1, use_container_width=True)

            fig2 = go.Figure()

            fig2.add_trace(go.Heatmap(
                            z=df_date[self.columns_hours_to_display].values,
                            x=self.columns_hours_to_display,
                            y=df_date['Name'].values,
                            colorscale='Viridis', coloraxis="coloraxis"))
            

            fig2.update_layout(showlegend=True,
                            coloraxis_showscale=False, 
                            xaxis_tickangle=45, 
                            yaxis_tickangle= -25,
                            yaxis_side="right")
                            #height= 700)
            fig2.update_layout(
                title=f'Closing Hours: {self.columns_hours_to_display[closing_time]} - {self.columns_hours_to_display[closing_time+6]}',
                xaxis_title="Time",
                yaxis_title="Name",
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1.02,
                    xanchor="right",
                    x=1
                ))
            fig2.add_vline(x=closing_time, line_width=3,
                        line_dash="solid", line_color="green", 
                        annotation_text="Closing time")
            
            fig2.add_vline(x=closing_time+6, line_width=3,
                        line_dash="solid", line_color="red",
                        annotation_text="1 hr and 30 minutes after closing time")
            

            st.plotly_chart(fig2, use_container_width=True)


            fig3 = make_subplots(specs=[[{"secondary_y": True}]])
            for division in unique_division:
                data = df_date[df_date['Division'] == division]
                fig3.add_trace(go.Bar(
                    x=self.columns_hours_to_display, y=data[self.columns_hours_to_display].sum(axis=0),
                    name=division,
                    marker_line_color='black',
                    marker_line_width=1.5,
                    opacity=0.6
                ),
                )

            fig3.add_trace(go.Bar(
                    x=self.columns_hours_to_display, y=data_for_sales.sum(axis=0),
                    name='Covers',
                    marker_line_width=1.5,
                    opacity=0.6,
                ),
                # this will be all stacked
                secondary_y=True
            )
            

            fig3.update_layout(
                title='Total',
                xaxis_title="Time",
                yaxis_title="Total",
                barmode='group', xaxis_tickangle=45,
                legend=dict(
                orientation="v",
                yanchor="top",
                y=1.02,
                xanchor="right",
                x=1
            ))
                            
            # show the plots
            
            st.plotly_chart(fig3, use_container_width=True)

    def run(self):
        self.create_sidebar()
        self.filter_data()
        self.create_daily_heatmap()

from tests import get_data, data_rota
if __name__ == '__main__':
    ui = UI_For_Daily_View(data_rota)