import json
import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def list_args_to_comma_separated(func):
    """Return function that converts list input arguments to comma-separated strings"""
    def input_args(*args, **kwargs):
        for v in kwargs:
            # check in **kwargs for lists and convert to comma-separated string
            if isinstance(kwargs[v], list):
                kwargs[v] = ','.join(kwargs[v])
        # check in *args for lists and convert to comma-separated string
        args = [','.join(v) if isinstance(v, list) else v for v in args]
        return func(*args, **kwargs)
    return input_args


def get_comma_separated_values(values):
    """Return the values as a comma-separated string"""

    # Make sure values is a list or tuple
    if not isinstance(values, list) and not isinstance(values, tuple):
        values = [values]
    return ','.join(values)


class CoinGeckoAPI:
    __API_URL_BASE = 'https://api.coingecko.com/api/v3/'

    def __init__(self, api_base_url=__API_URL_BASE):
        self.api_base_url = api_base_url
        self.request_timeout = 120

        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=0.5,
                        status_forcelist=[502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))

    def __request(self, url):
        # print(url)
        try:
            #print ("get ",url)
            response = self.session.get(url, timeout=self.request_timeout)
            response.raise_for_status()
            content = json.loads(response.content.decode('utf-8'))
            return content
        except Exception as e:
            # check if json (with error message) is returned
            try:
                content = json.loads(response.content.decode('utf-8'))
                raise ValueError(content)
            # if no json
            except json.decoder.JSONDecodeError:
                pass
            # except UnboundLocalError as e:
            #    pass
            raise

    def __api_url_params(self, api_url, params):
        if params:
            api_url += '?'
            for key, value in params.items():
                api_url += "{0}={1}&".format(key, value)
            api_url = api_url[:-1]
        return api_url

    # ---------- PING ----------#
    def ping(self):
        """Check API server status"""

        api_url = '{0}ping'.format(self.api_base_url)
        return self.__request(api_url)

    # ---------- SIMPLE ----------#
    @list_args_to_comma_separated
    def get_price(self, ids, vs_currencies, **kwargs):
        """Get the current price of any cryptocurrencies in any other supported currencies that you need"""

        ids = ids.replace(' ', '')
        kwargs['ids'] = ids
        vs_currencies = vs_currencies.replace(' ', '')
        kwargs['vs_currencies'] = vs_currencies

        api_url = '{0}simple/price'.format(self.api_base_url)
        api_url = self.__api_url_params(api_url, kwargs)

        return self.__request(api_url)

    @list_args_to_comma_separated
    def get_token_price(self, id, contract_addresses, vs_currencies, **kwargs):
        """Get the current price of any tokens on this coin (ETH only at this stage as per api docs) in any other supported currencies that you need"""

        contract_addresses = contract_addresses.replace(' ', '')
        kwargs['contract_addresses'] = contract_addresses
        vs_currencies = vs_currencies.replace(' ', '')
        kwargs['vs_currencies'] = vs_currencies

        api_url = '{0}simple/token_price/{1}'.format(self.api_base_url, id)
        api_url = self.__api_url_params(api_url, kwargs)
        return self.__request(api_url)

    def get_supported_vs_currencies(self):
        """Get list of supported_vs_currencies"""

        api_url = '{0}simple/supported_vs_currencies'.format(self.api_base_url)
        return self.__request(api_url)

    # ---------- COINS ----------#
    @list_args_to_comma_separated
    def get_coins(self, **kwargs):
        """List all coins with data (name, price, market, developer, community, etc)"""

        api_url = '{0}coins'.format(self.api_base_url)
        # ['order', 'per_page', 'page', 'localization']
        api_url = self.__api_url_params(api_url, kwargs)

        return self.__request(api_url)

    def get_coins_list(self):
        """List all supported coins id, name and symbol (no pagination required)"""

        api_url = '{0}coins/list'.format(self.api_base_url)

        return self.__request(api_url)

    @list_args_to_comma_separated
    def get_coins_markets(self, vs_currency, *ids, **kwargs):
        """List all supported coins price, market cap, volume, and market related data (no pagination required)"""
        #print(kwargs)

        kwargs['vs_currency'] = vs_currency
        if ids:
            kwargs['ids'] = ids

        api_url = '{0}coins/markets'.format(self.api_base_url)
        api_url = self.__api_url_params(api_url, kwargs)

        return self.__request(api_url)

    @list_args_to_comma_separated
    def get_coin_by_id(self, id, **kwargs):
        """Get current data (name, price, market, ... including exchange tickers) for a coin"""

        api_url = '{0}coins/{1}/'.format(self.api_base_url, id)
        api_url = self.__api_url_params(api_url, kwargs)

        return self.__request(api_url)

    @list_args_to_comma_separated
    def get_coin_ticker_by_id(self, id, **kwargs):
        """Get coin tickers (paginated to 100 items)"""

        api_url = '{0}coins/{1}/tickers'.format(self.api_base_url, id)
        api_url = self.__api_url_params(api_url, kwargs)

        return self.__request(api_url)

    @list_args_to_comma_separated
    def get_coin_history_by_id(self, id, date, **kwargs):
        """Get historical data (name, price, market, stats) at a given date for a coin"""

        kwargs['date'] = date

        api_url = '{0}coins/{1}/history'.format(self.api_base_url, id)
        api_url = self.__api_url_params(api_url, kwargs)

        return self.__request(api_url)

    @list_args_to_comma_separated
    def get_coin_market_chart_by_id(self, id, vs_currency, days):
        """Get historical market data include price, market cap, and 24h volume (granularity auto)"""

        api_url = '{0}coins/{1}/market_chart?vs_currency={2}&days={3}'.format(
            self.api_base_url, id, vs_currency, days)

        return self.__request(api_url)

    @list_args_to_comma_separated
    def get_coin_market_chart_range_by_id(self, id, vs_currency, from_timestamp, to_timestamp):
        """Get historical market data include price, market cap, and 24h volume within a range of timestamp (granularity auto)"""

        api_url = '{0}coins/{1}/market_chart/range?vs_currency={2}&from={3}&to={4}'.format(self.api_base_url, id,
                                                                                           vs_currency, from_timestamp,
                                                                                           to_timestamp)

        return self.__request(api_url)

    @list_args_to_comma_separated
    def get_coin_status_updates_by_id(self, id, **kwargs):
        """Get status updates for a given coin"""

        api_url = '{0}coins/{1}/status_updates'.format(self.api_base_url, id)
        api_url = self.__api_url_params(api_url, kwargs)

        return self.__request(api_url)

    # ---------- Contract ----------#
    @list_args_to_comma_separated
    def get_coin_info_from_contract_address_by_id(self, id, contract_address):
        """Get coin info from contract address"""

        api_url = '{0}coins/{1}/contract/{2}'.format(
            self.api_base_url, id, contract_address)

        return self.__request(api_url)

    @list_args_to_comma_separated
    def get_coin_market_chart_from_contract_address_by_id(self, id, contract_address, vs_currency, days):
        """Get historical market data include price, market cap, and 24h volume (granularity auto) from a contract address"""

        api_url = '{0}coins/{1}/contract/{2}/market_chart/?vs_currency={3}&days={4}'.format(self.api_base_url, id,
                                                                                            contract_address,
                                                                                            vs_currency, days)

        return self.__request(api_url)

    @list_args_to_comma_separated
    def get_coin_market_chart_range_from_contract_address_by_id(self, id, contract_address, vs_currency, from_timestamp,
                                                                to_timestamp):
        """Get historical market data include price, market cap, and 24h volume within a range of timestamp (granularity auto) from a contract address"""

        api_url = '{0}coins/{1}/contract/{2}/market_chart/range?vs_currency={3}&from={4}&to={5}'.format(
            self.api_base_url, id, contract_address, vs_currency, from_timestamp, to_timestamp)

        return self.__request(api_url)

    # ---------- EXCHANGES ----------#
    def get_exchanges_list(self):
        """List all exchanges"""

        api_url = '{0}exchanges'.format(self.api_base_url)
        kwargs = {}
        kwargs['per_page'] = 250
        api_url = self.__api_url_params(api_url, kwargs)

        return self.__request(api_url)

    def get_exchanges_id_name_list(self):
        """List all supported markets id and name (no pagination required)"""

        api_url = '{0}exchanges/list'.format(self.api_base_url)
        #kwargs['per_page'] = 250
        return self.__request(api_url)

    @list_args_to_comma_separated
    def get_exchanges_by_id(self, id):
        """Get exchange volume in BTC and tickers"""

        api_url = '{0}exchanges/{1}'.format(self.api_base_url, id)

        return self.__request(api_url)

    @list_args_to_comma_separated
    def get_exchanges_tickers_by_id(self, id, page=1, **kwargs):
        """Get exchange tickers (paginated)"""

        api_url = '{0}exchanges/{1}/tickers'.format(self.api_base_url, id)
        kwargs['page'] = page        
        api_url = self.__api_url_params(api_url, kwargs)

        return self.__request(api_url)

    @list_args_to_comma_separated
    def get_exchanges_status_updates_by_id(self, id, **kwargs):
        """Get status updates for a given exchange"""

        api_url = '{0}exchanges/{1}/status_updates'.format(
            self.api_base_url, id)
        api_url = self.__api_url_params(api_url, kwargs)

        return self.__request(api_url)

    @list_args_to_comma_separated
    def get_exchanges_volume_chart_by_id(self, id, days, **kwargs):
        """Get volume chart data for a given exchange"""

        kwargs['days'] = days

        api_url = '{0}exchanges/{1}/volume_chart'.format(self.api_base_url, id)
        api_url = self.__api_url_params(api_url, kwargs)

        return self.__request(api_url)

    # ---------- FINANCE ----------#
    def get_finance_platforms(self):
        """Get cryptocurrency finance platforms data"""

        api_url = '{0}finance_platforms'.format(self.api_base_url)

        return self.__request(api_url)

    def get_finance_products(self):
        """Get cryptocurrency finance products data"""

        api_url = '{0}finance_products'.format(self.api_base_url)

        return self.__request(api_url)

    # ---------- INDEXES ----------#
    def get_indexes(self, **kwargs):
        """List all market indexes"""

        api_url = '{0}indexes'.format(self.api_base_url)
        api_url = self.__api_url_params(api_url, kwargs)

        return self.__request(api_url)

    def get_indexes_by_id(self, id):
        """Get market index by id"""

        api_url = '{0}indexes/{1}'.format(self.api_base_url, id)

        return self.__request(api_url)

    def get_indexes_list(self):
        """List market indexes id and name"""

        api_url = '{0}indexes/list'.format(self.api_base_url)

        return self.__request(api_url)

    # ---------- DERIVATIVES ----------#
    def get_derivatives(self):
        """List all derivative tickers"""

        api_url = '{0}derivatives'.format(self.api_base_url)

        return self.__request(api_url)

    def get_derivatives_exchanges(self, **kwargs):
        """List all derivative tickers"""

        api_url = '{0}derivatives/exchanges'.format(self.api_base_url)
        api_url = self.__api_url_params(api_url, kwargs)

        return self.__request(api_url)

    def get_derivatives_exchanges_by_id(self, id):
        """List all derivative tickers"""

        api_url = '{0}derivatives/exchanges/{1}'.format(self.api_base_url, id)

        return self.__request(api_url)

    def get_derivatives_exchanges_list(self):
        """List all derivative tickers"""

        api_url = '{0}derivatives/exchanges/list'.format(self.api_base_url)

        return self.__request(api_url)

    # ---------- STATUS UPDATES ----------#
    @list_args_to_comma_separated
    def get_status_updates(self, **kwargs):
        """List all status_updates with data (description, category, created_at, user, user_title and pin)"""

        api_url = '{0}status_updates'.format(self.api_base_url)
        api_url = self.__api_url_params(api_url, kwargs)

        return self.__request(api_url)

    # ---------- EVENTS ----------#
    @list_args_to_comma_separated
    def get_events(self, **kwargs):
        """Get events, paginated by 100"""

        api_url = '{0}events'.format(self.api_base_url)
        api_url = self.__api_url_params(api_url, kwargs)

        return self.__request(api_url)

    def get_events_countries(self):
        """Get list of event countries"""

        api_url = '{0}events/countries'.format(self.api_base_url)

        return self.__request(api_url)

    def get_events_types(self):
        """Get list of event types"""

        api_url = '{0}events/types'.format(self.api_base_url)

        return self.__request(api_url)

    # ---------- EXCHANGE-RATES ----------#
    def get_exchange_rates(self):
        """Get BTC-to-Currency exchange rates"""

        api_url = '{0}exchange_rates'.format(self.api_base_url)

        return self.__request(api_url)

    # ---------- GLOBAL ----------#
    def get_global(self):
        """Get cryptocurrency global data"""

        api_url = '{0}global'.format(self.api_base_url)

        return self.__request(api_url)['data']
