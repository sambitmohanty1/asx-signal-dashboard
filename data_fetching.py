import requests
from bs4 import BeautifulSoup
import streamlit as st

@st.cache_data(ttl=86400)
def fetch_sector_pe_map():
    url = "https://fullratio.com/pe-ratio/by-sector"
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find("table")
        sector_pe = {}
        if table:
            for row in table.find_all("tr")[1:]:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    sector = cols[0].text.strip()
                    pe = cols[1].text.strip().replace(",", "")
                    try:
                        sector_pe[sector] = float(pe)
                    except:
                        continue
        return sector_pe
    except:
        return {}

def fetch_broker_rating_asx(ticker):
    url = "https://www.marketindex.com.au/broker-consensus"
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find("table")
        if table:
            for row in table.find_all("tr")[1:]:
                cols = row.find_all("td")
                if len(cols) >= 2 and ticker.upper() in cols[0].text:
                    rating = cols[1].text.strip().lower()
                    if "buy" in rating:
                        return 5
                    elif "accumulate" in rating:
                        return 4
                    elif "hold" in rating:
                        return 3
                    elif "reduce" in rating:
                        return 2
                    elif "sell" in rating:
                        return 1
        return 3
    except:
        return 3