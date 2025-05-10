from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime

class BitcoinPriceApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_routes()

    def get_usd_to_krw(self):
        try:
            response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
            return response.json()['rates']['KRW']
        except Exception as e:
            print(f"❌ 환율 조회 실패: {e}")
            return None

    def get_current_price_krw(self):
        url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd'
        btc_usd = requests.get(url).json()['bitcoin']['usd']
        rate = self.get_usd_to_krw()
        return round(btc_usd * rate)

    def get_historical_data_krw(self, days):
        url = f'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days={days}'
        res = requests.get(url).json()
        prices = res['prices']
        rate = self.get_usd_to_krw()

        labels = [datetime.fromtimestamp(p[0] / 1000).strftime('%m-%d') for p in prices]
        data = [int(p[1] * rate) for p in prices]
        return labels, data

    def setup_routes(self):
        @self.app.route('/')
        def index():
            current_price = self.get_current_price_krw()
            return render_template('index.html', price=current_price)

        @self.app.route('/get_data')
        def get_data():
            days = request.args.get('days', default='7')
            labels, data = self.get_historical_data_krw(days)
            return jsonify({'labels': labels, 'data': data})

    def run(self):
        self.app.run(debug=True)

if __name__ == '__main__':
    app_instance = BitcoinPriceApp()
    app_instance.run()
