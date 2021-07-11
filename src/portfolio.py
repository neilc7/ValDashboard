from . import webparse
import pandas as pd
import json

import logging

class portfolio:
    
    idata = {}
    val_ls = []
    graph_ls = []
    
    # master database
    mdb = {}
    gph = {}
    mdb_update_needed = 0
    gph_update_needed = 0
    
    cml_odata, grw_odata, big_odata = {}, {}, {}
    cml_gdata, grw_gdata, big_gdata = {}, {}, {}
    cml_pd_tbl, grw_pd_tbl, big_pd_tbl = '', '', ''
    
    # webparser instance
    wp = ''
    
    def __init__(self):
        self.wp = webparse.webparse()
        self.logger = logging.getLogger('main.portfolio')
    
    
    def process_parse(self, odata, gdata, upd_mkt, upd_val, p0, p1):
        # if update valuation, empty out and update everything
        if upd_val == 1:
            self.wp.clear_webcache()
            odata, gdata = self.process_parse(odata, gdata, 0, 0, p0, p1)
            
            for stk in self.idata['Portfolio']['Stocks'][p0][p1]:
                
                # grab latest date
                try:
                    odata[stk]['latest'] = self.gph[stk]['Rev Qtr date'][-1]
                except KeyError:
                    odata[stk]['latest'] = ''
                
                self.logger.info('\n====\nget valuation data for %s\n====' % stk)
                
                self.wp.pdata = odata
                for val in self.val_ls:
                    self.logger.info("get data for %s, %s" % (stk, val))
                    odata[stk][val] = self.wp.parse(stk, val)
                
                
                self.logger.info('\n====\nget graph data for %s\n====' % stk)
                
                # grab latest date
                try:
                    gdata[stk]['latest'] = self.gph[stk]['Rev Qtr date'][-1]
                except KeyError:
                    gdata[stk]['latest'] = ''
                    
                self.wp.pdata = gdata
                for val in self.graph_ls:
                    gdata[stk][val+' date'], gdata[stk][val] = self.wp.parse(stk, val, fn_type='graph')
                    
                del odata[stk]['latest']
                del gdata[stk]['latest']
                    
            self.mdb_update_needed = 1
            self.gph_update_needed = 1
            
        # if only update market cap, also update dependencies:
        # PS and PS_NXT
        elif upd_mkt == 1:
            odata, gdata = self.process_parse(odata, gdata, 0, 0, p0, p1)
            self.wp.pdata = odata

            for stk in self.idata['Portfolio']['Stocks'][p0][p1]:
                self.logger.info('\n====\nget mkt cap dependency for %s\n====' % stk)

                odata[stk]['Mkt Cap'], odata[stk]['PS TTM'] = self.update_mkt_cap_dep(stk)
                
                # we want to get the data for PS FY/1FY/2FY as well.. 
                # but since the Rev FY are not stored, parse them too
                for val in ['PS FY', 'PS 1FY', 'PS 2FY']:
                    odata[stk][val] = self.wp.parse(stk, val)
                    
            self.mdb_update_needed = 1
        
        # no update, just get from master db
        else:
            odata = {}
            gdata = {}
            
            for stk in self.idata['Portfolio']['Stocks'][p0][p1]:
                
                self.wp.pdata = odata
                odata[stk] = {}
                for val in self.val_ls:
                    try:
                        odata[stk][val] = self.mdb[stk][val]
                    # this exception is for data that's not present in database
                    except KeyError:
                        odata[stk][val] = self.wp.parse(stk, val)
                        self.mdb_update_needed = 1
            
                self.wp.pdata = gdata
                gdata[stk] = {}
                for val in self.graph_ls:
                    try:
                        gdata[stk][val] = self.gph[stk][val]
                        gdata[stk][val+' date'] = self.gph[stk][val+' date']
                    # this exception is for data that's not present in database
                    except KeyError:
                        gdata[stk][val+' date'], gdata[stk][val] = self.wp.parse(stk, val, fn_type='graph')
                        self.gph_update_needed = 1
                
        return odata, gdata
        
    
    def update_mkt_cap_dep(self, stk):
        mkt_cap = self.wp.parse(stk, 'Mkt Cap')
        ps_ttm  = float("{0:.3f}".format(mkt_cap/self.mdb[stk]['Rev TTM']))
        return mkt_cap, ps_ttm
    
    
    def update_db(self, odict, idict):
        for stk, vals in idict.items():
            if stk not in odict.keys():
                odict[stk] = {}
            for v_key, v_val in vals.items():
                odict[stk][v_key] = v_val
        return odict
    
    def save_to_db(self, upd_mdb, upd_gph):
        if upd_mdb:
            for db in [self.cml_odata, self.grw_odata, self.big_odata]:
                self.mdb = self.update_db(self.mdb, db)
        
                mfile = open('data/master_db.json', 'w')
                json.dump(self.mdb, mfile, indent=4)
                mfile.close()
        
            self.mdb_update_needed = 0
            print("INFO: Master DB Updated")
                
        if upd_gph:
            for db in [self.cml_gdata, self.grw_gdata, self.big_gdata]:
                self.gph = self.update_db(self.gph, db)
                
                mfile = open('data/graph_db.json', 'w')
                json.dump(self.gph, mfile, indent=4)
                mfile.close()
        
            self.gph_update_needed = 0
            print("INFO: Graph DB Updated")
    
    def open_db(self):
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
            pd_tbl.append(newdict)
        
        opd = pd.json_normalize(pd_tbl)
        # then convert to dataframe with header = valuation and index = stock
        #opd = opd.set_index('Stk')
        return opd
    
    
    def process(self, upd_mkt, upd_val):
        self.val_ls = self.idata['Portfolio']['Valuation']
        self.graph_ls = self.idata['Portfolio']['Graph']
        
        self.open_db()
        
        self.cml_odata, self.cml_gdata = self.process_parse(self.cml_odata, self.cml_gdata, 
                                                            upd_mkt, upd_val, 'Top', 'Growth')
        self.grw_odata, self.grw_gdata = self.process_parse(self.grw_odata, self.grw_gdata, 
                                                            upd_mkt, upd_val, 'Others', 'Growth')
        self.big_odata, self.big_gdata = self.process_parse(self.big_odata, self.big_gdata, 
                                                            upd_mkt, upd_val, 'Others', 'BigCap')
        
        self.save_to_db(self.mdb_update_needed, self.gph_update_needed)
        
        self.cml_pd_tbl = self.dict_to_pd(self.cml_odata)
        self.grw_pd_tbl = self.dict_to_pd(self.grw_odata)
        self.big_pd_tbl = self.dict_to_pd(self.big_odata)

        