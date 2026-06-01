import os
import requests
import pandas as pd
import numpy as np
import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import time

FRED_API_KEY    = os.environ['FRED_API_KEY']
EMAIL_ADDRESS   = os.environ['EMAIL_ADDRESS']
EMAIL_PASSWORD  = os.environ['EMAIL_PASSWORD']

TODAY          = datetime.today().strftime('%Y-%m-%d')
TWO_YEARS_AGO  = (datetime.today() - timedelta(days=730)).strftime('%Y-%m-%d')
THREE_YEARS_AGO = (datetime.today() - timedelta(days=1095)).strftime('%Y-%m-%d')

def get_treasury_yields():
    url_30 = f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS30&api_key={FRED_API_KEY}&file_type=json&observation_start={TWO_YEARS_AGO}"
    url_10 = f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS10&api_key={FRED_API_KEY}&file_type=json&observation_start={TWO_YEARS_AGO}"

    response_30 = requests.get(url_30).json()
    if 'observations' not in response_30:
        raise ValueError(f"FRED API error for 30yr: {response_30}")
    df_30 = pd.DataFrame(response_30['observations'])
    df_30 = df_30[df_30['value'] != '.']
    df_30['value'] = df_30['value'].astype(float)
    df_30['date']  = pd.to_datetime(df_30['date'])

    time.sleep(1)  

    response_10 = requests.get(url_10).json()
    if 'observations' not in response_10:
        raise ValueError(f"FRED API error for 10yr: {response_10}")
    df_10 = pd.DataFrame(response_10['observations'])
    df_10 = df_10[df_10['value'] != '.']
    df_10['value'] = df_10['value'].astype(float)
    df_10['date']  = pd.to_datetime(df_10['date'])

    latest_30 = df_30['value'].iloc[-1]
    latest_10 = df_10['value'].iloc[-1]

    print(f"30yr Yield: {latest_30}%")
    print(f"10yr Yield: {latest_10}%")

    return latest_30, latest_10

def get_cpi_data():
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=CPIAUCSL&api_key={FRED_API_KEY}&file_type=json&observation_start={THREE_YEARS_AGO}"
    
    response = requests.get(url).json()

    if 'observations' not in response:
        print(f"FRED API error: {response}")
        raise ValueError(f"FRED API did not return observations. Response: {response}")
    
    df = pd.DataFrame(response['observations'])
    df = df[df['value'] != '.']
    df['value'] = df['value'].astype(float)
    df['date']  = pd.to_datetime(df['date'])
    df = df.reset_index(drop=True)
    df['yoy_change'] = df['value'].pct_change(12) * 100
    df = df.dropna(subset=['yoy_change'])

    latest_cpi = df['yoy_change'].iloc[-1]
    prev_cpi   = df['yoy_change'].iloc[-2]

    print(f"CPI: {latest_cpi:.2f}%")

    return latest_cpi, prev_cpi

def get_jobs_data():
    url = f"https://api.stlouisfed.org/fred/series/observations?series_id=PAYEMS&api_key={FRED_API_KEY}&file_type=json&observation_start={TWO_YEARS_AGO}"

    response = requests.get(url).json()
    if 'observations' not in response:
        raise ValueError(f"FRED API error for jobs: {response}")
    df = pd.DataFrame(response['observations'])
    df = df[df['value'] != '.']
    df['value'] = df['value'].astype(float)
    df['date']  = pd.to_datetime(df['date'])
    df['monthly_change'] = df['value'].diff() * 1000
    df = df.dropna(subset=['monthly_change'])

    latest_jobs = df['monthly_change'].iloc[-1]

    print(f"NFP: {latest_jobs:,.0f}")

    return latest_jobs

def get_oil_prices():
    brent = yf.download('BZ=F', period='5d', progress=False, auto_adjust=True)
    wti   = yf.download('CL=F', period='5d', progress=False, auto_adjust=True)

    latest_brent = float(brent['Close'].dropna().iloc[-1].iloc[0])
    latest_wti   = float(wti['Close'].dropna().iloc[-1].iloc[0])

    print(f"Brent: ${latest_brent:.2f}")
    print(f"WTI:   ${latest_wti:.2f}")

    return latest_brent, latest_wti

def get_tlt_price():
    tlt = yf.download('TLT', period='5d', progress=False, auto_adjust=True)

    latest_tlt = float(tlt['Close'].dropna().iloc[-1].iloc[0])

    print(f"TLT: ${latest_tlt:.2f}")

    return latest_tlt

def calculate_signals(
    latest_30, latest_10,
    latest_cpi, prev_cpi,
    latest_jobs,
    latest_brent, latest_wti,
    latest_tlt
):
    y_score = 0
    if latest_30 >= 5.0:
        y_score += 1
    elif latest_30 < 4.5:
        y_score -= 1

    spread = latest_30 - latest_10
    if spread > 0.6:
        y_score += 1
    elif spread < 0.4:
        y_score -= 1

    c_score = 0
    if latest_cpi < prev_cpi:
        c_score += 2 if latest_cpi < 3.0 else 1
    else:
        c_score -= 2 if latest_cpi > 4.0 else 1

    j_score = 0
    if latest_jobs < 100000:
        j_score += 2
    elif latest_jobs < 150000:
        j_score += 1
    elif latest_jobs < 200000:
        j_score += 0
    elif latest_jobs < 250000:
        j_score -= 1
    else:
        j_score -= 2

    o_score = 0
    if latest_brent > 100:
        o_score -= 2
    elif latest_brent > 85:
        o_score -= 1
    elif latest_brent > 70:
        o_score += 0
    elif latest_brent > 60:
        o_score += 1
    else:
        o_score += 2

    contango = latest_brent - latest_wti
    if contango > 10:
        o_score -= 1
    elif contango < 3:
        o_score += 1

    t_score = 0
    if latest_tlt < 85:
        t_score -= 1
    elif latest_tlt < 90:
        t_score += 0
    elif latest_tlt < 95:
        t_score += 1
    else:
        t_score += 2

    total = y_score + c_score + j_score + o_score + t_score

    if total >= 5:
        signal = 'STRONG BUY'
    elif total >= 2:
        signal = 'BUY'
    elif total >= -1:
        signal = 'NEUTRAL'
    elif total >= -4:
        signal = 'WAIT'
    else:
        signal = 'STRONG AVOID'

    return total, signal, y_score, c_score, j_score, o_score, t_score

def send_alert(
    total_score, signal,
    latest_30, latest_10,
    latest_cpi, prev_cpi,
    latest_jobs,
    latest_brent, latest_wti,
    latest_tlt,
    force_send=False
):
    notable = ['BUY', 'STRONG BUY', 'STRONG AVOID']
    if not force_send and not any(s in signal for s in notable):
        print(f"Signal is {signal} - no email sent")
        return

    body = f"""
RATES TRADING SIGNAL UPDATE
{datetime.today().strftime('%B %d, %Y %H:%M')}

SIGNAL: {signal}
TOTAL SCORE: {total_score} / 9

MARKET DATA
30yr Yield:  {latest_30}%
10yr Yield:  {latest_10}%
CPI:         {latest_cpi:.2f}%
Prev CPI:    {prev_cpi:.2f}%
NFP Jobs:    {latest_jobs:,.0f}
Brent Oil:   ${latest_brent:.2f}
WTI Oil:     ${latest_wti:.2f}
TLT:         ${latest_tlt:.2f}

KEY THINGS TO WATCH
{'CPI cooling needed - next print coming' if latest_cpi > 3.5 else 'CPI trending in right direction'}
{'Iran ceasefire would be major catalyst' if latest_brent > 90 else 'Oil prices normalizing'}
{'30yr at historic entry point' if latest_30 > 5.0 else 'Yields not yet attractive'}
{'Weak jobs supporting rate cut case' if latest_jobs < 150000 else 'Strong jobs keeping Fed hawkish'}

Not financial advice.
    """

    msg = MIMEMultipart()
    msg['From']    = EMAIL_ADDRESS
    msg['To']      = EMAIL_ADDRESS
    msg['Subject'] = f"[RATES SIGNAL] {signal} | Score: {total_score}/9 | {datetime.today().strftime('%b %d %Y')}"
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent - Signal: {signal} Score: {total_score}/9")
    except Exception as e:
        print(f"Email failed: {e}")

def main():
    print("=" * 45)
    print(f"RATES DASHBOARD - {datetime.today().strftime('%B %d, %Y %H:%M')}")
    print("=" * 45)

    
    latest_30, latest_10     = get_treasury_yields()
    time.sleep(2)
    latest_cpi, prev_cpi     = get_cpi_data()
    time.sleep(2)
    latest_jobs              = get_jobs_data()
    time.sleep(2)
    latest_brent, latest_wti = get_oil_prices()
    latest_tlt               = get_tlt_price()

    total_score, signal, y_score, c_score, j_score, o_score, t_score = calculate_signals(
        latest_30, latest_10,
        latest_cpi, prev_cpi,
        latest_jobs,
        latest_brent, latest_wti,
        latest_tlt
    )

    print("\nSIGNAL SUMMARY")
    print("=" * 45)
    print(f"Yield Score:  {y_score:+d}")
    print(f"CPI Score:    {c_score:+d}")
    print(f"Jobs Score:   {j_score:+d}")
    print(f"Oil Score:    {o_score:+d}")
    print(f"TLT Score:    {t_score:+d}")
    print(f"Total Score:  {total_score:+d} / 9")
    print(f"Signal:       {signal}")
    print("=" * 45)

    send_alert(
        total_score, signal,
        latest_30, latest_10,
        latest_cpi, prev_cpi,
        latest_jobs,
        latest_brent, latest_wti,
        latest_tlt,
        force_send=False
    )

if __name__ == "__main__":
    main()
