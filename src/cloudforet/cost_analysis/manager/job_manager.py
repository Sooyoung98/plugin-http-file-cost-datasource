import logging
from datetime import datetime, timedelta

from spaceone.core.manager import BaseManager
from cloudforet.cost_analysis.model.job_model import Tasks
from cloudforet.cost_analysis.connector.http_file_connector import HTTPFileConnector

_LOGGER = logging.getLogger(__name__)


class JobManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.http_file_connector: HTTPFileConnector = self.locator.get_connector(HTTPFileConnector)

    def get_tasks(self, options, secret_data, schema, start, last_synchronized_at):
        self.http_file_connector.create_session(options, secret_data, schema)

        tasks = []
        changed = []

        start_time = self._get_start_time(start, last_synchronized_at)

        task_options = {
            'base_url': self.http_file_connector.base_url
        }

        tasks.append({'task_options': task_options})
        changed.append({
            'start': start_time
        })

        _LOGGER.debug(f'[get_tasks] tasks: {tasks}')
        _LOGGER.debug(f'[get_tasks] changed: {changed}')

        tasks = Tasks({'tasks': tasks, 'changed': changed})

        tasks.validate()
        return tasks.to_primitive()

    @staticmethod
    def _get_start_time(start, last_synchronized_at=None):

        if start:
            start_time: datetime = start
        elif last_synchronized_at:
            start_time: datetime = last_synchronized_at - timedelta(days=7)
            start_time = start_time.replace(day=1)
        else:
            start_time: datetime = datetime.utcnow() - timedelta(days=365)
            start_time = start_time.replace(day=1)

        start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)

        return start_time
