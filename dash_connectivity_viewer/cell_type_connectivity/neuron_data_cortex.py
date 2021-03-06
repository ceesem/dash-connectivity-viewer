import pandas as pd
import numpy as np
from ..common.neuron_data_base import NeuronData


def _schema_property_table(config, schema_name=None):
    prop_table = {
        "root_id": "pt_root_id",
        "include": ["classification_system", "cell_type"],
    }
    if schema_name:
        prop_table["table_bridge_schema"] = config.allowed_cell_type_schema_bridge.get(
            schema_name
        )
    return prop_table


def _cell_type_property_entry(cell_type_table, config, schema_name=None):
    return {cell_type_table: _schema_property_table(config, schema_name=schema_name)}


def _is_inhibitory_df(df, is_inhibitory_column, valence_map):
    if len(df) == 0:
        df[is_inhibitory_column] = None

    col = valence_map.get("column", None)
    e_str = valence_map.get("e", None)
    i_str = valence_map.get("i", None)
    ei_str = []
    if e_str:
        ei_str.append(e_str)
    if i_str:
        ei_str.append(i_str)

    def _is_inhibitory_row(row):
        if row[col] in ei_str:
            return row[col] == i_str
        else:
            return np.nan

    df[is_inhibitory_column] = df.apply(lambda x: _is_inhibitory_row(x), axis=1)
    return df


def _compute_depth_y(xyz, data_resolution):
    if np.any(pd.isna(xyz)):
        return np.nan
    else:
        return xyz[1] * data_resolution[1] / 1_000


def _extract_depth(df, depth_column, position_column, data_resolution):
    if len(df) == 0:
        df[depth_column] = None
        return df

    df[depth_column] = df[position_column].apply(
        lambda x: _compute_depth_y(x, data_resolution)
    )
    return df


class NeuronDataCortex(NeuronData):
    def __init__(
        self,
        object_id,
        client,
        config,
        cell_type_table=None,
        schema_name=None,
        timestamp=None,
        n_threads=None,
        id_type="root",
    ):

        self.config = config
        self.cell_type_table = cell_type_table
        self.schema_type = schema_name
        if cell_type_table is not None:
            property_tables = _cell_type_property_entry(
                cell_type_table, config, schema_name=self.schema_type
            )
        else:
            property_tables = dict()
        self.valence_map = config.table_valence_map.get(cell_type_table)
        super().__init__(
            object_id,
            client,
            config,
            property_tables=property_tables,
            timestamp=timestamp,
            n_threads=n_threads,
            id_type=id_type,
        )

    def _decorate_synapse_dataframe(self, df, merge_column):
        df = self._merge_property_tables(df, merge_column)

        if self.config.is_inhibitory_column is not None:
            if self.valence_map:
                df = _is_inhibitory_df(
                    df,
                    self.config.is_inhibitory_column,
                    self.valence_map,
                )
            else:
                df[self.config.is_inhibitory_column] = np.nan
        if self.config.soma_depth_column is not None and self.soma_table is not None:
            df = _extract_depth(
                df,
                self.config.soma_depth_column,
                self.config.soma_position_agg,
                self.property_data_resolution(self.soma_table),
            )
        return df

    def pre_syn_df_plus(self):
        return self._decorate_synapse_dataframe(
            self.pre_syn_df(), self.config.post_pt_root_id
        )

    def post_syn_df_plus(self):
        return self._decorate_synapse_dataframe(
            self.post_syn_df(), self.config.pre_pt_root_id
        )

    def _decorate_partner_dataframe(self, df):
        if self.config.soma_depth_column is not None and self.soma_table is not None:
            df = _extract_depth(
                df,
                self.config.soma_depth_column,
                self.config.soma_position_agg,
                self.property_data_resolution(self.soma_table),
            )
        if self.config.is_inhibitory_column is not None:
            if self.valence_map:
                df = _is_inhibitory_df(
                    df,
                    self.config.is_inhibitory_column,
                    self.valence_map,
                )
            else:
                df[self.config.is_inhibitory_column] = np.nan
        return df

    def partners_in_plus(self):
        return self._decorate_partner_dataframe(self.partners_in())

    def partners_out_plus(self):
        return self._decorate_partner_dataframe(self.partners_out())

    def _get_syn_df(self):
        super()._get_syn_df()
        if self.config.synapse_depth_column is not None:
            for syn_df in [self._pre_syn_df, self._post_syn_df]:
                _ = _extract_depth(
                    syn_df,
                    self.config.synapse_depth_column,
                    self.config.syn_pt_position,
                    self._synapse_data_resolution,
                )

    def soma_depth(self):
        return _compute_depth_y(
            self.soma_location(), self.property_data_resolution(self.soma_table)
        )
