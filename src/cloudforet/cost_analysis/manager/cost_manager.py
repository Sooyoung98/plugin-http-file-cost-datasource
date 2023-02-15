import logging
from datetime import datetime
from dateutil.parser import parse
from spaceone.core.manager import BaseManager
from cloudforet.cost_analysis.error import *
from cloudforet.cost_analysis.connector.http_file_connector import HTTPFileConnector

_LOGGER = logging.getLogger(__name__)

_REQUIRED_FIELDS = [
    'cost',
    'currency',
    'year',
    'month',
    'day'
]


class CostManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.http_file_connector: HTTPFileConnector = self.locator.get_connector(HTTPFileConnector)

    def get_data(self, options, secret_data, schema, task_options):
        self.http_file_connector.create_session(options, secret_data, schema)
        self._check_task_options(task_options)

        base_url = task_options['base_url']

        response_stream = self.http_file_connector.get_cost_data(base_url)
        for results in response_stream:
            yield self._make_cost_data(results)

    def _make_cost_data(self, results):
        costs_data = []
        for result in results:

            if self.http_file_connector.field_mapper:
                result = self._change_result_by_field_mapper(result)

            if self.http_file_connector.default_vars:
                self._set_default_vars(result)

            self._check_required_fields(result)

            try:
                data = {
                    'cost': result['cost'],
                    'currency': result['currency'],
                    'usage_quantity': result.get('usage_quantity', 0),
                    'provider': result.get('provider'),
                    'region_code': result.get('region_code'),
                    'product': result.get('product'),
                    'account': str(result.get('account')),
                    'usage_type': result.get('usage_type'),
                    'billed_at': self._create_billed_at_format(result['year'], result['month'], result['day']),
                    'additional_info': {},
                    'tags': result.get('tags', {})
                }

            except Exception as e:
                _LOGGER.error(f'[_make_cost_data] make data error: {e}', exc_info=True)
                raise e

            costs_data.append(data)
        return costs_data

    @staticmethod
    def _check_task_options(task_options):
        if 'base_url' not in task_options:
            raise ERROR_REQUIRED_PARAMETER(key='task_options.base_url')

    def _change_result_by_field_mapper(self, result):
        for origin_field, actual_field in self.http_file_connector.field_mapper.items():

            if actual_field in result:
                result[origin_field] = result[actual_field]
                del result[actual_field]

            if 'billed_at' in origin_field:
                result['billed_at'] = parse(result[origin_field])
                result['year'] = result[origin_field].year
                result['month'] = result[origin_field].month
                result['day'] = result[origin_field].day

            return result

    def _set_default_vars(self, result):
        for key, value in self.http_file_connector.default_vars.items():
            result[key] = value

    @staticmethod
    def _check_required_fields(result):
        for field in _REQUIRED_FIELDS:
            if field not in result:
                raise ERROR_REQUIRED_PARAMETER(key=field)

    @staticmethod
    def _create_billed_at_format(year, month, day):
        date = f'{year}-{month}-{day}'
        billed_at_format = '%Y-%m-%d'
        return datetime.strptime(date, billed_at_format)

    # TODO: add collection_info to cost data
    # TODO: add _LOGGER.debug