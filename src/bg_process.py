import time
import threading
import logging

# imports for class typing
from .portfolio import Portfolio
from .status import Status

class BackgroundProcess:

    def __init__(self, proc_interval = 1, stk_interval = 30):
        """
        :param proc_interval: interval to query current state of the app
        :param stk_interval: interval to get stocks data
        """
        self.proc_interval = proc_interval
        self.stk_interval = stk_interval
        self.logger = logging.getLogger('root.' + __name__)

    def config(self, pf: Portfolio, sts: Status):
        """
        :param sts: handle to Status object
        :param pf: handle to Portfolio object
        :return: None
        """
        self.pf = pf
        self.sts = sts

    def start(self):
        """
        Start the background process
        """
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()

    def run(self):
        """
        Main process of the thread
        :return:
        """
        while True:
            time.sleep(self.proc_interval)
            if self.sts.update_inprog:
                continue

            if self.sts.auto_update:
                self.get_next_stk_data()

    def get_next_stk_data(self):
        pass