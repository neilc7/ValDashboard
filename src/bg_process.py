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
        elapsed = 0

        # setup dictionary for easier iteration
        # key: type of portfolio with collection of stocks.. basically the tables being displayed
        acc = {
            ('Top', 'Growth'): {
                'tbl_data': [self.pf.top_odata, self.pf.top_gdata],
                'conv_fn': self.pf.conv_top_tbl
            },
            ('Others', 'Growth'): {
                'tbl_data': [self.pf.grw_odata, self.pf.grw_gdata],
                'conv_fn': self.pf.conv_grw_tbl
            },
            ('Others', 'BigCap'): {
                'tbl_data': [self.pf.big_odata, self.pf.big_gdata],
                'conv_fn': self.pf.conv_big_tbl
            }
        }

        while True:

            for key, vals in acc.items():

                for stk in self.pf.idata['Portfolio']['Stocks'][key[0]][key[1]]:

                    # Loop until seconds elapsed have passed the stk interval
                    while elapsed < self.stk_interval:
                        elapsed += 1
                        time.sleep(self.proc_interval)

                    elapsed = 0

                    # Wait until manual update is done
                    while self.sts.update_inprog:
                        time.sleep(0.1)

                    self.sts.update_inprog = 1

                    self.logger.info("\n========== START BG FETCH [%s] ==========" % stk)
                    stk_data, gph_data = vals['tbl_data'][0][stk], vals['tbl_data'][1][stk]
                    val_ls, gph_ls = self.pf.val_ls, self.pf.graph_ls
                    # update in-place the stk_data and gph_data, which point to the pf's top/grw/big odata/gdata
                    self.pf.get_stk_val(stk, stk_data, False, val_ls, False)
                    self.pf.get_stk_val(stk, gph_data, False, gph_ls, True)
                    self.pf.save_to_db()
                    vals['conv_fn']()

                    self.sts.update_inprog = 0

                    self.logger.info("\n========== FINISH BG FETCH [%s] ==========\n" % stk)