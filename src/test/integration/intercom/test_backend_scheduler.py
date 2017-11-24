import unittest
from intercom.back_end_binding import InterComBackEndBinding
from multiprocessing import Value, Queue
from tempfile import TemporaryDirectory
from time import sleep
from storage.MongoMgr import MongoMgr
from helperFunctions.config import get_config_for_testing


TMP_DIR = TemporaryDirectory(prefix='faf_test_')


# This number must be changed, whenever a listener is added or removed
NUMBER_OF_LISTENERS = 7


class ServiceMock():

    def __init__(self, test_queue):
        self.test_queue = test_queue

    def add_task(self, fo):
        self.test_queue.put(fo)

    def get_binary_and_name(self, uid):
        pass


class CommunicationBackendMock():

    counter = Value('i', 0)

    def __init__(self, config=None):
        pass

    def get_next_task(self):
        self.counter.value += 1
        if self.counter.value < 2:
            return 'test_task'
        else:
            return None

    def shutdown(self):
        pass


class AnalysisServiceMock():

    def __init__(self, config=None):
        pass

    def get_plugin_dict(self):
        return {}


class TestInterComBackEndScheduler(unittest.TestCase):

    def setUp(self):
        config = get_config_for_testing(TMP_DIR)
        self.test_queue = Queue()
        self.interface = InterComBackEndBinding(config=config, testing=True, analysis_service=AnalysisServiceMock(), compare_service=ServiceMock(self.test_queue), unpacking_service=ServiceMock(self.test_queue))
        self.interface.WAIT_TIME = 2
        self.db = MongoMgr(config=config)

    def tearDown(self):
        self.interface.shutdown()
        self.db.shutdown()
        self.test_queue.close()

    def test_backend_worker(self):
        service = ServiceMock(self.test_queue)
        self.interface._start_listener(CommunicationBackendMock, service.add_task)
        result = self.test_queue.get(timeout=5)
        self.assertEqual(result, 'test_task', 'task not received correctly')

    def test_all_listeners_startet(self):
        self.interface.startup()
        sleep(2)
        self.assertEqual(len(self.interface.process_list), NUMBER_OF_LISTENERS, 'Not all listeners started')
