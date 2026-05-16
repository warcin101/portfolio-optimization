TICKERS = [
    # US Equity
    "SPY",   # S&P 500
    "QQQ",   # Nasdaq 100 (US Tech)
    # Geographic — broad equity
    "VGK",   # Europe
    "EWJ",   # Japan
    "VWO",   # Emerging Markets broad (covers EM including India, China, Brazil)
    # Sectors
    "XLV",   # Healthcare
    # Real Estate
    "REET",  # Global REITs (proxy for Amundi FTSE EPRA NAREIT Global)
    # Commodities
    "GLD",   # Gold (proxy for iShares Physical Gold ETC — physically backed, no roll cost)
]

METADATA = {
    "SPY":  {"name": "SPDR S&P 500 ETF",                        "region": "US",       "type": "Broad Equity"},
    "QQQ":  {"name": "Invesco QQQ Trust (Nasdaq 100)",           "region": "US",       "type": "Broad Equity"},
    "VGK":  {"name": "Vanguard FTSE Europe ETF",                 "region": "Europe",   "type": "Broad Equity"},
    "EWJ":  {"name": "iShares MSCI Japan ETF",                   "region": "Japan",    "type": "Broad Equity"},
    "VWO":  {"name": "Vanguard FTSE Emerging Markets ETF",       "region": "EM Broad", "type": "Broad Equity"},
    "XLV":  {"name": "Healthcare Select Sector SPDR ETF",        "region": "US",       "type": "Sector"},
    "REET": {"name": "iShares Global REIT ETF",                  "region": "Global",   "type": "Real Estate"},
    "GLD":  {"name": "SPDR Gold Shares",                         "region": "Global",   "type": "Commodity"},
}

UCITS_MAP = {
    "SPY":  "CSPX.UK",   # iShares Core S&P 500 UCITS — confirmed on XTB
    "QQQ":  "EQQQ.UK",   # Invesco EQQQ Nasdaq-100 UCITS — confirmed on XTB
    "VGK":  "CEBZ.DE",   # iShares Core MSCI Europe UCITS — confirmed on XTB
    "EWJ":  "CJPU.UK",   # iShares MSCI Japan UCITS — confirmed on XTB
    "VWO":  "EIMI.UK",   # iShares Core MSCI EM IMI UCITS — confirmed on XTB
    "XLV":  "CBUF.DE",   # iShares MSCI World Healthcare ESG UCITS — confirmed on XTB
    "REET": "10AJ.DE",   # Amundi FTSE EPRA NAREIT Global — confirmed on XTB
    "GLD":  "EGLN.UK",   # iShares Physical Gold ETC (physically backed) — confirmed on XTB
}