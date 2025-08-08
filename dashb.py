import os
import pandas as pd
import numpy as np
from datetime import datetime
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import kagglehub


DATASET_DIR = kagglehub.dataset_download("joniarroba/noshowappointments")
CSV_FILE = os.path.join(DATASET_DIR, "KaggleV2-May-2016.csv")
df = pd.read_csv(CSV_FILE)


df.columns = [col.strip().replace('-', '_').replace(' ', '_').lower() for col in df.columns]

data = df.copy()


if 'no_show' not in data.columns and 'noshow' in data.columns:
    data = data.rename(columns={'noshow': 'no_show'})
data['no_show'] = data['no_show'].str.strip().str.lower().map({'no': 0, 'yes': 1}).astype(int)


for date_col in ['scheduledday', 'appointmentday']:
    if date_col in data.columns:
        data[date_col] = pd.to_datetime(data[date_col], errors='coerce')


if 'scheduledday' in data.columns and 'appointmentday' in data.columns:
    data['wait_days'] = (data['appointmentday'].dt.date - data['scheduledday'].dt.date).apply(lambda x: x.days if pd.notnull(x) else np.nan)
    data['wait_days'] = data['wait_days'].clip(lower=0)  # No negative waits


if 'appointmentday' in data.columns:
    data['appointment_weekday'] = data['appointmentday'].dt.day_name()


data['age'] = pd.to_numeric(data['age'], errors='coerce').fillna(0).astype(int)
data.loc[data['age'] < 0, 'age'] = 0
age_bins = [-1, 12, 18, 30, 45, 65, 120]
age_labels = ['Child', 'Teen', 'Young Adult', 'Adult', 'Middle Age', 'Senior']
data['age_group'] = pd.cut(data['age'], bins=age_bins, labels=age_labels)


medical_cols = ['diabetes', 'hypertension', 'alcoholism', 'handicap', 'sms_received', 'scholarship']
for col in medical_cols:
    if col in data.columns:
        data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0).astype(int)


if 'neighbourhood' in data.columns:
    data['neighbourhood'] = data['neighbourhood'].astype(str).str.title()


TOTAL_ROWS = len(data)
SHOW_RATE = 1 - data['no_show'].mean()


app = dash.Dash(__name__, title="Medical Appointment Dashboard")
server = app.server  # for deploying if needed


gender_options = [{'label': g, 'value': g} for g in sorted(data['gender'].unique())] if 'gender' in data.columns else []
neighbourhood_options = [{'label': n, 'value': n} for n in data['neighbourhood'].value_counts().index[:50]] if 'neighbourhood' in data.columns else []
age_min, age_max = int(data['age'].min()), int(data['age'].max())


app.layout = html.Div([
    html.H1("Medical Appointment No-Show Dashboard"),
    html.P(f"Total records: {TOTAL_ROWS:,} • Show rate: {SHOW_RATE:.1%}"),

    
    html.Div([
        html.Label("Filter by Gender:"),
        dcc.Dropdown(id='gender-filter', options=gender_options, multi=True, placeholder="Select genders"),
    ]),

    html.Div([
        html.Label("Filter by Neighborhood:"),
        dcc.Dropdown(id='neigh-filter', options=neighbourhood_options, multi=True, placeholder="Select neighborhoods"),
    ]),

    html.Div([
        html.Label("Filter by Age:"),
        dcc.RangeSlider(id='age-slider', min=age_min, max=age_max, value=[age_min, age_max],
                        marks={age_min: str(age_min), age_max: str(age_max)}),
    ]),

   
    dcc.Graph(id='pie-show-no-show'),
    dcc.Graph(id='age-gender-hist'),
    dcc.Graph(id='weekday-bar'),
    dcc.Graph(id='neighbourhood-top'),
    dcc.Graph(id='conditions-heat'),
    dcc.Graph(id='waitdays-scatter'),

    html.P("Use the filters above to explore the data. Hover over charts for details."),
])



def filter_data(genders, neighs, age_range):
    filtered = data.copy()
    if genders:
        filtered = filtered[filtered['gender'].isin(genders)]
    if neighs:
        filtered = filtered[filtered['neighbourhood'].isin(neighs)]
    if age_range:
        low, high = age_range
        filtered = filtered[(filtered['age'] >= low) & (filtered['age'] <= high)]
    return filtered



@app.callback(
    Output('pie-show-no-show', 'figure'),
    Output('age-gender-hist', 'figure'),
    Output('weekday-bar', 'figure'),
    Output('neighbourhood-top', 'figure'),
    Output('conditions-heat', 'figure'),
    Output('waitdays-scatter', 'figure'),
    Input('gender-filter', 'value'),
    Input('neigh-filter', 'value'),
    Input('age-slider', 'value'),
)
def update_dashboard(selected_genders, selected_neighs, selected_ages):
    d = filter_data(selected_genders, selected_neighs, selected_ages)

    
    pie = px.pie(d, names=d['no_show'].map({0: 'Showed', 1: 'No-Show'}), title="Show vs No-Show", hole=0.4)
    pie.update_traces(textinfo='percent+label')

    m
    if 'gender' in d.columns:
        hist = px.histogram(d, x='age', color=d['no_show'].map({0: 'Showed', 1: 'No-Show'}),
                           barmode='overlay', nbins=30, facet_col='gender',
                           title="Age Distribution by Gender and Attendance")
    else:
        hist = px.histogram(d, x='age', color=d['no_show'].map({0: 'Showed', 1: 'No-Show'}),
                           nbins=30, title="Age Distribution and Attendance")

    if 'appointment_weekday' in d.columns:
        weekday_counts = d.groupby('appointment_weekday').agg(total=('no_show', 'count'), no_show=('no_show', 'sum')).reset_index()
        order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_counts['appointment_weekday'] = pd.Categorical(weekday_counts['appointment_weekday'], categories=order, ordered=True)
        weekday_counts = weekday_counts.sort_values('appointment_weekday')
        weekday_counts['show_rate'] = 1 - weekday_counts['no_show'] / weekday_counts['total']
        weekday_bar = px.bar(weekday_counts, x='appointment_weekday', y='show_rate',
                             title="Show Rate by Weekday", labels={'show_rate': 'Show Rate', 'appointment_weekday': 'Weekday'})
        weekday_bar.update_yaxes(tickformat=".0%")
    else:
        weekday_bar = px.bar(title="No weekday data")

   
    if 'neighbourhood' in d.columns:
        top_neigh = d['neighbourhood'].value_counts().nlargest(15).index
        neigh_df = d[d['neighbourhood'].isin(top_neigh)]
        neigh_summary = neigh_df.groupby(['neighbourhood', 'no_show']).size().reset_index(name='count')
        neigh_summary['status'] = neigh_summary['no_show'].map({0: 'Showed', 1: 'No-Show'})
        neigh_bar = px.bar(neigh_summary, x='neighbourhood', y='count', color='status',
                           title="Top 15 Neighborhoods by Appointments (Stacked)")
        neigh_bar.update_layout(xaxis_tickangle=-45)
    else:
        neigh_bar = px.bar(title="No neighborhood data")

    conditions = [c for c in medical_cols if c in d.columns]
    if conditions:
        cond_stats = []
        for c in conditions:
            grouped = d.groupby(c).agg(total=('no_show', 'count'), no_show=('no_show', 'sum')).reset_index()
            if 1 in grouped[c].values:
                cond_present = grouped[grouped[c] == 1]
                total = cond_present['total'].sum()
                no_show = cond_present['no_show'].sum()
                show_rate_cond = 1 - (no_show / total) if total > 0 else np.nan
            else:
                show_rate_cond = np.nan
            cond_stats.append({'condition': c, 'show_rate': show_rate_cond})
        cond_df = pd.DataFrame(cond_stats)
        cond_heat = px.bar(cond_df, y='condition', x='show_rate', orientation='h',
                          title="Show Rate When Condition is Present")
        cond_heat.update_xaxes(tickformat=".0%")
    else:
        cond_heat = px.bar(title="No medical condition data")

   
    if 'wait_days' in d.columns:
        wait = d.dropna(subset=['wait_days']).copy()
        wait['wait_bin'] = pd.cut(wait['wait_days'], bins=[-1, 0, 1, 3, 7, 14, 30, 60, 365],
                                  labels=['0', '1', '2-3', '4-7', '8-14', '15-30', '31-60', '60+'])
        wait_bin_stats = wait.groupby('wait_bin').agg(total=('no_show', 'count'), no_show=('no_show', 'sum')).reset_index()
        wait_bin_stats['no_show_rate'] = wait_bin_stats['no_show'] / wait_bin_stats['total']
        wait_fig = px.scatter(wait_bin_stats, x='wait_bin', y='no_show_rate', size='total',
                              title="No-Show Rate by Wait-Time Bin", labels={'wait_bin': 'Wait (days)', 'no_show_rate': 'No-show rate'})
        wait_fig.update_yaxes(tickformat=".0%")
    else:
        wait_fig = px.scatter(title="No wait time data")

    return pie, hist, weekday_bar, neigh_bar, cond_heat, wait_fig


if __name__ == '__main__':
   
    app.run(debug=True)
