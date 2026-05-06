import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from data_processing import (
    load_and_preprocess_data, 
    compute_statistics, 
    get_funnel_data, 
    get_time_series, 
    get_geo_data, 
    get_behavior_data,
    get_device_browser_data
)

# Initialize Dash App
app = dash.Dash(__name__, 
                suppress_callback_exceptions=True,
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])
server = app.server

# Constants
CSV_PATH = "synthetic_web_logs.csv"
THEME_TEMPLATE = "plotly_dark"

# Pre-load data for initial sizing
FULL_DF = load_and_preprocess_data(CSV_PATH)

# --- Components ---

def make_kpi_card(label, value, id):
    return html.Div([
        html.Div(label, className="kpi-label"),
        html.Div(value, className="kpi-value", id=id)
    ], className="card kpi-card")

def make_chart_card(title, chart_id, className=""):
    return html.Div([
        html.H3(title, style={"fontSize": "1rem", "marginBottom": "1rem", "color": "#94a3b8"}),
        dcc.Graph(id=chart_id, config={'displayModeBar': False}, style={"height": "350px"})
    ], className=f"card {className}")

# --- Layout Components ---

def get_header(active_tab):
    return html.Div([
        html.Div([
            html.Button("☰", id="btn-toggle-sidebar", className="nav-item", style={"fontSize": "1.25rem", "padding": "0.5rem"}),
            html.Img(src="/assets/logo.png", style={"height": "32px", "marginLeft": "12px"}),
            html.Span("LogSense AI", className="header-brand", style={"marginLeft": "8px"})
        ], style={"display": "flex", "alignItems": "center"}),
        html.Div([
            html.Button("Overview", id="btn-overview", className=f"nav-item {'active' if active_tab == 'overview' else ''}"),
            html.Button("Geographic", id="btn-geo", className=f"nav-item {'active' if active_tab == 'geo' else ''}"),
            html.Button("Technology", id="btn-tech", className=f"nav-item {'active' if active_tab == 'tech' else ''}"),
            html.Button("Data Explorer", id="btn-data", className=f"nav-item {'active' if active_tab == 'data' else ''}"),
        ], className="nav-tabs")
    ], className="top-header")

def get_sidebar():
    return html.Div([
        html.Div("Analysis Filters", className="sidebar-header"),
        
        html.Div([
            html.Label("Country Origin", className="filter-label"),
            dcc.Dropdown(
                id="filter-country",
                options=[{"label": c, "value": c} for c in sorted(FULL_DF['country'].unique())],
                placeholder="Global View",
                className="custom-dropdown"
            ),
        ], className="filter-group"),

        html.Div([
            html.Label("Request Type", className="filter-label"),
            dcc.Dropdown(
                id="filter-type",
                options=[{"label": t.replace('_', ' ').title(), "value": t} for t in FULL_DF['request_type'].unique()],
                placeholder="All Actions"
            ),
        ], className="filter-group"),

        html.Div([
            html.Label("Device Segment", className="filter-label"),
            dcc.Dropdown(
                id="filter-device",
                options=[{"label": d, "value": d} for d in FULL_DF['device_type'].unique()],
                placeholder="All Devices"
            ),
        ], className="filter-group"),

        html.Div([
            html.Label("Browser Segment", className="filter-label"),
            dcc.Dropdown(
                id="filter-browser",
                options=[{"label": b, "value": b} for b in FULL_DF['browser'].unique()],
                placeholder="All Browsers"
            ),
        ], className="filter-group"),

        # Persistent Pagination Controls (Hidden when not in Data tab)
        html.Div([
            html.Div("Explorer Controls", className="sidebar-header", style={"marginTop": "2rem"}),
            html.Div(id="pagination-info", style={"fontSize": "0.75rem", "color": "#94a3b8", "marginBottom": "1rem"}),
            html.Div([
                html.Button("← Prev", id="btn-prev", className="nav-item", style={"flex": "1", "padding": "0.5rem"}),
                html.Button("Next →", id="btn-next", className="nav-item", style={"flex": "1", "padding": "0.5rem", "marginLeft": "8px"}),
            ], style={"display": "flex"})
        ], id="explorer-controls-sidebar", style={"display": "none"})

    ], id="sidebar-nav", className="sidebar-container")

# --- Page Layouts ---

def layout_overview():
    return html.Div([
        html.Div([
            html.Div([
                html.Div("Total Traffic", className="kpi-card-title"),
                html.Div(id="kpi-total", className="kpi-card-value")
            ], className="kpi-card bg-blue"),
            html.Div([
                html.Div("Job Applications", className="kpi-card-title"),
                html.Div(id="kpi-jobs", className="kpi-card-value")
            ], className="kpi-card bg-green"),
            html.Div([
                html.Div("Demo Requests", className="kpi-card-title"),
                html.Div(id="kpi-demos", className="kpi-card-value")
            ], className="kpi-card bg-red"),
        ], className="kpi-grid"),

        html.Div([
            html.Div([
                html.Div([
                    html.Div("Traffic Velocity per Hour", className="card-title"),
                    html.Div("Real-time Trends", className="chart-badge")
                ], className="card-header"),
                dcc.Graph(id="chart-trends", style={"height": "350px"})
            ], className="card"),
            
            html.Div([
                html.Div([
                    html.Div("Action Intensity Breakdown", className="card-title"),
                    html.Div("User Behavior", className="chart-badge")
                ], className="card-header"),
                dcc.Graph(id="chart-behavior", style={"height": "350px"})
            ], className="card"),
        ], className="grid-cols-2", style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "1.5rem"}),

        html.Div([
            html.Div([
                html.Div([
                    html.Div("Regional Traffic Leaders", className="card-title"),
                    html.Div("Top 10 Countries", className="chart-badge")
                ], className="card-header"),
                dcc.Graph(id="chart-top-countries", style={"height": "300px"})
            ], className="card"),
            
            html.Div([
                html.Div([
                    html.Div("Response Health Status", className="card-title"),
                    html.Div("HTTP Codes", className="chart-badge")
                ], className="card-header"),
                dcc.Graph(id="chart-status-codes", style={"height": "300px"})
            ], className="card"),
        ], className="grid-cols-2", style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "1.5rem"}),
    ])

def layout_geo():
    return html.Div([
        html.Div([
            html.Div([
                html.Div("Global Request Distribution", className="card-title"),
                html.Div("Heatmap", className="chart-badge")
            ], className="card-header"),
            dcc.Graph(id="chart-geo-main", style={"height": "600px"})
        ], className="card")
    ])

def layout_tech():
    return html.Div([
        html.Div([
            html.Div([
                html.Div("Device Segment Performance", className="card-title"),
                html.Div("Hardware distribution", className="chart-badge")
            ], className="card-header"),
            dcc.Graph(id="chart-tech-device", style={"height": "350px"})
        ], className="card"),
        html.Div([
            html.Div([
                html.Div("Browser Engine Usage", className="card-title"),
                html.Div("Software distribution", className="chart-badge")
            ], className="card-header"),
            dcc.Graph(id="chart-tech-browser", style={"height": "350px"})
        ], className="card")
    ], className="grid-row")

def layout_data():
    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.Div("Raw Log Inspector", className="card-title"),
                    html.Div("Interactive Dataset", className="chart-badge")
                ], className="card-header"),
                
                html.Div(id="data-table-container")
            ])
        ], className="card")
    ])

# --- Main App Layout ---

# --- Main App Layout ---

app.layout = html.Div([
    dcc.Store(id="active-tab", data="overview"),
    dcc.Store(id="current-page", data=0),
    dcc.Store(id="sidebar-visible", data=True),
    
    # Static Navigation (Always present)
    html.Div(id="header-placeholder"), 
    get_sidebar(),
    
    # All Page Layouts (Hidden/Shown via CSS)
    html.Div([
        html.Div(layout_overview(), id="tab-overview-content", style={"display": "block"}),
        html.Div(layout_geo(), id="tab-geo-content", style={"display": "none"}),
        html.Div(layout_tech(), id="tab-tech-content", style={"display": "none"}),
        html.Div(layout_data(), id="tab-data-content", style={"display": "none"}),
    ], id="tab-content", className="main-content")
])

# Toggle Sidebar Callback
@app.callback(
    Output("sidebar-visible", "data"),
    Input("btn-toggle-sidebar", "n_clicks"),
    State("sidebar-visible", "data"),
    prevent_initial_call=True
)
def toggle_sidebar(n, visible):
    return not visible

@app.callback(
    Output("sidebar-nav", "className"),
    Output("tab-content", "className"),
    Input("sidebar-visible", "data")
)
def update_sidebar_visibility(visible):
    sidebar_class = "sidebar-container" if visible else "sidebar-container sidebar-hidden"
    content_class = "main-content" if visible else "main-content content-expanded"
    return sidebar_class, content_class

# Initialize Header content
@app.callback(
    Output("header-placeholder", "children"),
    Input("active-tab", "data")
)
def update_header(active_tab):
    return get_header(active_tab)

@app.callback(
    Output("active-tab", "data"),
    Input("btn-overview", "n_clicks"),
    Input("btn-geo", "n_clicks"),
    Input("btn-tech", "n_clicks"),
    Input("btn-data", "n_clicks"),
    prevent_initial_call=True
)
def update_tab(*args):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    return button_id.replace("btn-", "")

@app.callback(
    Output("explorer-controls-sidebar", "style"),
    Input("active-tab", "data")
)
def toggle_explorer_controls(active_tab):
    if active_tab == "data":
        return {"display": "block"}
    return {"display": "none"}

@app.callback(
    Output("current-page", "data"),
    Input("btn-prev", "n_clicks"),
    Input("btn-next", "n_clicks"),
    Input("filter-country", "value"),
    Input("filter-type", "value"),
    Input("filter-device", "value"),
    Input("filter-browser", "value"),
    State("current-page", "data"),
    prevent_initial_call=True
)
def update_page(n_prev, n_next, c, t, d, b, current):
    ctx = dash.callback_context
    if not ctx.triggered:
        return 0
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger in ["filter-country", "filter-type", "filter-device", "filter-browser"]:
        return 0
    
    if trigger == "btn-prev":
        return max(0, current - 1)
    if trigger == "btn-next":
        return current + 1
    return 0

@app.callback(
    Output("tab-overview-content", "style"),
    Output("tab-geo-content", "style"),
    Output("tab-tech-content", "style"),
    Output("tab-data-content", "style"),
    Input("active-tab", "data")
)
def update_tab_visibility(active_tab):
    styles = [{"display": "none"}] * 4
    if active_tab == "overview": styles[0] = {"display": "block"}
    elif active_tab == "geo": styles[1] = {"display": "block"}
    elif active_tab == "tech": styles[2] = {"display": "block"}
    elif active_tab == "data": styles[3] = {"display": "block"}
    return styles

# --- Analysis Callbacks (Modularized to prevent ReferenceErrors) ---

@app.callback(
    Output("kpi-total", "children"),
    Output("kpi-jobs", "children"),
    Output("kpi-demos", "children"),
    Output("chart-trends", "figure"),
    Output("chart-behavior", "figure"),
    Output("chart-top-countries", "figure"),
    Output("chart-status-codes", "figure"),
    Input("filter-country", "value"),
    Input("filter-type", "value"),
    Input("filter-device", "value"),
    Input("filter-browser", "value"),
    Input("active-tab", "data")
)
def update_overview(country, rtype, device, browser, tab):
    if tab != "overview": return [dash.no_update] * 7
    
    dff = FULL_DF.copy()
    if country: dff = dff[dff['country'] == country]
    if rtype: dff = dff[dff['request_type'] == rtype]
    if device: dff = dff[dff['device_type'] == device]
    if browser: dff = dff[dff['browser'] == browser]
    
    stats = compute_statistics(dff)
    
    # 1. Trends
    trends_df = get_time_series(dff)
    fig_trends = px.line(trends_df, x='hour', y='count', markers=True)
    fig_trends.update_traces(line_color='#3b82f6', fill='tozeroy', fillcolor='rgba(59, 130, 246, 0.1)')
    fig_trends.update_layout(template="plotly_white", margin=dict(t=10, b=10, l=10, r=10), xaxis_title="Hour of Day", yaxis_title="Requests")
    
    # 2. Behavior
    behavior_df = get_behavior_data(dff)
    fig_behavior = px.bar(behavior_df, x='count', y='request_type', orientation='h', color='count', color_continuous_scale='Blues')
    fig_behavior.update_layout(template="plotly_white", margin=dict(t=10, b=10, l=10, r=10), showlegend=False, coloraxis_showscale=False)

    # 3. Top Countries (Bar)
    country_counts = dff['country'].value_counts().head(10).reset_index()
    country_counts.columns = ['country', 'count']
    fig_countries = px.bar(country_counts, x='country', y='count', color='count', color_continuous_scale='Blues')
    fig_countries.update_layout(template="plotly_white", margin=dict(t=10, b=10, l=10, r=10), showlegend=False, coloraxis_showscale=False)

    # 4. Status Codes (Pie)
    status_counts = dff['status_code'].value_counts().reset_index()
    status_counts.columns = ['status_code', 'count']
    status_counts['status_code'] = status_counts['status_code'].astype(str)
    fig_status = px.pie(status_counts, values='count', names='status_code', hole=0.5, color_discrete_sequence=px.colors.sequential.Tealgrn_r)
    fig_status.update_layout(template="plotly_white", margin=dict(t=20, b=20, l=20, r=20))
    
    return (
        f"{stats['total_requests']:,}",
        f"{stats['job_apps']:,}",
        f"{stats['demo_requests']:,}",
        fig_trends, fig_behavior, fig_countries, fig_status
    )

@app.callback(
    Output("chart-geo-main", "figure"),
    Input("filter-country", "value"),
    Input("filter-type", "value"),
    Input("filter-device", "value"),
    Input("filter-browser", "value"),
    Input("active-tab", "data")
)
def update_geo(country, rtype, device, browser, tab):
    if tab != "geo": return dash.no_update
    
    dff = FULL_DF.copy()
    if country: dff = dff[dff['country'] == country]
    if rtype: dff = dff[dff['request_type'] == rtype]
    if device: dff = dff[dff['device_type'] == device]
    if browser: dff = dff[dff['browser'] == browser]
    
    geo_df = get_geo_data(dff)
    fig_geo = px.choropleth(geo_df, locations="country", locationmode='country names', color="count", color_continuous_scale="Blues")
    fig_geo.update_layout(template="plotly_white", margin=dict(t=0, b=0, l=0, r=0), geo=dict(bgcolor='rgba(0,0,0,0)', showframe=False))
    
    return fig_geo

@app.callback(
    Output("chart-tech-device", "figure"),
    Output("chart-tech-browser", "figure"),
    Input("filter-country", "value"),
    Input("filter-type", "value"),
    Input("filter-device", "value"),
    Input("filter-browser", "value"),
    Input("active-tab", "data")
)
def update_tech(country, rtype, device, browser, tab):
    if tab != "tech": return dash.no_update, dash.no_update
    
    dff = FULL_DF.copy()
    if country: dff = dff[dff['country'] == country]
    if rtype: dff = dff[dff['request_type'] == rtype]
    if device: dff = dff[dff['device_type'] == device]
    if browser: dff = dff[dff['browser'] == browser]
    
    dev_df, brow_df = get_device_browser_data(dff)
    fig_device = px.pie(dev_df, values='count', names='device_type', hole=0.5, color_discrete_sequence=px.colors.sequential.Blues_r)
    fig_browser = px.pie(brow_df, values='count', names='browser', hole=0.5, color_discrete_sequence=px.colors.sequential.Greens_r)
    
    fig_device.update_layout(template="plotly_white", margin=dict(t=20, b=20, l=20, r=20))
    fig_browser.update_layout(template="plotly_white", margin=dict(t=20, b=20, l=20, r=20))
    
    return fig_device, fig_browser

@app.callback(
    Output("data-table-container", "children"),
    Output("pagination-info", "children"),
    Input("filter-country", "value"),
    Input("filter-type", "value"),
    Input("filter-device", "value"),
    Input("filter-browser", "value"),
    Input("active-tab", "data"),
    Input("current-page", "data")
)
def update_data(country, rtype, device, browser, tab, page):
    if tab != "data": return dash.no_update, dash.no_update
    
    dff = FULL_DF.copy()
    if country: dff = dff[dff['country'] == country]
    if rtype: dff = dff[dff['request_type'] == rtype]
    if device: dff = dff[dff['device_type'] == device]
    if browser: dff = dff[dff['browser'] == browser]
    
    total_rows = len(dff)
    rows_per_page = 100
    start = page * rows_per_page
    end = min(start + rows_per_page, total_rows)
    
    cols = ['timestamp', 'ip_address', 'http_method', 'url_requested', 'status_code', 'country', 'device_type', 'browser', 'request_type']
    
    table_header = html.Thead(html.Tr([html.Th(c.replace('_', ' ').title()) for c in cols]))
    table_body = html.Tbody([
        html.Tr([html.Td(str(dff.iloc[i][c])) for c in cols])
        for i in range(start, end)
    ])
    
    info_text = f"Showing {start+1:,} - {end:,} of {total_rows:,} entries"
    if total_rows == 0: info_text = "No entries found"
    
    return html.Table([table_header, table_body], className="data-table"), info_text

if __name__ == '__main__':
    app.run(debug=True)
