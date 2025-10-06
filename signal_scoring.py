def calculate_signal_score(current_price, sma_200, pe_ratio, sector_pe, analyst_upside, broker_score):
    try:
        sma_score = max(0, 100 - abs(current_price - sma_200) / sma_200 * 100)
        pe_z = (pe_ratio - sector_pe) / sector_pe
        pe_score = max(0, 100 - abs(pe_z) * 100)
        upside_score = min(100, analyst_upside)
        broker_score = broker_score * 20
        return round((sma_score * 0.25 + pe_score * 0.25 + upside_score * 0.25 + broker_score * 0.25), 2)
    except:
        return 50.0