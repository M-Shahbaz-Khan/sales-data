import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
from datetime import datetime
from datetime import timedelta
from datetime import date
from dateutil.relativedelta import relativedelta
from xlrd import open_workbook
import plotly.express as px

import numpy as np
import pandas as pd
import json

# use data from date data was pulled - 1 year
earliest_data_date = datetime(2021, 3, 17) - relativedelta(years=1)

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def customLegend(fig, nameSwap):
    for i, dat in enumerate(fig.data):
        for elem in dat:
            if elem == 'name':
                fig.data[i].name = nameSwap[fig.data[i].name]
    return(fig)

def app_rate_to_group(x, sum_type):
    total_dials = x[sum_type].sum()
    apps_submitted = x[x['lead_status'] == 'Application Submitted'][sum_type].sum()

    if(apps_submitted != 0):
        x.loc[:,'app_rate'] = str(round((apps_submitted * 100) / total_dials, 2)) + '%'
    else:
        x.loc[:,'app_rate'] = str(0) + '%'

    return x

# Pandas options
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 30)
pd.set_option('display.min_rows', 25)

df_engagements_leads = pd.read_pickle('./df_engagements_leads_processed') # Read data from file

# Load SDR hash -> SDR name
book = open_workbook('./SDR.xls', on_demand=True)
sheet = book.sheet_by_name('Sheet1')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Generate dict of class codes to populate drop down menu
def class_code_list(class_codes):
    options_list = []
    class_codes = np.sort(class_codes)

    for code in class_codes:
        code_dict = {}
        code_dict['label'] = code
        code_dict['value'] = code
        options_list.append(code_dict)

    options_list.append({'label':'ALL', 'value':'ALL'})

    return options_list

def sdr_list(sheet):
    options_list = []

    for i in range(0, sheet.nrows):
        sdr_dict = {}
        row = sheet.row_values(i)
        sdr_dict['label'] = row[1].title()
        sdr_dict['value'] = row[0]
        options_list.append(sdr_dict)

    options_list.append({'label':'ALL', 'value':'ALL'})

    return options_list

gclasscode_options = class_code_list(df_engagements_leads['governing_class_code'].unique())
sdr_options = sdr_list(sheet)

app.layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                dcc.Dropdown(
                    id='class_code_dropdown',
                    options=gclasscode_options,
                    placeholder='Class Code',
                )
            ]),

            dcc.DatePickerRange(
                id='my-date-picker-range',
                style={'background-color': 'white'},
                min_date_allowed=date(1995, 8, 5),
                max_date_allowed=date(2022, 9, 19),
                initial_visible_month=date(2021, 2, 1),
                stay_open_on_select = False,
                clearable = True,
            ),

            html.Div([
                dcc.Dropdown(
                    id='sales_rep_dropdown',
                    options=sdr_options,
                    placeholder='Sales Rep',
                )
            ]),
        ], id='filter-div'),

        html.Div([
            dash_table.DataTable(
                id='total-table',
                style_cell={'textAlign': 'center',
                            'background-color' :'white',
                            'border': 'rgb(50, 50, 50) solid'},
                style_as_list_view=True,
                style_header={
                    'backgroundColor': 'white',
                    'fontWeight': 'bold'
                },
                columns=[{'name': 'Total Leads', 'id':'total_leads'},
                            {'name': 'Active Leads Dialed', 'id':'active_leads_dialed'},
                            {'name': 'App Submitted', 'id':'app_submitted'},
                            {'name': 'Total Dials', 'id':'total_dials'},
                            {'name': 'App Rate', 'id':'app_rate'}],
            )
        ]),
    ], id='header-div'),

    html.Div([
        html.Div([
            dcc.Loading(id = "loading-icon-fig0", className='loading-icon', children=[
                dcc.Graph(id='leads_lead_active_by_effective_month_fig0'),
            ], type='circle'),
            dcc.Loading(id = "loading-icon-fig1", className='loading-icon', children=[
                dcc.Graph(id='dials_lead_status_by_effective_month_fig1'),
            ], type='circle'),
            dcc.Loading(id = "loading-icon-fig2", className='loading-icon', children=[
                dcc.Graph(id='leads_lead_status_by_effective_month_fig2'),
            ], type='circle'),
            dcc.Loading(id = "loading-icon-fig3", className='loading-icon', children=[
                dcc.Graph(id='dials_lead_status_by_call_number_fig3'),
            ], type='circle'),
            dcc.Slider(
                id='cutoff-slider-fig3',
                min=0,
                max=1000,
                step=None,
                marks={
                    0: '0',
                    15: '15',
                    50: '50',
                    250: '250',
                    500: '500',
                    750: '750',
                    1000: '1000'
                },
                value=0
            ),
        ], id='left-container'),

        html.Div([
            dcc.Loading(id = "loading-icon-governing-class-code-table", className='loading-icon',
                children=[
                dash_table.DataTable(
                    id='governing-class-code-table',
                    style_cell={'textAlign': 'center',
                                'background-color' :'white'},
                    style_as_list_view=True,
                    style_header={
                        'backgroundColor': 'white',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        },
                        {
                            'if': {'column_id': 'lost'},
                            'border': 'rgb(50, 50, 50) solid'
                        },
                        {
                            'if': {'column_id': 'is_active'},
                            'border': 'rgb(50, 50, 50) solid'
                        },
                        {
                            'if': {'column_id': 'is_lead'},
                            'border': 'rgb(50, 50, 50) solid'
                        }
                    ],
                    columns = [{'name': 'Class Code', 'id': 'governing_class_code'},
                                {'name': 'Total', 'id': 'is_lead'},
                                {'name': 'Active', 'id': 'is_active'},
                                {'name': 'Lost', 'id': 'lost'},
                                {'name': 'Connected', 'id': 'call_connected'},
                                {'name': 'DM Reached', 'id': 'dm_reached'},
                                {'name': 'App Started', 'id': 'app_started'},
                                {'name': 'App Submitted', 'id': 'app_submitted'}],
                    filter_action="native",
                    sort_action="native",
                    sort_mode="multi",
                    column_selectable="single",
                    selected_columns=[],
                    selected_rows=[],
                    page_action="native",
                    page_current= 0,
                    page_size= 10,
                )
            ], type='circle'),
            dcc.Loading(id = "loading-icon-fig4", className='loading-icon', children=[
                dcc.Graph(id='dials_lead_status_by_governing_class_code_fig4'),
            ], type='circle'),
            dcc.Slider(
                id='cutoff-slider-classcode',
                min=0,
                max=1000,
                step=None,
                marks={
                    0: '0',
                    15: '15',
                    50: '50',
                    250: '250',
                    500: '500',
                    750: '750',
                    1000: '1000'
                },
                value=0
            ),
            dcc.Loading(id = "loading-icon-fig5", className='loading-icon', children=[
                dcc.Graph(id='dials_lead_status_by_insurance_group_fig5'),
            ], type='circle'),
            dcc.Slider(
                id='cutoff-slider-insurance',
                min=0,
                max=1000,
                step=None,
                marks={
                    0: '0',
                    15: '15',
                    50: '50',
                    250: '250',
                    500: '500',
                    750: '750',
                    1000: '1000'
                },
                value=0
            ),
        ], id='right-container'),
    ])

], id='full-page')

@app.callback(
    Output('leads_lead_active_by_effective_month_fig0', 'figure'),
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date'),
     Input('class_code_dropdown', 'value'),
     Input('sales_rep_dropdown', 'value')])
def update_data(start_date, end_date, class_code, sales_rep):
    dff = df_engagements_leads.copy()

    if (sales_rep != 'ALL') and (sales_rep is not None):
        dff = dff[dff['updated_by'] == sales_rep]

    if (class_code != 'ALL') and (class_code is not None):
        dff = dff[dff['governing_class_code'] == class_code]

    if start_date is not None:
        st_date = date.fromisoformat(start_date)
        dff = dff[dff['activity_date'] >=
                            datetime(st_date.year, st_date.month, st_date.day)]
    if end_date is not None:
        end_date = date.fromisoformat(end_date)

        dff = dff[dff['activity_date'] <
                        datetime(end_date.year, end_date.month, end_date.day)]

    try:
        dff['effective_month'] = pd.Categorical(dff['effective_month'], categories=months, ordered=True)
        dff.sort_values(by='effective_month', ascending=True, inplace=True)

        dff = dff.sort_values(by="activity_date").drop_duplicates(subset=["lead"], keep="last")
        dff = dff.groupby('effective_month')[['is_lead', 'is_active', 'lost', 'app_submitted']].sum().reset_index()

        def get_app_rate(x):
            if(x.app_submitted != 0):
                return str(round((x.app_submitted * 100/x.is_lead) , 2)) + '%'
            else:
                return str(0) + '%'

        dff.loc[:, 'app_rate'] = dff.apply(lambda x: get_app_rate(x), axis=1)

        fig0 = px.bar(data_frame=dff, x="effective_month", y=["is_lead", "is_active", "app_submitted", "lost"],
                    title='Fig 0 - Number Leads by Effective Month', hover_data=['app_rate'], hover_name='app_rate',
                    barmode="stack", template="plotly")

        fig0.update_layout(
            yaxis_title="Leads",
            xaxis_title="Effective Month",
            xaxis = dict(
                tickmode = 'linear'
            ),
            legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
            )
        )

        fig0 = customLegend(fig = fig0, nameSwap = {'is_lead':'Leads',
                                       'is_active' : 'Active',
                                       'app_submitted' : 'App Submitted',
                                       'lost' : 'Lost'})
    except Exception as ex:
        fig0 = {}
        print(ex)

    return fig0

@app.callback(
    Output('dials_lead_status_by_effective_month_fig1', 'figure'),
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date'),
     Input('class_code_dropdown', 'value'),
     Input('sales_rep_dropdown', 'value')])
def update_data(start_date, end_date, class_code, sales_rep):

    dff = df_engagements_leads.copy()

    if (sales_rep != 'ALL') and (sales_rep is not None):
        dff = dff[dff['updated_by'] == sales_rep]

    if (class_code != 'ALL') and (class_code is not None):
        dff = dff[dff['governing_class_code'] == class_code]

    if start_date is not None:
        st_date = date.fromisoformat(start_date)
        dff = dff[dff['activity_date'] >=
                            datetime(st_date.year, st_date.month, st_date.day)]
    if end_date is not None:
        end_date = date.fromisoformat(end_date)

        dff = dff[dff['activity_date'] <
                        datetime(end_date.year, end_date.month, end_date.day)]

    try:

        dff['effective_month'] = pd.Categorical(dff['effective_month'], categories=months, ordered=True)
        dff.sort_values(by='effective_month', ascending=True, inplace=True)  # same as you have now; can use inplace=True
        dff_fig1 = dff.groupby(by=["effective_month", "lead_status"]).size().reset_index(name="Dials")

        dff_fig1 = dff_fig1.groupby(by=["effective_month"]).apply(lambda x: app_rate_to_group(x, 'Dials'))

        fig1 = px.bar(data_frame=dff_fig1, x="effective_month", y="Dials",
                    title='Fig 1 - Number Dials by Effective Month', color="lead_status",
                    hover_name='app_rate', hover_data=['app_rate'], barmode="stack", template="seaborn")

        fig1.update_layout(
            xaxis_title="Effective Month",
            xaxis = dict(
                tickmode = 'linear'
            ),
        )
    except Exception as ex:
        fig1 = {}
        print(ex)

    return fig1

@app.callback(
    Output('leads_lead_status_by_effective_month_fig2', 'figure'),
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date'),
     Input('class_code_dropdown', 'value'),
     Input('sales_rep_dropdown', 'value')])
def update_data(start_date, end_date, class_code, sales_rep):
    dff = df_engagements_leads.copy()

    if (sales_rep != 'ALL') and (sales_rep is not None):
        dff = dff[dff['updated_by'] == sales_rep]

    if (class_code != 'ALL') and (class_code is not None):
        dff = dff[dff['governing_class_code'] == class_code]

    if start_date is not None:
        st_date = date.fromisoformat(start_date)
        dff = dff[dff['activity_date'] >=
                            datetime(st_date.year, st_date.month, st_date.day)]
    if end_date is not None:
        end_date = date.fromisoformat(end_date)

        dff = dff[dff['activity_date'] <
                        datetime(end_date.year, end_date.month, end_date.day)]

    try:
        dff['effective_month'] = pd.Categorical(dff['effective_month'], categories=months, ordered=True)
        dff.sort_values(by='effective_month', ascending=True, inplace=True)

        dff_fig2 = dff.sort_values(by="activity_date").drop_duplicates(subset=["lead"], keep="last")
        dff_fig2 = dff_fig2.groupby(by=["effective_month", "lead_status"]).size().reset_index(name="Leads")

        dff_fig2 = dff_fig2.groupby(by=["effective_month"]).apply(lambda x: app_rate_to_group(x, 'Leads'))

        fig2 = px.bar(data_frame=dff_fig2, x="effective_month", y="Leads",
                    title='Fig 2 - Number Leads by Effective Month', color="lead_status",
                    hover_name='app_rate', hover_data=['app_rate'], barmode="stack", template="plotly")

        fig2.update_layout(
            xaxis_title="Effective Month",
            xaxis = dict(
                tickmode = 'linear'
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.35,
                xanchor="right",
                x=1.0
            )
        )
    except Exception as ex:
        fig2 = {}
        print(ex)

    return fig2

@app.callback(
    Output('dials_lead_status_by_call_number_fig3', 'figure'),
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date'),
     Input('class_code_dropdown', 'value'),
     Input('sales_rep_dropdown', 'value'),
     Input('cutoff-slider-fig3', 'value')])
def update_data(start_date, end_date, class_code, sales_rep, cutoff):
    dff = df_engagements_leads.copy()

    if (sales_rep != 'ALL') and (sales_rep is not None):
        dff = dff[dff['updated_by'] == sales_rep]

    if (class_code != 'ALL') and (class_code is not None):
        dff = dff[dff['governing_class_code'] == class_code]

    if start_date is not None:
        st_date = date.fromisoformat(start_date)
        dff = dff[dff['activity_date'] >=
                            datetime(st_date.year, st_date.month, st_date.day)]
    if end_date is not None:
        end_date = date.fromisoformat(end_date)

        dff = dff[dff['activity_date'] <
                        datetime(end_date.year, end_date.month, end_date.day)]

    try:
        dff_fig3 = dff.groupby(by=["call_number"]).filter(
                                            lambda g: g.lead_status.count() > cutoff).groupby(
                                            by=["call_number", "lead_status"]).size(
                                            ).reset_index(name="Dials")

        dff_fig3 = dff_fig3.groupby(by=["call_number"]).apply(lambda x: app_rate_to_group(x, 'Dials'))

        fig3 = px.bar(data_frame=dff_fig3, x="call_number", y="Dials",
                    title='Fig 3 - Number Dials by Call Number', color="lead_status",
                    hover_name='app_rate', hover_data=['app_rate'], barmode="stack", template="simple_white")
        fig3.update_layout(xaxis={"tickmode":"linear", 'categoryorder':'category ascending'},
                            xaxis_title="Call Number")
    except Exception as ex:
        fig3 = {}
        print(ex)

    return fig3

@app.callback(
    Output('dials_lead_status_by_governing_class_code_fig4', 'figure'),
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date'),
     Input('class_code_dropdown', 'value'),
     Input('sales_rep_dropdown', 'value'),
     Input('cutoff-slider-classcode', 'value')])
def update_data(start_date, end_date, class_code, sales_rep, cutoff):
    dff = df_engagements_leads.copy()

    if (sales_rep != 'ALL') and (sales_rep is not None):
        dff = dff[dff['updated_by'] == sales_rep]

    if (class_code != 'ALL') and (class_code is not None):
        dff = dff[dff['governing_class_code'] == class_code]

    if start_date is not None:
        st_date = date.fromisoformat(start_date)
        dff = dff[dff['activity_date'] >=
                            datetime(st_date.year, st_date.month, st_date.day)]
    if end_date is not None:
        end_date = date.fromisoformat(end_date)

        dff = dff[dff['activity_date'] <
                        datetime(end_date.year, end_date.month, end_date.day)]

    try:
        dff_fig4 = dff.groupby(by=["governing_class_code"]).filter(
                                            lambda g: g.lead_status.count() > cutoff).groupby(
                                            by=["governing_class_code", "lead_status"]).size(
                                            ).reset_index(name="Dials")

        dff_fig4 = dff_fig4.groupby(by=["governing_class_code"]).apply(
                                                            lambda x: app_rate_to_group(x, 'Dials'))
        fig4 = px.bar(data_frame=dff_fig4, x="Dials", y="governing_class_code", orientation='h',
                    title='Fig 4 - Number Dials by Governing Class Code', color="lead_status",
                    hover_data=['app_rate'], hover_name='app_rate', barmode="stack", template="ggplot2")
        fig4.update_layout(yaxis={'categoryorder':'total ascending'},
                            xaxis_title="Dials",
                            yaxis_title="Class Code")
    except Exception as ex:
        fig4 = {}
        print(ex)

    return fig4

@app.callback(
    Output('dials_lead_status_by_insurance_group_fig5', 'figure'),
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date'),
     Input('class_code_dropdown', 'value'),
     Input('sales_rep_dropdown', 'value'),
     Input('cutoff-slider-insurance', 'value')])
def update_data(start_date, end_date, class_code, sales_rep, cutoff):
    dff = df_engagements_leads.copy()

    if (sales_rep != 'ALL') and (sales_rep is not None):
        dff = dff[dff['updated_by'] == sales_rep]

    if (class_code != 'ALL') and (class_code is not None):
        dff = dff[dff['governing_class_code'] == class_code]

    if start_date is not None:
        st_date = date.fromisoformat(start_date)
        dff = dff[dff['activity_date'] >=
                            datetime(st_date.year, st_date.month, st_date.day)]
    if end_date is not None:
        end_date = date.fromisoformat(end_date)

        dff = dff[dff['activity_date'] <
                        datetime(end_date.year, end_date.month, end_date.day)]

    try:
        dff_fig5 = dff.groupby(by=["current_coverage_insurers_group_name"]).filter(
                                            lambda g: g.lead_status.count() > cutoff).groupby(
                                            by=["current_coverage_insurers_group_name", "lead_status"]).size(
                                            ).reset_index(name="Dials")
        dff_fig5 = dff_fig5[dff_fig5['current_coverage_insurers_group_name'].str.len() > 0]

        dff_fig5 = dff_fig5.groupby(by=["current_coverage_insurers_group_name"]).apply(
                                                                    lambda x: app_rate_to_group(x, 'Dials'))
        #dff_fig5['test'] = dff_fig5.apply(lambda x: x.Dials + 1, axis=1)

        fig5 = px.bar(data_frame=dff_fig5, x="Dials", y="current_coverage_insurers_group_name", orientation='h',
                    title='Fig 5 - Number Dials by Insurer\'s Group Name', color="lead_status", hover_name="app_rate",
                    hover_data=['app_rate'], barmode="stack", template="plotly_white")
        #fig5.update_traces(texttemplate='%{text:.2s}', textposition='outside')
        fig5.update_layout(yaxis={'categoryorder':'total ascending', "tickmode":"linear"},
                                    uniformtext_minsize=8, uniformtext_mode='hide',
                                    xaxis_title="Dials",
                                    yaxis_title="Insurance Group Name")
    except Exception as ex:
        fig5 = {}
        print(ex)

    return fig5

@app.callback(
    Output('governing-class-code-table', 'data'),
    Output('governing-class-code-table', 'columns'),
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date'),
     Input('class_code_dropdown', 'value'),
     Input('sales_rep_dropdown', 'value')])
def update_data(start_date, end_date, class_code, sales_rep):
    dff = df_engagements_leads.copy()

    if (sales_rep != 'ALL') and (sales_rep is not None):
        dff = dff[dff['updated_by'] == sales_rep]

    if (class_code != 'ALL') and (class_code is not None):
        dff = dff[dff['governing_class_code'] == class_code]

    if start_date is not None:
        st_date = date.fromisoformat(start_date)
        dff = dff[dff['activity_date'] >=
                            datetime(st_date.year, st_date.month, st_date.day)]
    if end_date is not None:
        end_date = date.fromisoformat(end_date)

        dff = dff[dff['activity_date'] <
                        datetime(end_date.year, end_date.month, end_date.day)]

    try:
        dff_dials = dff.groupby('governing_class_code')[['call_connected', 'dm_reached', 'app_started', 'app_submitted']].sum().reset_index()
        dff_leads = dff.sort_values(by="activity_date").drop_duplicates(subset=["lead"], keep="last")
        dff_leads = dff_leads.groupby('governing_class_code')[['is_lead', 'is_active', 'lost']].sum().reset_index()
        dff_merged = dff_leads.merge(dff_dials, how='left', on='governing_class_code')

        #dff_merged.drop(columns=['app_submitted_x'], inplace=True)
        #dff_merged.rename(columns={'app_submitted_y':'app_submitted'},inplace=True)
        dff_merged.sort_values(by=['is_lead'], inplace=True, ascending=False)

        #columns = [{'name': col, 'id': col} for col in dff_merged.columns]
        columns = [{'name': 'Class Code', 'id': 'governing_class_code'},
                    {'name': 'Total', 'id': 'is_lead'},
                    {'name': 'Active', 'id': 'is_active'},
                    {'name': 'Lost', 'id': 'lost'},
                    {'name': 'Connected', 'id': 'call_connected'},
                    {'name': 'DM Reached', 'id': 'dm_reached'},
                    {'name': 'App Started', 'id': 'app_started'},
                    {'name': 'App Submitted', 'id': 'app_submitted'}]
        data = dff_merged.to_dict(orient='records')
    except Exception as ex:
        print(ex)

    return data, columns

@app.callback(
    Output('total-table', 'data'),
    [Input('my-date-picker-range', 'start_date'),
     Input('my-date-picker-range', 'end_date'),
     Input('class_code_dropdown', 'value'),
     Input('sales_rep_dropdown', 'value')])
def update_data(start_date, end_date, class_code, sales_rep):
    dff = df_engagements_leads.copy()

    if (sales_rep != 'ALL') and (sales_rep is not None):
        dff = dff[dff['updated_by'] == sales_rep]

    if (class_code != 'ALL') and (class_code is not None):
        dff = dff[dff['governing_class_code'] == class_code]

    if start_date is not None:
        st_date = date.fromisoformat(start_date)
        dff = dff[dff['activity_date'] >=
                            datetime(st_date.year, st_date.month, st_date.day)]
    if end_date is not None:
        end_date = date.fromisoformat(end_date)

        dff = dff[dff['activity_date'] <
                        datetime(end_date.year, end_date.month, end_date.day)]

    try:
        dff_active = dff[dff['is_active'] == 1].copy()
        dff_app_submitted = dff[dff['app_submitted'] == 1].copy()

        total_leads = len(dff['lead'].unique())
        active_leads_dialed = len(dff_active['lead'].unique())
        leads_app_submitted = len(dff_app_submitted['lead'].unique())
        total_dials = len(dff)
        app_rate = round(float(leads_app_submitted * 100)/float(total_leads), 2)

        data_dict = [{'total_leads':str(total_leads),
                    'active_leads_dialed':str(active_leads_dialed),
                    'app_submitted':str(leads_app_submitted),
                    'total_dials':str(total_dials),
                    'app_rate':(str(app_rate) + '%')}]
    except Exception as ex:
        data_dict = [{'total_leads':str(0),
                    'active_leads_dialed':str(0),
                    'active_leads_not_dialed':str(0),
                    'app_submitted':str(0)}]
        print(ex)

    return data_dict

if __name__ == '__main__':
    app.run_server(debug=False)
