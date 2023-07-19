
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
# import subplot
from plotly.subplots import make_subplots

def lambda_for_percentage(x):
    # max number is the tot working in first hour   
    max_number = x[0]
    # divide each number by the max number
    return x / max_number

class UInterface:

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
        self.columns_hours_to_display = self.DEFAULTS_COLUMNS_HOURS  if columns_hours_to_display is None else columns_hours_to_display
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
        self.data['Day'] = self.data.apply(lambda x: x['Day'] if x['Month'] == 5 else x['Month'], axis=1)
        # set all month to 4
        self.data['Month'] = 5
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
        self.division = st.sidebar.multiselect('Division', self.unique_division)
        self.restaurant = st.sidebar.multiselect('Restaurant', self.unique_restaurant)
        self.day_of_the_week = st.sidebar.multiselect('Day of the week', self.unique_days_of_week)
        self.start_date = st.sidebar.date_input('Start date', unique_shift_dates[0], min_value=unique_shift_dates[0], max_value=unique_shift_dates[-1])
        self.end_date = st.sidebar.date_input('End date', unique_shift_dates[-1], min_value=unique_shift_dates[0], max_value=unique_shift_dates[-1])
        self.percentage_ = st.sidebar.checkbox('Percentage')

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
            self.data = self.data[self.data['Home'].isin(self.restaurant)]
        if self.day_of_the_week != []:
            self.data = self.data[self.data['Day of the week'].isin(self.day_of_the_week)]
        
        self.start_date = pd.to_datetime(self.start_date)
        self.end_date = pd.to_datetime(self.end_date)
        self.data = self.data[(self.data['Shift date'] >= self.start_date) & (self.data['Shift date'] <= self.end_date)]
        #st.write(self.data)

    def create_heatmap_view_for_each_restaurant(self):
        for restaurant in self.restaurant:
            with st.expander(restaurant):
                # filter the data
                data = self.data[self.data['Home'] == restaurant]
                data = data.groupby(['Division'])[self.columns_hours_to_display].sum()
                # keep only the ones that are greater than 0
                # keep the values at col 0 that are greater than 0
                data = data[data[self.columns_hours_to_display[0]] > 0]

                def lambda_for_percentage(x):
                    # max number is the tot working in first hour   
                    max_number = x[0]
                    # divide each number by the max number
                    return x / max_number
                
                # apply the lambda function to each row
                if self.percentage_:
                    data = data.apply(lambda_for_percentage, axis=1)
                    # multiply by 100
                    data = data * 100
                    # transform to int
                data = data.astype(int)
                    #st.write(data)
                data = data.where(data != 0, None)
                # create a heatmap, x axis is the hours, y axis is the 1 or 0
                fig = go.Figure(data=go.Heatmap(
                                z=data.values,
                                x=self.columns_hours_to_display,
                                y=data.index,
                                colorscale='Viridis', coloraxis="coloraxis"))
                

                week_ends = ['Thursday', 'Friday', 'Saturday']
                week_days = ['Monday', 'Tuesday', 'Wednesday','Sunday']
                
                # check if all the days are in the week_ends list
                if all(elem in week_ends for elem in self.day_of_the_week):
                    #st.write('**Week ends**')
                    closing_time =  6
                elif all(elem in week_days for elem in self.day_of_the_week):
                    #st.write('**Week days**')
                    closing_time =  2
                else:
                    closing_time =  6

                fig.add_vline(x=closing_time, line_width=3,
                            line_dash="solid", line_color="green", 
                            annotation_text="Closing time")

                fig.add_vline(x=closing_time+6, line_width=3,
                            line_dash="solid", line_color="red",
                            annotation_text="1 hr and 30 minutes after closing time")
            
                # add text value inside eeach cells as percentage
                if self.percentage_:
                    fig.update_layout(
                        annotations=[go.layout.Annotation(
                            text=str(int(data.values[i][j])) + '%' if data.values[i][j] > 0 else '',
                            x=self.columns_hours_to_display[j], y=data.index[i],
                            xref='x1', yref='y1',
                            showarrow=False, font=dict(color='black', size=10)


                        ) for i in range(len(data.index)) for j in range(len(self.columns_hours_to_display))]
                    )
                else:
                    fig.update_layout(
                        annotations=[go.layout.Annotation(
                            text=str(int(data.values[i][j])) + '' if data.values[i][j] > 0 else '',
                            x=self.columns_hours_to_display[j], y=data.index[i],
                            xref='x1', yref='y1',
                            showarrow=False, font=dict(color='black', size=10)


                        ) for i in range(len(data.index)) for j in range(len(self.columns_hours_to_display))]
                    )
                fig.update_layout(height= 700)
                # ticks angle   
                fig.update_layout(xaxis_tickangle=45, yaxis_tickangle=-45, showlegend=False, coloraxis_showscale=False)
                
                c1,c2 = st.columns(2)
                c1.plotly_chart(fig, use_container_width=True)

                # now create a heatmap for each day of the week
                data = self.data[self.data['Home'] == restaurant]
                data = data.groupby(['Day of the week'])[self.columns_hours_to_display].sum()
                # keep only the ones that are greater than 0
                # keep the values at col 0 that are greater than 0
                if self.percentage_:
                    data = data[data[self.columns_hours_to_display[0]] > 0]
                    # apply the lambda function to each row
                    data = data.apply(lambda_for_percentage, axis=1)
                    # multiply by 100
                    data = data * 100
                    # transform to int
                data = data.astype(int)
                # reindex the data

                data = data.reindex(reversed(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']))
                #st.write(data)
                # instead of 0 is float('nan')
                data = data.where(data != 0, None)
                # create a heatmap, x axis is the hours, y axis is the 1 or 0
                fig = go.Figure(data=go.Heatmap(

                                z=data.values,
                                x=self.columns_hours_to_display,
                                y=data.index,
                                colorscale='Viridis', coloraxis="coloraxis"))
                # add text value inside eeach cells as percentage
                if self.percentage_:
                    fig.update_layout(
                        annotations=[go.layout.Annotation(
                            text=str(int(data.values[i][j])) + '%' if data.values[i][j] > 0 else '',
                            x=self.columns_hours_to_display[j], y=data.index[i],
                            xref='x1', yref='y1',
                            showarrow=False, font=dict(color='black', size=10),
                        ) for i in range(len(data.index)) for j in range(len(self.columns_hours_to_display))]
                    )
                else:
                    fig.update_layout(
                        annotations=[go.layout.Annotation(
                            text=str(int(data.values[i][j])) + '' if data.values[i][j] > 0 else '',
                            x=self.columns_hours_to_display[j], y=data.index[i],
                            xref='x1', yref='y1',
                            showarrow=False, font=dict(color='black', size=10),
                        ) for i in range(len(data.index)) for j in range(len(self.columns_hours_to_display))]
                    )
                fig.update_layout(height= 700)
                # ticks angle
                fig.update_layout(xaxis_tickangle=45, yaxis_tickangle=-45, showlegend=False, coloraxis_showscale=False)
                
                week_ends = ['Thursday', 'Friday', 'Saturday']
                week_days = ['Monday', 'Tuesday', 'Wednesday','Sunday']

                # check if all the days are in the week_ends list
                if all(elem in week_ends for elem in self.day_of_the_week):
                    #st.write('**Week ends**')
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
                
                c2.plotly_chart(fig, use_container_width=True)

    def group_and_get_percentages(self, group_by = 'Division'):
        data = self.data.groupby([group_by])[self.columns_hours_to_display].sum()
        data = data[data[self.columns_hours_to_display[0]] > 0]
        # apply the lambda function to each row
        data = data.apply(lambda_for_percentage, axis=1)
        # multiply by 100
        data = data * 100
        # transform to int
        data_division = data.astype(int)
        data_division = data_division.where(data_division != 0, None)
        return data_division
    
    def group_and_get_real_values(self, group_by = 'Division'):
        data = self.data.groupby([group_by])[self.columns_hours_to_display].sum()
        data = data[data[self.columns_hours_to_display[0]] > 0]
        # apply the lambda function to each row
        data_division = data.astype(int)
        data_division = data_division.where(data_division != 0, None)
        return data_division

    def create_main_heatmap_view(self):
        percentage_ = self.percentage_
        if percentage_:
        # 1. Heatmap for each division
            data_division = self.group_and_get_percentages(group_by = 'Division')
            data_day = self.group_and_get_percentages(group_by = 'Day of the week')
            data_restaurant = self.group_and_get_percentages(group_by = 'Home')
        else:
            data_division = self.group_and_get_real_values(group_by = 'Division')
            data_day = self.group_and_get_real_values(group_by = 'Day of the week')
            data_restaurant = self.group_and_get_real_values(group_by = 'Home')


        # for each of the dataframes replace 0 with None
        data_division = data_division.where(data_division != 0, None)
        data_day = data_day.where(data_day != 0, None)
        data_restaurant = data_restaurant.where(data_restaurant != 0, None)
        # sort restaurant by name and reverse it
        data_restaurant = data_restaurant.sort_index(ascending=False)

        data_day = data_day.reindex(reversed(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']))

        fig1 = go.Figure(data=go.Heatmap(
                        z=data_division.values,
                        x=self.columns_hours_to_display,
                        y=data_division.index,
                        colorscale='Viridis', coloraxis="coloraxis",
                        # don't show the values that are 0
                        #text = data_division.values,
                        #hoverinfo='text', 
                        #texttemplate='%{text:.2s}%',
                        #textsrc='text'
                        ))
        # put the yaxis names in the right side
        fig1.update_layout(yaxis_side='right')
        # tick angle
        fig1.update_layout(yaxis_tickangle=45)

        fig2 =  go.Figure(data=go.Heatmap(
                        z=data_restaurant.values,
                        x=self.columns_hours_to_display,
                        y=data_restaurant.index,
                        colorscale='Viridis', coloraxis="coloraxis", 
                        #text=data_restaurant.values,
                        #textsrc='text', hoverinfo='text', texttemplate='%{text:.2s}%'
                        ))
        fig2.update_layout(yaxis_side='right') #or 
        fig2.update_layout(yaxis_tickangle=45)
        fig3 = go.Figure(data=go.Heatmap(
                        z=data_day.values,
                        x=self.columns_hours_to_display,
                        y=data_day.index,
                        colorscale='Viridis', coloraxis="coloraxis", 
                        #text=data_day.values,
                        #textsrc='text', hoverinfo='text', texttemplate='%{text:.2s}%'
        ))
        # tick angleof fig3
        fig3.update_layout(yaxis_side='right')
        fig3.update_layout(yaxis_tickangle=45)
        # add annotations on first graph
        if percentage_:
            fig1.update_layout(
                annotations=[go.layout.Annotation(
                    text=str(int(data_division.values[i][j])) + '%' if data_division.values[i][j] > 0 else '',
                    x=self.columns_hours_to_display[j], y=data_division.index[i],
                    showarrow=False, font=dict(color='black', size=10)


                ) for i in range(len(data_division.index)) for j in range(len(self.columns_hours_to_display))]
            )
            # add annotations on second graph
            fig2.update_layout(
                annotations=[go.layout.Annotation(
                    text=str(int(data_restaurant.values[i][j])) + '%' if data_restaurant.values[i][j] > 0 else '',
                    x=self.columns_hours_to_display[j], y=data_restaurant.index[i],
                    showarrow=False, font=dict(color='black', size=10)


                ) for i in range(len(data_restaurant.index)) for j in range(len(self.columns_hours_to_display))]
            )

            # add annotations on third graph
            fig3.update_layout(
                annotations=[go.layout.Annotation(
                    text=str(int(data_day.values[i][j])) + '%' if data_day.values[i][j] > 0 else '',
                    x=self.columns_hours_to_display[j], y=data_day.index[i],
                    showarrow=False, font=dict(color='black', size=10)


                ) for i in range(len(data_day.index)) for j in range(len(self.columns_hours_to_display))]
            )
        else:
            fig1.update_layout(
                annotations=[go.layout.Annotation(
                    text=str(int(data_division.values[i][j])) + '' if data_division.values[i][j] > 0 else '',
                    x=self.columns_hours_to_display[j], y=data_division.index[i],
                    showarrow=False, font=dict(color='black', size=10)


                ) for i in range(len(data_division.index)) for j in range(len(self.columns_hours_to_display))]
            )
            # add annotations on second graph
            fig2.update_layout(
                annotations=[go.layout.Annotation(
                    text=str(int(data_restaurant.values[i][j])) + '' if data_restaurant.values[i][j] > 0 else '',
                    x=self.columns_hours_to_display[j], y=data_restaurant.index[i],
                    showarrow=False, font=dict(color='black', size=10)


                ) for i in range(len(data_restaurant.index)) for j in range(len(self.columns_hours_to_display))]
            )

            # add annotations on third graph
            fig3.update_layout(
                annotations=[go.layout.Annotation(
                    text=str(int(data_day.values[i][j])) + '' if data_day.values[i][j] > 0 else '',
                    x=self.columns_hours_to_display[j], y=data_day.index[i],
                    showarrow=False, font=dict(color='black', size=10)


                ) for i in range(len(data_day.index)) for j in range(len(self.columns_hours_to_display))]
            )

            
        week_ends = ['Thursday', 'Friday', 'Saturday']
        week_days = ['Monday', 'Tuesday', 'Wednesday','Sunday']

        # check if all the days are in the week_ends list
        if all(elem in week_ends for elem in self.day_of_the_week):
            #st.write('**Week ends**')
            closing_time =  6
        elif all(elem in week_days for elem in self.day_of_the_week):
            #st.write('**Week days**')
            closing_time =  2
        else: 
            closing_time =  6

        fig1.add_vline(x=closing_time, line_width=3,
                    line_dash="solid", line_color="green", 
                    annotation_text="Closing time")
        
        fig1.add_vline(x=closing_time+6, line_width=3,
                    line_dash="solid", line_color="red",
                    annotation_text="1 hr and 30 minutes after closing time")

        # same for the other graphs
        fig2.add_vline(x=closing_time, line_width=3,
                    line_dash="solid", line_color="green",
                    annotation_text="Closing time")
        
        fig2.add_vline(x=closing_time+6, line_width=3,
                    line_dash="solid", line_color="red",
                    annotation_text="1 hr and 30 minutes after closing time")
        
        fig3.add_vline(x=closing_time, line_width=3,
                    line_dash="solid", line_color="green",
                    annotation_text="Closing time")

        fig3.add_vline(x=closing_time+6, line_width=3,
                    line_dash="solid", line_color="red",
                    annotation_text="1 hr and 30 minutes after closing time")

        # set titles for all graphs
        fig1.update_layout(title_text='Departments View')
        fig2.update_layout(title_text='Cafés')
        fig3.update_layout(title_text='Weekly View')

        fig2.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)
        fig3.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)
        fig1.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig1, use_container_width=True)

    def run(self):
        self.create_sidebar()
        self.filter_data()

        self.create_main_heatmap_view()
        self.create_heatmap_view_for_each_restaurant()
        

        # split by department and take the average of the total_minutes_after_close
        # take off 0 and None values from Total_minute_after_close
        self.data = self.data[self.data['Total_minute_after_close'] > 0]
        
        # create a heatmap with the restaurant and the average of the total minutes after close for each restaurant
        data = self.data.groupby(['Home', 'Division'])['Total_minute_after_close'].mean()   
        # now we need to pivot the data
        data = data.reset_index()
        data = data.pivot(index='Home', columns='Division', values='Total_minute_after_close')
        # need to make it as a heatmap
        fig = go.Figure(data=go.Heatmap(
                        z=data.values,
                        x=data.columns,
                        y=data.index,
                        colorscale='Viridis', coloraxis="coloraxis",
                        # show text value inside each cell
                        ))
        # add text value inside eeach cells
        fig.update_layout(
            annotations=[go.layout.Annotation(
                text=str(int(data.values[i][j])) + '' if data.values[i][j] > 0 else '',
                x=data.columns[j], y=data.index[i],
                showarrow=False, font=dict(color='black', size=10)


            ) for i in range(len(data.index)) for j in range(len(data.columns))]
        )

        fig.update_layout(coloraxis_showscale=False)
        # set title as average of total minutes after close
        fig.update_layout(title_text='How long it takes to close the café after the last order in Average? (expressed in minutes after the last order time)')
        st.plotly_chart(fig, use_container_width=True)

