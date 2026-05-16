TICKERS = [
    # US Equity
    "SPY",   # S&P 500
    "QQQ",   # Nasdaq 100 (US Tech)
    # Geographic — broad equity
    "VGK",   # Europe
    "EWJ",   # Japan
    "VWO",   # Emerging Markets broad (covers EM including India, China, Brazil)
    # Sectors
    "ICLN",  # Global Clean Energy
    "XLV",   # Healthcare
]

METADATA = {
    "SPY":  {"name": "SPDR S&P 500 ETF",                        "region": "US",       "type": "Broad Equity"},
    "QQQ":  {"name": "Invesco QQQ Trust (Nasdaq 100)",           "region": "US",       "type": "Broad Equity"},
    "VGK":  {"name": "Vanguard FTSE Europe ETF",                 "region": "Europe",   "type": "Broad Equity"},
    "EWJ":  {"name": "iShares MSCI Japan ETF",                   "region": "Japan",    "type": "Broad Equity"},
    "VWO":  {"name": "Vanguard FTSE Emerging Markets ETF",       "region": "EM Broad", "type": "Broad Equity"},
    "ICLN": {"name": "iShares Global Clean Energy ETF",          "region": "Global",   "type": "Sector"},
    "XLV":  {"name": "Healthcare Select Sector SPDR ETF",        "region": "US",       "type": "Sector"},
}

UCITS_MAP = {
    "SPY":  "CSPX.UK",   # iShares Core S&P 500 UCITS — confirmed on XTB
    "QQQ":  "EQQQ.UK",   # Invesco EQQQ Nasdaq-100 UCITS — confirmed on XTB
    "VGK":  "CEBZ.DE",   # iShares Core MSCI Europe UCITS — confirmed on XTB
    "EWJ":  "CJPU.UK",   # iShares MSCI Japan UCITS — confirmed on XTB
    "VWO":  "EIMI.UK",   # iShares Core MSCI EM IMI UCITS — confirmed on XTB
    "ICLN": "IQQH.DE",   # iShares Global Clean Energy UCITS — confirmed on XTB
    "XLV":  "CBUF.DE",   # iShares MSCI World Healthcare ESG UCITS — confirmed on XTB
}