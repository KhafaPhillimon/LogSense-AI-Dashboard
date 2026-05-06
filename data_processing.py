import pandas as pd
import numpy as np

def load_and_preprocess_data(filepath):
    """Load CSV and perform initial cleaning/parsing."""
    df = pd.read_csv(filepath)
    
    # Convert timestamp to datetime (using a dummy date for time-series analysis)
    # Since the log has HH:MM:SS, we'll prefix it with a reference date
    df['dt'] = pd.to_datetime('2026-05-04 ' + df['timestamp'])
    df['hour'] = df['dt'].dt.hour
    
    # Ensure numeric status codes
    df['status_code'] = pd.to_numeric(df['status_code'], errors='coerce')
    
    return df

def compute_statistics(df):
    """Compute top-level KPI metrics."""
    total_requests = len(df)
    job_apps = len(df[df['request_type'] == 'job_application'])
    demo_requests = len(df[df['request_type'] == 'demo_request'])
    ai_usage = len(df[df['request_type'] == 'ai_usage'])
    
    # Conversion Rate: Demo Requests / Pricing Visits
    pricing_visits = len(df[df['url_requested'] == '/pricing'])
    conversion_rate = (demo_requests / pricing_visits * 100) if pricing_visits > 0 else 0
    
    # Hourly stats
    hourly_counts = df.groupby('hour').size()
    mean_req = hourly_counts.mean()
    std_req = hourly_counts.std()
    
    return {
        "total_requests": total_requests,
        "job_apps": job_apps,
        "demo_requests": demo_requests,
        "ai_usage": ai_usage,
        "conversion_rate": conversion_rate,
        "mean_req": mean_req,
        "std_req": std_req
    }

def get_funnel_data(df):
    """Product -> Pricing -> Demo Request."""
    stages = {
        "Product Page": len(df[df['url_requested'] == '/products']),
        "Pricing Page": len(df[df['url_requested'] == '/pricing']),
        "Demo Request": len(df[df['request_type'] == 'demo_request'])
    }
    return pd.DataFrame({
        "number": list(stages.values()),
        "stage": list(stages.keys())
    })

def get_time_series(df):
    """Requests per hour."""
    return df.groupby('hour').size().reset_index(name='count')

def get_geo_data(df):
    """Requests by country."""
    return df.groupby('country').size().reset_index(name='count').sort_values('count', ascending=False)

def get_behavior_data(df):
    """Requests by type."""
    return df.groupby('request_type').size().reset_index(name='count').sort_values('count', ascending=False)

def get_device_browser_data(df):
    """Distributions for pie charts."""
    devices = df.groupby('device_type').size().reset_index(name='count')
    browsers = df.groupby('browser').size().reset_index(name='count')
    return devices, browsers
