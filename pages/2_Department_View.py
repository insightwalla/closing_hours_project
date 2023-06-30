import streamlit as st
st.set_page_config(layout="wide")
import pandas as pd
import plotly.graph_objects as go

def lambda_for_percentage(x):
    # max number is the tot working in first hour   
    max_number = x[0]
    # divide each number by the max number
    return x / max_number

class UI_For_Department_View:

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
        self.day_of_the_week = None
        self.start_date = None
        self.end_date = None
        self.columns_hours_to_display = self.DEFAULTS_COLUMNS_HOURS  if columns_hours_to_display is None else columns_hours_to_display
        self.run()
    
    def transformation0(self):
        '''
        Since some of the data is not correct, I will transform the data to make it correct
        modifying the format of the date, and adding the month, day, and year

        I am modify the month since it is express in 2 different ways
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

    def create_sidebar(self):
        self.transformation0()
        unique_shift_dates = self.data['Shift date'].unique()
        # sort the dates
        # transform to datetime
        unique_shift_dates = pd.to_datetime(unique_shift_dates)
        unique_shift_dates = sorted(unique_shift_dates)
        self.division = self.unique_division
        self.day_of_the_week = st.sidebar.multiselect('Day of the week', self.unique_days_of_week)
        self.start_date = st.sidebar.date_input('Start date', unique_shift_dates[0], min_value=unique_shift_dates[0], max_value=unique_shift_dates[-1])
        self.end_date = st.sidebar.date_input('End date', unique_shift_dates[-1], min_value=unique_shift_dates[0], max_value=unique_shift_dates[-1])

    def filter_data(self):
        '''
        I could modify this class to give back the inputs values,
        depending on the values I will create a different chart.

        Example.
        if the restaurant is empty and the division is not empty, I will create a chart with the average for each division
        if the restaurant is not empty and the division is empty, I will create a chart with the average for each restaurant
        '''
        if self.day_of_the_week != []:
            self.data = self.data[self.data['Day of the week'].isin(self.day_of_the_week)]
        
        self.start_date = pd.to_datetime(self.start_date)
        self.end_date = pd.to_datetime(self.end_date)
        self.data = self.data[(self.data['Shift date'] >= self.start_date) & (self.data['Shift date'] <= self.end_date)]
        #st.write(self.data)

    def create_depaertment_view(self):
                
        week_ends = ['Thursday', 'Friday', 'Saturday']
        week_days = ['Monday', 'Tuesday', 'Wednesday','Sunday']

        percentage_ = st.sidebar.checkbox('Percentage')
        for d in self.division:
            with st.expander(f'{d}'):
                # filter the data
                df = self.data[self.data['Division'] == d]
                unique_restaurants = df['Home'].unique()
                final_data_for_each_restaurant = []
                for r in unique_restaurants:
                    # filter the data   
                    df_restaurant = df[df['Home'] == r]
                    # merge division and restaurant
                    df_restaurant['Division'] = df_restaurant['Division'] + ' - ' + df_restaurant['Home']
                    data = df_restaurant.groupby(['Division'])[self.columns_hours_to_display].sum()
                    # keep only the ones that are greater than 0
                    # keep the values at col 0 that are greater than 0
                    data = data[data[self.columns_hours_to_display[0]] > 0]
                    # sort the restaurants by name



                    if percentage_: 
                        # apply the lambda function to each row
                        data = data.apply(lambda_for_percentage, axis=1)
                        # multiply by 100
                        data = data * 100
                        # transform to int
                        data = data.astype(int)
                    #st.write(data)
                    # add the data to the final data
                    final_data_for_each_restaurant.append(data)

                # now create a dataframe with the average
                df_average = pd.concat(final_data_for_each_restaurant)
                # sort by index
                df_average = df_average.sort_index(ascending=True)
                # REPLACE THE 0s with nan
                df_average = df_average.replace(0, float('nan'))
                fig = go.Figure(data=go.Heatmap(
                                z=df_average.values,
                                x=self.columns_hours_to_display,
                                y=df_average.index,
                                colorscale='Viridis', coloraxis="coloraxis"))

                # check if all the days are in the week_ends list
                if all(elem in week_ends for elem in self.day_of_the_week):
                    closing_time =  6
                elif all(elem in week_days for elem in self.day_of_the_week):
                    closing_time =  2
                else:
                    closing_time =  6
                fig.add_vline(x=closing_time, line_width=3,
                            line_dash="solid", line_color="green", 
                            annotation_text="Closing time")
                fig.add_vline(x=closing_time+6, line_width=3,
                            line_dash="solid", line_color="red",
                            annotation_text="1 hr and 30 minutes after closing time")

                if percentage_:
                    fig.update_layout(
                        annotations=[go.layout.Annotation(
                            text=str(int(df_average.values[i][j])) + '%' if df_average.values[i][j] > 0 else '',
                            x=self.columns_hours_to_display[j], y=df_average.index[i],
                            xref='x1', yref='y1',
                            showarrow=False, font=dict(color='black', size=10)


                        ) for i in range(len(df_average.index)) for j in range(len(self.columns_hours_to_display))]
                    )
                else:
                    fig.update_layout(
                        annotations=[go.layout.Annotation(
                            text=str(int(df_average.values[i][j])) if df_average.values[i][j] > 0 else '',
                            x=self.columns_hours_to_display[j], y=df_average.index[i],
                            xref='x1', yref='y1',
                            showarrow=False, font=dict(color='black', size=10)


                        ) for i in range(len(df_average.index)) for j in range(len(self.columns_hours_to_display))]
                    )
                # add a vertical line for the closing time and
                fig.update_layout(height= 700)
                fig.update_layout(xaxis_tickangle=45, yaxis_tickangle=-45, showlegend=False, coloraxis_showscale=False)
                
                st.plotly_chart(fig, use_container_width=True)

    def run(self):
        self.create_sidebar()
        self.filter_data()
        self.create_depaertment_view()

from tests import get_data, data_rota
if __name__ == '__main__':
    ui = UI_For_Department_View(data_rota)