def run_backtest(df, signal_score, threshold):
    trades = []
    holding_period = 10
    for i in range(len(df) - holding_period):
        if signal_score > threshold:
            entry_price = df['Close'].iloc[i]
            exit_price = df['Close'].iloc[i + holding_period]
            return_pct = (exit_price - entry_price) / entry_price * 100
            trades.append(return_pct)

    total_trades = len(trades)
    wins = len([r for r in trades if r > 0])
    win_rate = round(wins / total_trades * 100, 2) if total_trades > 0 else 0
    avg_return = round(sum(trades) / total_trades, 2) if total_trades > 0 else 0
    cumulative_return = round(sum(trades), 2)

    return {
        "Total Trades": total_trades,
        "Win Rate (%)": win_rate,
        "Average Return per Trade (%)": avg_return,
        "Cumulative Return (%)": cumulative_return,
        "Holding Period (days)": holding_period
    }