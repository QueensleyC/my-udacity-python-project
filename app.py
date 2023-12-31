from dash import Dash, dcc, html, Output, Input, dash_table, clientside_callback
from dash.dependencies import Input, Output, State
from dash_iconify import DashIconify
from dash.exceptions import PreventUpdate

import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

import datetime
import pandas as pd
import numpy as np
import plotly.express as px

from collections import Counter

# Instantiate app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server

# Set background colour of Graphs in UI
graph_ui_background = {'layout' :
        {
            'plot_bgcolor':'rgba(0,0,0,0)',
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'font':{
                'color':'7fdbff'
            }
        }
        }

# Create app layout
app.layout = html.Div(
        style={'backgroundColor': '#0147ab'},
        children = [
        # Application title
        html.H1("Descriptive Statistics on US Bikeshare Data", style = {'textAlign':'center'}),
        
        # Dropdown elements for filtering data
        html.H2("Filter Data", style = {'color':'#0252bd'}),

        html.H5('Select City'),
        dcc.Dropdown(options = ['Washington', 'New York City', 'Chicago'], value = 'Chicago', id='city-dropdown', clearable=False),
        html.Br(), 

        html.H5('Select Month'),
        dcc.Dropdown(options = ['All', 'January', 'February', 'March', 'April', 'May', 'June'], value = 'All', id='month-dropdown',clearable=False),
        html.Br(), 

        html.H5('Select Day'),
        dcc.Dropdown(options = ['All', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'], value = 'All', id='day-dropdown',clearable=False),
        html.Br(), 

        html.H5('How many rows of the data would you like to view?'),
        dcc.Dropdown(options = [0,5,10,20,50,100,200], value = 0, id='rows-data-dropdown',clearable=False),

        html.Br(), # Adds spacing between elements

        # Button for running analysis
        dmc.Button('Run Analysis', 
                    id='analyse_button', 
                    leftIcon = [DashIconify(icon = 'mdi:chart-line')],
                    style = {'margin-left': '37.5%', 'width': '300px'}
                    ),

        html.Br(),
        html.Br(),


        html.H5("NB 1: It takes >5 minutes to compute when Month and/or Day are set to 'All'",
                 style = {'textAlign':'center', 'color':'red'},
                 ),
        
        html.H5("NB 2: To obtain maximum result, use a PC",
                 style = {'textAlign':'center', 'color':'red'},
                 ),

        # Stores the filtered dataframe for use
        dcc.Store(id = 'filtered-df-show'),
        dcc.Store(id = 'filtered-df-use'),

        html.Br(),

        # Element for displaying dataframe to the user
        dash_table.DataTable(
            id = 'show-df'
        ),

        html.Br(),

        # Shows values of statistical analysis
        html.H3('Most Frequent Times of Travel' ,style = {'textAlign':'center'}),
        html.H5('Most Common Month:'),
        html.Div(id = 'most-common-month'),
        html.H5('Most Common Day of the Week:'),
        html.Div(id = 'most-common-dow'),
        html.H5('Most Common Start Hour:'),
        html.Div(id = 'most-common-sh'),

        html.H3('Most Popular Stations and Trip' ,style = {'textAlign':'center'}),
        html.H5('Most used Start Station:'),
        html.Div(id = 'most-used-ss'),
        html.H5('Most used End Station:'),
        html.Div(id = 'most-used-es'),
        html.H5('Most Frequent Route:'),
        html.Div(id = 'most-freq-route'),

        html.H3('Total and Average Trip Duration' ,style = {'textAlign':'center'}),
        html.H5('Total Travel Time (in seconds):'),
        html.Div(id = 'total-travel-time'),
        html.H5('Mean Travel Time (in seconds):'),
        html.Div(id = 'mean-travel-time'),

        html.H3('User Statistics' ,style = {'textAlign':'center'}),
        html.H5('User Type Count:'),
        dbc.Row(
            [
                dbc.Col(html.H6('Subscriber:'), width = 1),
                dbc.Col(html.Div(id = 'subscriber')),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(html.H6('Customer:'), width = 1),
                dbc.Col(html.Div(id = 'customer')),
            ]
        ),
        html.Div(id = 'user-type-count-1'),
        html.Div(id = 'user-type-count-2'),

        html.H5('Gender Count:'),
        dbc.Row(
            [
                dbc.Col(html.H6('Male:'), width = 1),
                dbc.Col(html.Div(id = 'gender-count-m')),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(html.H6('Female:'), width = 1),
                dbc.Col(html.Div(id = 'gender-count-f')),
            ]
        ),

        html.H5('Most Common Year of Birth:'),
        html.Div(id = 'common-year-birth'),
        html.H5('Earliest Year of Birth:'),
        html.Div(id = 'earliest-year-birth'),
        html.H5('Most Recent Year of Birth:'),
        html.Div(id = 'recent-year-birth'),

        # Displays graphs
        dcc.Graph(id = 'dsn-birth-year', figure = graph_ui_background),
        dcc.Graph(id = 'gender-count-plot', figure = graph_ui_background),
        dcc.Graph(id = 'user-type-count-plot', figure = graph_ui_background),
        dcc.Graph(id = 'top-10-start-station', figure = graph_ui_background),
        dcc.Graph(id = 'top-10-end-station', figure = graph_ui_background),
        dcc.Graph(id = 'top-10-routes', figure = graph_ui_background)

])

# Turns on loading state for button
clientside_callback(
    """
    function updateLoadingState(n_clicks) {
        return true
    }
    """,
    Output("analyse_button", "loading", allow_duplicate=True),
    Input("analyse_button", "n_clicks"),
    prevent_initial_call=True,
)


@app.callback(
    Output(component_id='filtered-df-use', component_property= 'data'),
    inputs = [Input('analyse_button', 'n_clicks')],
    state = [
        State(component_id='city-dropdown', component_property='value'),
        State(component_id='month-dropdown', component_property='value'),
        State(component_id='day-dropdown', component_property='value')
    ],
   )
# Filters data according to user input (This will be used for the analysis)
def filter_data_use(clicks, city, month, day):

    if clicks is None:
        raise PreventUpdate
    else:

        print('Creating dataset at {}'.format(datetime.datetime.now()))

        CITY_DATA = { 'Chicago': 'chicago.csv',
                'New York City': 'new_york_city.csv',
                'Washington': 'washington.csv' }

        df = pd.read_csv(f'{CITY_DATA[city]}', parse_dates=['Start Time', 'End Time'])

        # Drop first column
        df = df.iloc[:,1:]

        # Create month column
        months_dict = {'01': 'January', '02': 'February', '03': 'March', '04':'April', '05': 'May', '06': 'June'}

        df['month'] = df['Start Time'].dt.strftime('%m')
        df['month'] = df['month'].map(months_dict)

        # Create day of week (dow) column
        dow_dict ={0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}

        df['dow'] = df['Start Time'].dt.dayofweek
        df['dow'] = df['dow'].map(dow_dict)

        # Create an hour column
        df['hour'] = df['Start Time'].dt.hour
        df['hour'] = df['hour'].apply(lambda x: str(x) + ':00')  


        # Filter data
        if month != 'All':
            df = df[df['month'] == month]

        if day != 'All':
            df = df[df['dow'] == day]

        return df.to_dict('list')



@app.callback(
    Output(component_id='filtered-df-show', component_property= 'data'),
    inputs = [Input('analyse_button', 'n_clicks')],
    state = [
        State(component_id='city-dropdown', component_property='value'),
        State(component_id='month-dropdown', component_property='value'),
        State(component_id='day-dropdown', component_property='value'),
        State(component_id='rows-data-dropdown', component_property='value')
    ],
   )
# Filters data according to user input (This will be displayed to the user if requested for)
def filter_data_show(clicks, city, month, day, rows):

    if clicks is None:
        raise PreventUpdate
    else:
        CITY_DATA = { 'Chicago': 'chicago.csv',
                'New York City': 'new_york_city.csv',
                'Washington': 'washington.csv' }

        df = pd.read_csv(f'{CITY_DATA[city]}', parse_dates=['Start Time', 'End Time'])

        # Drop first column
        df = df.iloc[:,1:]

        # Create month column
        months_dict = {'01': 'January', '02': 'February', '03': 'March', '04':'April', '05': 'May', '06': 'June'}

        df['month'] = df['Start Time'].dt.strftime('%m')
        df['month'] = df['month'].map(months_dict)

        # Create day of week (dow) column
        dow_dict ={0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}

        df['dow'] = df['Start Time'].dt.dayofweek
        df['dow'] = df['dow'].map(dow_dict)

        # Create an hour column
        df['hour'] = df['Start Time'].dt.hour
        df['hour'] = df['hour'].apply(lambda x: str(x) + ':00')  


        # Filter data
        if month != 'All':
            df = df[df['month'] == month]

        if day != 'All':
            df = df[df['dow'] == day]

        df = df.head(rows)
        return df.to_dict('records')

@app.callback(
    Output('show-df', 'data'),
    Input('filtered-df-show', 'data')
)
# Displays data if requested for
def show_data(data):
    return data

@app.callback(
    Output('most-common-month', 'children'),
    Output('most-common-dow', 'children'),
    Output('most-common-sh', 'children'),
    Input('filtered-df-use','data')
)
# Analyses travel times
def times_of_travel(df):
    
    month = Counter(df['month'])
    month_series = pd.Series(month)
    month_series.sort_values(ascending= False, inplace= True)
    top_month = month_series.index[0]

    dow = Counter(df['dow'])
    dow_series = pd.Series(dow)
    dow_series.sort_values(ascending= False, inplace= True)
    top_dow = dow_series.index[0]

    hour = Counter(df['hour'])
    hour_series = pd.Series(hour)
    hour_series.sort_values(ascending= False, inplace= True)
    top_hour = hour_series.index[0]

    return top_month, top_dow, top_hour

@app.callback(
    Output('most-used-ss', 'children'),
    Output('most-used-es', 'children'),
    Output('most-freq-route', 'children'),
    Input('filtered-df-use','data')
)
# Analysis station statistic
def station_stats(df):
    ss = Counter(df['Start Station'])
    ss_series = pd.Series(ss)
    ss_series.sort_values(ascending= False, inplace= True)
    
    top_ss = ss_series.index[0]

    es = Counter(df['End Station'])
    es_series = pd.Series(es)
    es_series.sort_values(ascending= False, inplace= True)
    
    top_es = es_series.index[0]


    station_zip = list(zip(df['Start Station'], df['End Station']))
    station_hyphened = [str(start) + ' - ' + str(end) for start, end in station_zip]
    routes = Counter(station_hyphened)
    routes_series = pd.Series(routes)
    routes_series.sort_values(ascending= False, inplace= True)

    freq_route = routes_series.index[0]
    return top_ss, top_es, freq_route


@app.callback(
    Output('total-travel-time', 'children'),
    Output('mean-travel-time', 'children'),
    Input('filtered-df-use','data')
)
# Analysis duration of trip
def trip_duration(df):
    total_duration = np.sum(df["Trip Duration"])
    mean_duration = np.mean(df["Trip Duration"])

    return total_duration, mean_duration

@app.callback(
    Output('subscriber', 'children'),
    Output('customer', 'children'),
    Output('gender-count-m', 'children'),
    Output('gender-count-f', 'children'),
    Output('recent-year-birth', 'children'),
    Output('earliest-year-birth','children'),
    Output('common-year-birth','children'),
    Input('filtered-df-use','data')
)
def user_stat(df):

    ### --------- User Type ---------- ###
    user_type_list_cleaned = [item for item in df['User Type'] if item is not None]

    user_type_dict = Counter(user_type_list_cleaned)

    print(user_type_dict)

    users = ['','']

    users[0] = user_type_dict['Subscriber']
    users[1] = user_type_dict['Customer']



    ### --------- Gender ---------- ###
    genders = ['','']

    if 'Gender' in df:
        # Remove all NoneType from the list
        gender_list_cleaned = [item for item in df['Gender'] if item is not None]

        gender_count_dict = Counter(gender_list_cleaned)

        print(gender_count_dict)        

        genders[0] = gender_count_dict['Male'] 
        genders[1] = gender_count_dict['Female'] 

    else: 
        genders[0] = 'This city has no data for genders'
        genders[1] = 'This city has no data for genders'


    ### --------- Births ---------- ###
    if 'Birth Year' in df:
        print('Removing NoneType...')
        year_list_cleaned = [item for item in df['Birth Year'] if item is not None]


        birth_year = Counter(year_list_cleaned)
        
        list_birth_year_count = []

        for item in birth_year.items():
            list_birth_year_count.append(item)


        top_birth_year = sorted(list_birth_year_count, key = lambda x: x[1], reverse=True)[0][0] #TODO: Not producing correct result
                
        year_list_cleaned.sort()

        earliest_birth_year = int(year_list_cleaned[0])
        recent_birth_year = int(year_list_cleaned[-1])
    
    else:
        earliest_birth_year = 'This city has no data for year'
        recent_birth_year = 'This city has no data for year'
        top_birth_year = 'This city has no data for year'


    return users[0], users[1], genders[0], genders[1], recent_birth_year, earliest_birth_year, top_birth_year


@app.callback(
    Output("dsn-birth-year", "figure"),
    Output("gender-count-plot", "figure"),
    Output("user-type-count-plot", "figure"),
    Output("top-10-start-station", "figure"),
    Output("top-10-end-station", "figure"),
    Output("top-10-routes", "figure"),
    Input('filtered-df-use','data')
)
# Plots chart 
def plot_charts(df):

    transparent_background = 'rgba(0,0,0,0)'

    if 'Birth Year' in df and 'Gender' in df:
        # plot year distribution
        year_list_cleaned = [item for item in df['Birth Year'] if item is not None]
        birth_year = Counter(year_list_cleaned)
        birth_year_series = pd.Series(birth_year)
        
        birth_year_dsn = px.bar(y = birth_year_series.values, x = birth_year_series.index,title='Distribution of Birth Year')
        birth_year_dsn.update_layout(xaxis_title = "Year", 
                                        yaxis_title = "Count",
                                        plot_bgcolor = transparent_background,
                                        paper_bgcolor = transparent_background
                                    )

        # plot gender count
        gender_list_cleaned = [item for item in df['Gender'] if item is not None]

        gender_count = Counter(gender_list_cleaned)
        gender_count_series = pd.Series(gender_count)

        gender_count_plot = px.bar(y = gender_count_series.values, x = gender_count_series.index,title='Gender Count Plot')
        gender_count_plot.update_layout(xaxis_title = "Gender", 
                                            yaxis_title = "Count",
                                            plot_bgcolor = transparent_background,
                                            paper_bgcolor = transparent_background
                                        )
    
    else: 
        empty_graph_year = {
                "layout": {
                    "xaxis": {
                        "visible": False
                    },
                    "yaxis": {
                        "visible": False
                    },
                    "annotations": [
                        {
                            "text": "No data for year found",
                            "xref": "paper",
                            "yref": "paper",
                            "showarrow": False,
                            "font": {
                                "size": 28
                            }
                        }
                    ]
                }
            }

        empty_graph_gender = {
                "layout": {
                    "xaxis": {
                        "visible": False
                    },
                    "yaxis": {
                        "visible": False
                    },
                    "annotations": [
                        {
                            "text": "No data for gender found",
                            "xref": "paper",
                            "yref": "paper",
                            "showarrow": False,
                            "font": {
                                "size": 28
                            }
                        }
                    ]
                }
            }

        birth_year_dsn = empty_graph_year
        gender_count_plot = empty_graph_gender

    # plot user type count
    user_type_list_cleaned = [item for item in df['User Type'] if item is not None]

    user_type_count = Counter(user_type_list_cleaned)
    user_type_series = pd.Series(user_type_count)

    user_type_count_plot =  px.bar(y = user_type_series.values, x = user_type_series.index,title='User Type Count Plot')
    user_type_count_plot.update_layout(xaxis_title = "User Type", 
                                        yaxis_title = "Count",
                                        plot_bgcolor = transparent_background,
                                        paper_bgcolor = transparent_background
                                    )

    # plot station statistic
    ss = Counter(df['Start Station'])
    ss_series = pd.Series(ss)
    ss_series.sort_values(ascending= False, inplace= True)

    ss_plot =  px.bar(y = ss_series.values[:10], x = ss_series.index[:10],title='Top 10 Most Used Start Stations')
    ss_plot.update_layout(xaxis_title = "Stations", 
                            yaxis_title = "Count",
                            plot_bgcolor = transparent_background,
                            paper_bgcolor = transparent_background
                           )


    es = Counter(df['End Station'])
    es_series = pd.Series(es)
    es_series.sort_values(ascending= False, inplace= True)

    es_plot =  px.bar(y = es_series.values[:10], x = es_series.index[:10],title='Top 10 Most Used End Stations')
    es_plot.update_layout(xaxis_title = "Stations",
                            yaxis_title = "Count",
                            plot_bgcolor = transparent_background,
                            paper_bgcolor = transparent_background
                           )

    # top 10 Routes
    station_zip = list(zip(df['Start Station'], df['End Station']))
    station_hyphened = [str(start) + ' - ' + str(end) for start, end in station_zip]
    routes = Counter(station_hyphened)
    routes_series = pd.Series(routes)
    routes_series.sort_values(ascending= False, inplace= True)

    routes_plot = px.bar(y = routes_series.values[:10], x = routes_series.index[:10],title='Top 10 Most Plied Routes')
    routes_plot.update_layout(xaxis_title = "Routes", 
                                yaxis_title = "Count",
                                plot_bgcolor = transparent_background,
                                paper_bgcolor = transparent_background
                               )


    return birth_year_dsn, gender_count_plot, user_type_count_plot, ss_plot, es_plot, routes_plot

# Turns off loading state for button
@app.callback(
    Output('analyse_button', 'loading'),
    Input("top-10-routes", "figure"),
    prevent_initial_call=True
)
def update(_):
    return False


if __name__ == '__main__':
    app.run_server(debug = True)
