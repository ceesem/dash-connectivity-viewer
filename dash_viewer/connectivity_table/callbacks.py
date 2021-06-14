from dash_viewer.common.neuron_data_base import NeuronData
from annotationframeworkclient.frameworkclient import FrameworkClient
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from ..common.link_utilities import (
    generate_statebuider_syn_grouped,
    generate_statebuilder,
    generate_statebuilder_pre,
    generate_statebuilder_post,
    generate_url_synapses,
    EMPTY_INFO_CACHE,
)
from ..common.dataframe_utilities import (
    stringify_root_ids,
    stringify_point_array,
    unstringify_point_array,
)
from ..common.dash_url_helper import _COMPONENT_ID_TYPE
from ..common.lookup_utilities import make_client, get_root_id_from_nuc_id
from .config import *

import datetime
import flask
import numpy as np
import pandas as pd

try:
    from loguru import logger
    import time
except:
    logger = None


InputDatastack = Input({"id_inner": "datastack", "type": _COMPONENT_ID_TYPE}, "value")
StateAnnoID = State({"id_inner": "anno-id", "type": _COMPONENT_ID_TYPE}, "value")
StateAnnoType = State({"id_inner": "cell-id-type", "type": _COMPONENT_ID_TYPE}, "value")
StateLiveQuery = State(
    {"id_inner": "live-query-toggle", "type": _COMPONENT_ID_TYPE}, "value"
)


def register_callbacks(app, config):
    @app.callback(
        Output("data-table", "selected_rows"),
        Input("reset-selection", "n_clicks"),
        Input("connectivity-tab", "value"),
    )
    def reset_selection(n_clicks, tab_value):
        return []

    @app.callback(
        Output("target-table-json", "data"),
        Output("source-table-json", "data"),
        Output("output-tab", "label"),
        Output("input-tab", "label"),
        Output("reset-selection", "n_clicks"),
        Output("client-info-json", "data"),
        Output("loading-spinner", "children"),
        Output("message-text", "children"),
        Input("submit-button", "n_clicks"),
        InputDatastack,
        StateAnnoID,
        StateAnnoType,
        StateLiveQuery,
    )
    def update_data(_, datastack_name, anno_id, id_type, live_query):
        if logger is not None:
            t0 = time.time()

        try:
            client = make_client(datastack_name, config)
            info_cache = client.info.info_cache[datastack_name]
            info_cache["global_server"] = client.server_address
        except Exception as e:
            return (
                [],
                [],
                "Output",
                "Input",
                1,
                EMPTY_INFO_CACHE,
                "",
                str(e),
            )

        if len(anno_id) == 0:
            return (
                [],
                [],
                "Output",
                "Input",
                1,
                info_cache,
                "",
                "No annotation id selected",
            )

        if len(anno_id) == 0:
            anno_id = None
            id_type = "anno_id"

        if live_query == "static":
            timestamp = client.materialize.get_timestamp()
        else:
            timestamp = datetime.datetime.now()
        if anno_id is None:
            root_id = None
        else:
            if id_type == "root_id":
                root_id = int(anno_id)
                anno_id = None
            elif id_type == "nucleus_id":
                root_id = get_root_id_from_nuc_id(
                    nuc_id=int(anno_id),
                    client=client,
                    nucleus_table=NUCLEUS_TABLE,
                    timestamp=timestamp,
                    live=live_query == "live",
                )
                anno_id = None
            else:
                raise ValueError('id_type must be either "root_id" or "nucleus_id"')

        info_cache["root_id"] = str(root_id)
        if live_query == "static":
            info_cache["ngl_timestamp"] = timestamp.timestamp()

        try:
            nrn_data = NeuronData(
                root_id,
                client,
                timestamp=timestamp,
                live_query=live_query == "live",
            )
            pre_targ_df = nrn_data.pre_targ_simple_df()
            pre_targ_df = stringify_root_ids(pre_targ_df, stringify_cols=["root_id"])

            post_targ_df = nrn_data.post_targ_simple_df()
            post_targ_df = stringify_root_ids(post_targ_df, stringify_cols=["root_id"])

            n_syn_pre = pre_targ_df[num_syn_col].sum()
            n_syn_post = post_targ_df[num_syn_col].sum()
        except Exception as e:
            return (
                [],
                [],
                "Output",
                "Input",
                1,
                EMPTY_INFO_CACHE,
                "",
                str(e),
            )

        if logger is not None:
            logger.info(
                f"Data update for {root_id} | time:{time.time() - t0:.2f} s, syn_in: {n_syn_post} , syn_out: {n_syn_pre}"
            )

        return (
            pre_targ_df.to_dict("records"),
            post_targ_df.to_dict("records"),
            f"Output (n = {n_syn_pre}",
            f"Input (n = {n_syn_post})",
            1,
            info_cache,
            "",
            f"Connectivity for root id {root_id}",
        )

    @app.callback(
        Output("data-table", "data"),
        Input("connectivity-tab", "value"),
        Input("target-table-json", "data"),
        Input("source-table-json", "data"),
    )
    def update_table(
        tab_value,
        pre_data,
        post_data,
    ):
        if tab_value == "tab-pre":
            return pre_data
        elif tab_value == "tab-post":
            return post_data
        else:
            return []

    @app.callback(
        Output("ngl_link", "href"),
        Input("connectivity-tab", "value"),
        Input("data-table", "derived_virtual_data"),
        Input("data-table", "derived_virtual_selected_rows"),
        Input("client-info-json", "data"),
    )
    def update_link(
        tab_value,
        rows,
        selected_rows,
        info_cache,
    ):
        if rows is None or len(rows) == 0:
            rows = {}
            sb = generate_statebuilder(info_cache)
            return sb.render_state(None, return_as="url")
        else:
            syn_df = pd.DataFrame(rows)
            if len(selected_rows) == 0:
                if tab_value == "tab-pre":
                    sb = generate_statebuilder_pre(info_cache)
                elif tab_value == "tab-post":
                    sb = generate_statebuilder_post(info_cache)
                else:
                    raise ValueError('tab must be "tab-pre" or "tab-post"')
                return sb.render_state(
                    syn_df.sort_values(by=num_syn_col, ascending=False), return_as="url"
                )
            else:
                if tab_value == "tab-pre":
                    anno_layer = "Output Synapses"
                elif tab_value == "tab-post":
                    anno_layer = "Input Synapses"
                sb = generate_statebuider_syn_grouped(
                    info_cache, anno_layer, preselect=len(selected_rows) == 1
                )
                return sb.render_state(syn_df.iloc[selected_rows], return_as="url")

    pass