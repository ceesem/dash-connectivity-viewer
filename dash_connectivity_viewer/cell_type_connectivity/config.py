import numpy as np
import seaborn as sns
import pandas as pd
import os
import pathlib
from ..common.config import CommonConfig, bound_pt_position, bound_pt_root_id

####################
### Column names ###
####################


class VisConfig:
    def __init__(
        self,
        dendrite_color,
        axon_color,
        e_palette,
        i_palette,
        u_palette,
        tick_locs=[],
        tick_labels=[],
        base_ind=6,
        n_e_colors=9,
        n_i_colors=9,
        n_u_colors=9,
        e_string="Exc",
        i_string="Inh",
        u_string="Unknown",
        e_opacity=0.5,
        i_opacity=0.75,
        u_opacity=0.3,
    ):
        self.dendrite_color = dendrite_color
        self.axon_color = axon_color

        self.e_colors = sns.color_palette(e_palette, n_colors=n_e_colors)
        self.i_colors = sns.color_palette(i_palette, n_colors=n_i_colors)
        self.u_colors = sns.color_palette(u_palette, n_colors=n_u_colors)
        self.base_ind = base_ind

        self.e_string = e_string
        self.i_string = i_string
        self.u_string = u_string

        self.e_opacity = e_opacity
        self.i_opacity = i_opacity
        self.u_opacity = u_opacity

        self.ticklocs = tick_locs
        self.tick_labels = tick_labels

    @property
    def clrs(self):
        return np.array([self.axon_color, self.dendrite_color])

    @property
    def e_color(self):
        return self.e_colors[self.base_ind]

    @property
    def i_color(self):
        return self.i_colors[self.base_ind]

    @property
    def u_color(self):
        return self.u_colors[max(self.base_ind - 2, 0)]

    @property
    def valence_colors(self):
        return np.vstack([self.e_color, self.i_color, self.u_color])

    def valence_color_map(self, is_inhib):
        cmap = []
        for x in is_inhib:
            if pd.isna(x):
                cmap.append(2)
            elif x:
                cmap.append(0)
            else:
                cmap.append(1)
        return np.array(cmap)

    def valence_string_map(self, is_inhib):
        smap = []
        for x in is_inhib:
            if pd.isna(x):
                smap.append(self.u_string)
            elif x:
                smap.append(self.i_string)
            else:
                smap.append(self.e_string)
        return smap


class TypedConnectivityConfig(CommonConfig):
    def __init__(self, config):
        super().__init__(config)

        self.ct_conn_cell_type_column = config.get(
            "ct_conn_cell_type_column", "cell_type"
        )

        self.soma_depth_column = config.get("ct_conn_soma_depth_column", "soma_depth")
        self.synapse_depth_column = config.get("ct_conn_syn_depth_column", "syn_depth")
        self.is_inhibitory_column = config.get(
            "ct_conn_is_inhibitory_column", "is_inhibitory"
        )

        self.cell_type_dropdown_options = config.get("cell_type_dropdown_options", [])
        self.default_cell_type_option = config.get("default_cell_type_option", "")

        self.omit_cell_type_tables = config.get("omit_cell_type_tables", [])
        self.synapse_aggregation_rules = config.get("synapse_aggregation_rules", {})
        self.aggregation_columns = list(self.synapse_aggregation_rules.keys())
        self.table_valence_map = config.get("valence_map", {})
        self.table_columns = (
            [
                self.root_id_col,
                self.num_syn_col,
                self.ct_conn_cell_type_column,
                self.soma_depth_column,
                self.is_inhibitory_column,
            ]
            + self.aggregation_columns
            + [self.num_soma_col]
        )

        self.show_plots = config.get("ct_conn_show_plots", True)
        self.show_depth_plots = config.get("ct_conn_show_depth_plots", True)

        # Next thing to fix!
        base_dir = pathlib.Path(os.path.dirname(__file__))
        data_path = base_dir.parent.joinpath("common/data")
        self.layer_bnds = np.load(f"{data_path}/layer_bounds_v1.npy")
        self.height_bnds = np.load(f"{data_path}/height_bounds_v1.npy")
        ticklocs = np.concatenate(
            [self.height_bnds[0:1], self.layer_bnds, self.height_bnds[1:]]
        )

        self.allowed_cell_type_schema_bridge = config.get("ct_conn_cell_type_schema")
        self.allowed_cell_type_schema = list(
            self.allowed_cell_type_schema_bridge.keys()
        )

        dendrite_color = config.get("ct_conn_dendrite_color", (0.894, 0.102, 0.110))
        axon_color = config.get("ct_conn_axon_color", (0.227, 0.459, 0.718))

        e_color_palette = config.get("ct_conn_e_palette", "RdPu")
        i_color_palette = config.get("ct_conn_i_palette", "Greens")
        u_color_palette = config.get("ct_conn_u_palette", "Greys")
        base_ind = int(config.get("ct_conn_palette_base", 6))

        self.vis = VisConfig(
            dendrite_color,
            axon_color,
            e_color_palette,
            i_color_palette,
            u_color_palette,
            base_ind=base_ind,
            tick_locs=ticklocs,
            tick_labels=["L1", "L2/3", "L4", "L5", "L6", "WM", ""],
        )
