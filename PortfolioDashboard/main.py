import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table

import plotly.graph_objs as go

from dash.dependencies import Input, Output, State

import portfolio
import json
import logger

in_app = 0
app = dash.Dash(__name__)

table_cond = [
    {
        'if': {'column_id': c,
               'filter_query': '{' + c + '} > 30'},
        'color': 'Red', 'fontWeight': 'bold'
    } for c in ['PS TTM', 'PS FY', 'PS 1FY', 'PS 2FY'] ] + [
    {
        'if': {'column_id': c,
                'filter_query': '{' + c + '} > 20 && {' + c + '} <= 30'},
        'color': 'DarkOrange', 'fontWeight': 'bold'
    } for c in ['PS TTM', 'PS FY', 'PS 1FY', 'PS 2FY'] ] + [
    {
        'if': {'column_id': c,
                'filter_query': '{' + c + '} < 15'},
        'color': 'LimeGreen', 'fontWeight': 'bold'
    } for c in ['PS TTM', 'PS FY', 'PS 1FY', 'PS 2FY'] 
]



style_cond = [
    {
        'if': {'column_id': c},
        'width': '9%',
    } for c in ['Rev Grow', 'RevGw FY', 'RevGw 1FY', 'RevGw 2FY'] ] + [
    {
        'if': {'column_id': c},
        'width': '9%',
    } for c in ['PS TTM', 'PS FY', 'PS 1FY', 'PS 2FY']
]

graph_loc = {
    'TL': 'Rev Qtr',
    'TM': 'Rev TTM',
    'TR': 'Rev Grow',
    'BL': 'Inc Qtr',
    'BM': 'Inc TTM',
    'BR': 'Inc Grow',
}

def create_fig(title, values = [], **kwargs):
    fig = go.Figure(
        data = values,
        layout = go.Layout(
            #autosize = True,
            title = go.layout.Title(text=title),
            title_x = 0.5,
            margin = dict(l=20, r=20, t=50, b=10),
        )
    )
    fig.update_layout(xaxis_visible = False)
    
    try:
        fig.update_layout(yaxis_type = kwargs['yaxis_type'])
    except KeyError:
        pass
    
    return fig

def create_table(i_id, pd_tbl, **kwargs):
    tbl = dash_table.DataTable(
        id = i_id,
        columns = [{'name':i, 'id':i} for i in pd_tbl.columns],
        data = pd_tbl.to_dict('records'),
        fixed_rows = {'headers': True},
        sort_action = 'native',
        
        style_table = {
            'width': '100%',
            #'height': '50%',
            'height': kwargs['height'],
            'overflowY': 'auto'
        },
        
        style_data_conditional = table_cond,
        style_cell_conditional = style_cond,
        cell_selectable = True,
    )
    return tbl 


def refresh():
    global pf
    jfile = open('data/stocks.json', 'r')
    pf.idata = json.load(jfile)
    pf.process(upd_val=0, upd_mkt=0)


def main():
    global pf
    pf = portfolio.portfolio()
    
    refresh()
  
    app.layout = html.Div(className='wrapper', children = [

        html.Div(className='tables', children = [
            html.Button('Refresh', id='btn_refresh'),
            html.Button('Update Mkt Cap', id='btn_upd_mkt'),
            html.Button('Update Valuation', id='btn_upd_val'),
            html.Button('Save to DB', id='btn_save_db'),
        
        
        #html.Div(className='tables_r1c0', children = [
            html.Div(children = [
                html.H4("Top Stocks", className='tbl-title'),
                create_table(i_id='cml_table', pd_tbl=pf.cml_pd_tbl, height=300),
            ]),
            
            html.Div(children = [
                html.H4("Growth Stocks", className='tbl-title'),
                create_table(i_id='grw_table', pd_tbl=pf.grw_pd_tbl, height=260),
            ]),
            
            html.Div(children = [
                html.H4('Big Cap Stocks', className='tbl-title'),
                create_table(i_id='big_table', pd_tbl=pf.big_pd_tbl, height=200),
            ]),
        #]),
        ]),

        html.Div(className = 'status', children = [
            html.H4(id='update_msg', className='status-msg'),
            html.Span('Selected Stock: '),
            html.Span(id='selected_stk'),
        ]),
        
        html.Div(className = 'charts', children = [
            dcc.Graph(id='graph_TL', figure = create_fig(graph_loc['TL'], [])),
            dcc.Graph(id='graph_TM', figure = create_fig(graph_loc['TM'], [])),
            dcc.Graph(id='graph_TR', figure = create_fig(graph_loc['TR'], [])),
            dcc.Graph(id='graph_BL', figure = create_fig(graph_loc['BL'], [])),
            dcc.Graph(id='graph_BM', figure = create_fig(graph_loc['BM'], [])),
            dcc.Graph(id='graph_BR', figure = create_fig(graph_loc['BR'], [])),
        ]),
    ]
    )
    
    
    app.run_server(debug=True)



def get_tables():
    cml_col  = [{'name':i, 'id':i} for i in pf.cml_pd_tbl.columns]
    cml_data = pf.cml_pd_tbl.to_dict('records')
    grw_col  = [{'name':i, 'id':i} for i in pf.grw_pd_tbl.columns]
    grw_data = pf.grw_pd_tbl.to_dict('records')
    big_col  = [{'name':i, 'id':i} for i in pf.big_pd_tbl.columns]
    big_data = pf.big_pd_tbl.to_dict('records')
    return (cml_col, cml_data, grw_col, grw_data, big_col, big_data)



''' 
Button callbacks
'''
@app.callback(
    Output('update_msg', 'children'),
    Output('cml_table', 'columns'),
    Output('cml_table', 'data'),
    Output('grw_table', 'columns'),
    Output('grw_table', 'data'),
    Output('big_table', 'columns'),
    Output('big_table', 'data'),
    [Input('btn_refresh', 'n_clicks'),
     Input('btn_upd_mkt', 'n_clicks'),
     Input('btn_upd_val', 'n_clicks'),
     Input('btn_save_db', 'n_clicks')]
)
def update_top_button(btn_refresh, btn_upd_mkt, btn_upd_val, btn_save_db):
    global in_app
    msg = 'Status Message'
    
    all_tbl = get_tables()
    
    changed_id = dash.callback_context.triggered[0]['prop_id']
    
    if 'btn_refresh' in changed_id:
        refresh()
        all_tbl = get_tables()
        msg = "JSON reloaded"
    
    elif 'btn_upd_val' in changed_id:
        pf.process(upd_val=1, upd_mkt=0)
        msg = 'Valuations Updated'
        all_tbl = get_tables()
    
    elif 'btn_upd_mkt' in changed_id:
        pf.process(upd_val=0, upd_mkt=1)
        msg = 'Market Cap Updated'
        all_tbl = get_tables()
    
    elif 'btn_save_db' in changed_id:
        msg = 'Saving to Master DB'
        pf.save_to_db(1, 1)
    
    return (msg, ) + all_tbl


''' 
Table selection callback
'''
@app.callback(
    Output('selected_stk', 'children'),
    Output('cml_table', 'style_data_conditional'),
    Output('grw_table', 'style_data_conditional'),
    Output('big_table', 'style_data_conditional'),

    Output('graph_TL', 'figure'),
    Output('graph_TM', 'figure'),
    Output('graph_TR', 'figure'),
    Output('graph_BL', 'figure'),
    Output('graph_BM', 'figure'),
    Output('graph_BR', 'figure'),
    
    [Input('cml_table', 'selected_cells'),
     Input('grw_table', 'selected_cells'),
     Input('big_table', 'selected_cells')],
    
    [State('cml_table', 'derived_virtual_indices'),
     State('grw_table', 'derived_virtual_indices'),
     State('big_table', 'derived_virtual_indices')]
)
def pick_tbl_entry(cml_cell, grw_cell, big_cell, cml_idx, grw_idx, big_idx):
    stk_name = '...'
    cml_dict, grw_dict, big_dict = table_cond, table_cond, table_cond

    g_TL = create_fig(graph_loc['TL'], [])
    g_TM = create_fig(graph_loc['TM'], [])
    g_TR = create_fig(graph_loc['TR'], [])
    g_BL = create_fig(graph_loc['BL'], [])
    g_BM = create_fig(graph_loc['BM'], [])
    g_BR = create_fig(graph_loc['BR'], [])
    
    if (cml_cell != None) or (grw_cell != None) or (big_cell != None):
        clicked_tbl = dash.callback_context.triggered[0]
        '''
        # clicked tbl will contain:
        # [{'prop_id': 'cml_table.selected_cells', 
        #   'value': [{'row': 3, 'column': 5, 'column_id': 'PS Nxt'}]}]
        '''
        tbl = clicked_tbl['prop_id'].split('.')[0].split('_')[0]
        pd_tbl = getattr(pf, tbl + '_pd_tbl')
        
        try:
            if tbl == 'cml'  : stk_name = pd_tbl.loc[cml_idx[clicked_tbl['value'][0]['row']], 'Stk']
            elif tbl == 'grw': stk_name = pd_tbl.loc[grw_idx[clicked_tbl['value'][0]['row']], 'Stk']
            elif tbl == 'big': stk_name = pd_tbl.loc[big_idx[clicked_tbl['value'][0]['row']], 'Stk']
            style_dict = table_cond + [{'if': {'row_index': clicked_tbl['value'][0]['row']},
                           'background_color': 'MistyRose'}]
        except IndexError:
            stk_name = '...'
            style_dict = table_cond
        
        if tbl == 'cml'     : cml_dict = style_dict
        elif tbl == 'grw'   : grw_dict = style_dict
        elif tbl == 'big'   : big_dict = style_dict
        
        '''
        update the graphs
        '''
        if stk_name != '...':
            gdata = getattr(pf, tbl + '_gdata')
            g_ls = [0] * 6
            s_ls = ['TL', 'TM', 'TR', 'BL', 'BM', 'BR']
            
            for g in range(len(g_ls)):
                g_ls[g] = create_fig(graph_loc[s_ls[g]],
                                     go.Bar(y = gdata[stk_name][graph_loc[s_ls[g]]],
                                            x = gdata[stk_name][graph_loc[s_ls[g]]+' date']))
            
            [g_TL, g_TM, g_TR, g_BL, g_BM, g_BR] = g_ls
        
    return (stk_name, cml_dict, grw_dict, big_dict, g_TL, g_TM, g_TR, g_BL, g_BM, g_BR)


if __name__ == "__main__":
    main()
    
