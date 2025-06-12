import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pytrends.request import TrendReq
import yfinance as yf

@st.cache_data
def get_google_trends_data(keywords, timeframe):
    pytrends = TrendReq(hl='en-US', tz=540)
    pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo='JP', gprop='')
    return pytrends.interest_over_time()
    
# Axis
st.sidebar.title("Settings")
keywords = st.sidebar.multiselect(
    "Select Keywords (English/Japanese)", 
    ["crude oil", "電気料金", "天然ガス", "LNG", "原油"], 
    default=["crude oil", "電気料金"]
)

timeframe = st.sidebar.selectbox(
    "Select Google Trends Timeframe", 
    ["today 3-m", "today 12-m", "today 5-y"], 
    index=0
)
st.sidebar.write("Tip: Use Japanese keywords for Japanese trends!")

# fetching google trends data

st.header("Google Trends Data")
pytrends = TrendReq(hl='en-US', tz=540)

if len(keywords) == 0:
    st.warning("Please select at least one keyword.")
    st.stop()
    
pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo='JP', gprop='')
interest_over_time_df = pytrends.interest_over_time()
if interest_over_time_df.empty:
    st.error("No trend data found for the selected keywords/timeframe.")
    st.stop()
st.write("Sample Google Trends Data:")
st.dataframe(interest_over_time_df.head())

# fetch commodity price for crude oil
st.header("Crude Oil Price Data")

# Mapping for yfinance periods
timeframe_mapping = {
    "today 3-m": "3mo",
    "today 12-m": "12mo",
    "today 5-y": "5y"
}
 # default time frame to 3mo if not found
selected_period = timeframe_mapping.get(timeframe, "3mo") 
oil_data = yf.download('CL=F', period=selected_period, interval='1d')
if oil_data.empty:
    st.error("Could not fetch oil price data.")
    st.stop()
st.write("Sample Oil Price Data:")
st.dataframe(oil_data[['Close']].head())

# merging and cleaning data
st.header("Merge & Clean Data")
# converting google trends to fit business days to match market data
trends = interest_over_time_df.resample('B').mean().fillna(method='ffill')
merged_df = pd.merge(trends, oil_data['Close'], left_index=True, right_index=True)
merged_df.rename(columns={'Close': 'Oil Price'}, inplace=True)
st.write("Merged Data Sample:")
st.dataframe(merged_df.head())

# correlation analysis
st.header("Correlation Analysis")
correlation = merged_df.corr()
st.write("Correlation Matrix:")
st.dataframe(correlation)

# Lagged correlation
st.write("Lagged Correlations (Keyword vs Oil Price):")
lag_results = {}
for kw in keywords:
    lags = []
    for lag in range(1, 8):
        shifted = merged_df.copy()
        shifted[kw] = shifted[kw].shift(lag)
        lag_corr = shifted.corr()[kw]['Oil Price']
        lags.append(lag_corr)
    lag_results[kw] = lags
lag_df = pd.DataFrame(lag_results, index=[f"Lag {i}" for i in range(1, 8)])
st.dataframe(lag_df)

# visualizations
st.header("Visualization")

st.subheader("Google Trends & Oil Price Over Time")
for kw in keywords:
    fig, ax1 = plt.subplots(figsize=(12, 5))
    color = 'tab:blue'
    ax1.set_xlabel('Date')
    ax1.set_ylabel(f'Google Trend - {kw}', color=color)
    ax1.plot(merged_df.index, merged_df[kw], color=color)
    ax1.tick_params(axis='y', labelcolor=color)
    
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Oil Price (USD)', color=color)
    ax2.plot(merged_df.index, merged_df['Oil Price'], color=color)
    ax2.tick_params(axis='y', labelcolor=color)
    
    plt.title(f'Google Trend ("{kw}") vs. Oil Price')
    plt.tight_layout()
    st.pyplot(fig)

# option to download
st.header("Download Merged Data")
st.download_button(
    label="Download merged data as CSV",
    data=merged_df.to_csv().encode('utf-8'),
    file_name='merged_trends_oil.csv',
    mime='text/csv'
)

st.success("✅ Done! Adjust keywords and timeframe on the sidebar to explore different correlations.")

st.markdown("---")
st.markdown("Built with ❤️ using [pytrends](https://github.com/GeneralMills/pytrends), [yfinance](https://github.com/ranaroussi/yfinance), [Matplotlib](https://matplotlib.org/), and [Streamlit](https://streamlit.io/).")
