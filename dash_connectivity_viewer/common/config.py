###########################################
### Default data and request parameters ###
###########################################
def parse_environ_vector(input, num_type):
    return [num_type(x) for x in input.split(",")]


def bound_pt_position(pt):
    return f"{pt}_position"


def bound_pt_root_id(pt):
    return f"{pt}_root_id"


class CommonConfig(object):
    def __init__(self, config):
        self.default_datastack = config.get("datastack")
        if self.default_datastack is None:
            raise ValueError("Must datastack parameter!")

        self.server_address = config.get("server_address")
        if self.server_address is None:
            raise ValueError("Must set server address parameter!")

        self.disallow_live_query = config.get("disallow_live_query", False)
        self.image_black = config.get("image_black", 0)
        self.image_white = config.get("image_white", 1)

        self.target_root_id_per_call = config.get("target_root_id_per_call", 200)
        self.max_chunks = config.get("max_chunks", 20)
        self.pool_maxsize = 2 * self.max_chunks
        self.voxel_resolution = config.get("voxel_resolution")

        ##############################
        ### Link generation limits ###
        ##############################

        self.max_dataframe_length = config.get("max_dataframe_length", 8_000)
        self.max_server_dataframe_length = config.get(
            "max_server_dataframe_length", 20_000
        )

        # If None, the info service is used
        self.nucleus_table = config.get("nucleus_table", None)
        self.nucleus_id_column = config.get("nucleus_id_column", "id")

        # Used to look up number of neurons per root id
        self.soma_table = self.nucleus_table
        self.soma_id_column = self.nucleus_id_column

        # Used to look up connectivity
        # If None, the info service is used
        self.synapse_table = config.get("synapse_table", None)
        self.syn_id_col = "id"
        self.pre_pt_root_id = "pre_pt_root_id"
        self.post_pt_root_id = "post_pt_root_id"
        self.synapse_aggregation_rules = config.get("synapse_aggregation_rules", {})

        self.syn_pt_prefix = config.get("syn_position_column", "ctr_pt")
        self.syn_pt_position = bound_pt_position(self.syn_pt_prefix)

        self.soma_pt_prefix = config.get("soma_postion_column", "pt")
        self.soma_pt_position = bound_pt_position(self.soma_pt_prefix)
        self.soma_pt_root_id = bound_pt_root_id(self.soma_pt_prefix)

        self.soma_ct_col = config.get("soma_cell_type_column", "cell_type")
        self.soma_table_cell_category = config.get("soma_table_cell_type")
        if self.soma_ct_col and self.soma_table_cell_category:
            self.soma_table_query = (
                f"{self.soma_ct_col} == '{self.soma_table_cell_category}'"
            )
        else:
            self.soma_table_query = None

        self.num_soma_prefix = "num"
        self.num_syn_col = "num_syn"
        self.root_id_col = "root_id"

        self.num_soma_suffix = "_soma"
        self.num_soma_col = f"{self.num_soma_prefix}{self.num_soma_suffix}"

        self.soma_position_agg = self.soma_pt_position + self.num_soma_suffix

        self.synapse_table_columns_base = [
            "id",
            self.pre_pt_root_id,
            self.post_pt_root_id,
            self.syn_pt_position,
        ]

        additional_syn_merges = []
        for _, v in self.synapse_aggregation_rules.items():
            if v["column"] not in additional_syn_merges:
                additional_syn_merges.append(v["column"])

        self.synapse_table_columns_dataframe = (
            self.synapse_table_columns_base + additional_syn_merges
        )

        self.target_table_display = [
            self.root_id_col,
            self.syn_pt_position,
            self.num_syn_col,
            self.num_soma_col,
        ] + list(self.synapse_aggregation_rules.keys())

        self.soma_table_columns = [
            self.soma_pt_root_id,
            self.soma_pt_position,
            self.num_soma_col,
        ]