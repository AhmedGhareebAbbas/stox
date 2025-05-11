from flask import Flask, render_template, request
from recommendation_logic import generate_recommendation_yf as generate_recommendation

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    search_result = None
    symbol = ""

    if request.method == 'POST':
        symbol = request.form.get('stock_symbol')
        if symbol:
            search_result = generate_recommendation(symbol)

    return render_template('index.html',
                           search_result=search_result,
                           total_symbols=10,
                           sma_short_period=20,
                           sma_long_period=50,
                           rsi_period=14,
                           macd_fast=12,
                           macd_slow=26,
                           macd_signal=9,
                           bbands_period=20,
                           bbands_std_dev=2,
                           timestamp="Now")

if __name__ == '__main__':
    app.run(debug=True)
