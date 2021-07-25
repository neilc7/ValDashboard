from .webparse import WebParse
import pandas as pd
import json

import logging

class Portfolio:
    
    idata = {}
    val_ls = []
    graph_ls = []
    
    # master database
    mdb = {}
    gph = {}
    mdb_update_needed = 0
    gph_update_needed = 0
    
    top_odata, grw_odata, big_odata = {}, {}, {}
    top_gdata, grw_gdata, big_gdata = {}, {}, {}
    top_pd_tbl, grw_pd_tbl, big_pd_tbl = '', '', ''
    
    def __init__(self):
        self.wp = WebParse()
        self.logger = logging.getLogger('root.' + __name__)

    def assign_wp_pdata(self, dict_, stk = None):
        """
        pdata is a web parser's handler to the portfolio data to access info that is already parsed.
        We can assign pdata to any dictionary to aid the parsing.
        :param dict_: dictionary of stk and valuation, or just valuations
        :param stk: if specified, assign the valuation.. otherwise assign the stock and valuation
        """
        if self.wp.pdata != {}:
            raise Exception('Trying to assign a dictionary to a non-empty pdata', stk, dict_)

        if stk is not None:
            self.wp.pdata[stk] = dict_
        else:
            self.wp.pdata = dict_

    def release_wp_pdata(self):
        """
        Since pdata is temporary handler, it should be freed up after any operation
        """
        self.wp.pdata = {}

    def process_parse(self, odata, gdata, upd_val, p0, p1):
        # if update valuation, empty out and update everything
        if upd_val == 1:
            self.wp.clear_webcache()
            odata, gdata = self.process_parse(odata, gdata, 0, p0, p1)
            
            for stk in self.idata['Portfolio']['Stocks'][p0][p1]:
                odata[stk] = self.get_stk_val(stk, odata[stk], False, self.val_ls, False)
                gdata[stk] = self.get_stk_val(stk, gdata[stk], False, self.graph_ls, True)
        
        # no update, just get from master db
        else:
            odata = {}
            gdata = {}
            
            for stk in self.idata['Portfolio']['Stocks'][p0][p1]:
                odata[stk] = self.get_stk_val(stk, {}, True, self.val_ls, False)
                gdata[stk] = self.get_stk_val(stk, {}, True, self.graph_ls, True)

        return odata, gdata

    def get_stk_val(self, stk, stk_data, from_db: bool, val_ls: list, is_graph: bool):
        """
        :param stk: The stock ticker
        :param stk_data: Stock data dictionary. This can be empty of pre-filled
        :param from_db: Get the data from database or webparse
        :param val_ls: Valuation list
        :param is_graph: Indicates graph mode, which will call different mode of parsing
        :return:
        """
        self.assign_wp_pdata(stk_data, stk)

        # if not from_db, get latest date that we have to later compare against the website data
        # if date is similar, we can skip the parsing of some metrics
        if not from_db:
            try:
                stk_data['latest'] = self.gph[stk]['Rev Qtr date'][-1]
            except KeyError:
                stk_data['latest'] = ''

        # get the valuation and financial metrics
        for val in val_ls:
            try:
                if from_db:
                    if is_graph:
                        stk_data[val] = self.gph[stk][val]
                        stk_data[val+' date'] = self.gph[stk][val+' date']
                    else:
                        stk_data[val] = self.mdb[stk][val]
                else:
                    raise KeyError('Raise KeyError to execute parse')
            # exception for data that doesn't exist in mdb, or for manual parse (i.e. not from db)
            except KeyError:
                if is_graph:
                    self.logger.info('get graph data for %s %s' % (stk, val))
                    stk_data[val+' date'], stk_data[val] = self.wp.parse(stk, val, fn_type='graph')
                    self.gph_update_needed = 1
                else:
                    self.logger.info('get table data for %s %s' % (stk, val))
                    stk_data[val] = self.wp.parse(stk, val)
                    self.mdb_update_needed = 1

        # delete the 'latest' date since it's only for temporary comparison
        if not from_db:
            del stk_data['latest']

        self.release_wp_pdata()
        return stk_data

    def update_mkt_cap_dep(self, stk):
        mkt_cap = self.wp.parse(stk, 'Mkt Cap')
        ps_ttm  = float("{0:.3f}".format(mkt_cap/self.mdb[stk]['Rev TTM']))
        return mkt_cap, ps_ttm

    def update_db(self, odict, idict):
        """
        Update existing database with new entry.
        Update the value if entry already exists. Otherwise, create new entry

        :param odict: existing database
        :param idict: new database
        :return: Updated database
        """
        for stk, vals in idict.items():
            if stk not in odict.keys():
                odict[stk] = {}
            for v_key, v_val in vals.items():
                odict[stk][v_key] = v_val
        return odict
    
    def save_to_db(self):
        """
        Append master and graph db with new or updated entries
        """
        if self.mdb_update_needed:
            for db in [self.top_odata, self.grw_odata, self.big_odata]:
                self.mdb = self.update_db(self.mdb, db)
        
                mfile = open('data/master_db.json', 'w')
                json.dump(self.mdb, mfile, indent=4)
                mfile.close()
        
            self.mdb_update_needed = 0
            self.logger.info("INFO: Master DB Updated")
                
        if self.gph_update_needed:
            for db in [self.top_gdata, self.grw_gdata, self.big_gdata]:
                self.gph = self.update_db(self.gph, db)
                
                mfile = open('data/graph_db.json', 'w')
                json.dump(self.gph, mfile, indent=4)
                mfile.close()
        
            self.gph_update_needed = 0
            self.logger.info("INFO: Graph DB Updated")
    
    def open_db(self):
        """
        Open the master and graph generated json if already exist.
        Otherwise, assign empty dict to self's handle of master and graph db
        :return:
        """
        try:
            mfile = open('data/master_db.json', 'r')
            self.mdb = json.load(mfile)
            mfile.close()
        except OSError:
            self.mdb = {}
    
        try:
            mfile = open('data/graph_db.json', 'r')
            self.gph = json.load(mfile)
            mfile.close()
        except OSError:
            self.gph = {}
    
    
    def dict_to_pd(self, idict):
        # convert to flat list like this:
        # [{'stk':'ROKU', 'mkt_cap':XXX, 'inc qtr': YYY},
        #  {'stk':'FSLY', ....}]
        pd_tbl = []
        for stk, vals in idict.items():
            newdict = {'Stk':stk}
            newdict.update(vals)
            pd_tbl += [newdict]
        
        opd = pd.json_normalize(pd_tbl)
        return opd

    def process(self, upd_val):
        """
        Entry of the udpate process. Decide whether to update market cap, or entire valuation.
        1. Get the valuation and graph list from the json
        :param upd_val:
        """
        self.val_ls = self.idata['Portfolio']['Valuation']
        self.graph_ls = self.idata['Portfolio']['Graph']
        
        self.open_db()
        
        self.top_odata, self.top_gdata = self.process_parse(self.top_odata, self.top_gdata, upd_val, 'Top', 'Growth')
        self.grw_odata, self.grw_gdata = self.process_parse(self.grw_odata, self.grw_gdata, upd_val, 'Others', 'Growth')
        self.big_odata, self.big_gdata = self.process_parse(self.big_odata, self.big_gdata, upd_val, 'Others', 'BigCap')
        
        self.save_to_db()
        
        self.top_pd_tbl = self.dict_to_pd(self.top_odata)
        self.grw_pd_tbl = self.dict_to_pd(self.grw_odata)
        self.big_pd_tbl = self.dict_to_pd(self.big_odata)

    def conv_top_tbl(self):
        self.top_pd_tbl = self.dict_to_pd(self.top_odata)

    def conv_grw_tbl(self):
        self.grw_pd_tbl = self.dict_to_pd(self.grw_odata)

    def conv_big_tbl(self):
        self.big_pd_tbl = self.dict_to_pd(self.big_odata)