import plotly.graph_objects as go
import numpy as np


def _violin_plot(syn_df, x_col, y_col, name, side, color, xaxis, yaxis):
    return go.Violin(
        x=syn_df[x_col],
        y=syn_df[y_col],
        side=side,
        scalegroup="syn",
        name=name,
        points=False,
        line_color=f"rgb{color}",
        fillcolor=f"rgb{color}",
        xaxis=xaxis,
        yaxis=yaxis,
    )


def post_violin_plot(
    ndat,
    xaxis=None,
    yaxis=None,
):
    return _violin_plot(
        ndat.syn_all_df().query('direction == "post"'),
        x_col="x",
        y_col=ndat.config.synapse_depth_column,
        name="Post",
        side="negative",
        color=ndat.config.vis.dendrite_color,
        xaxis=xaxis,
        yaxis=yaxis,
    )


def pre_violin_plot(
    ndat,
    xaxis=None,
    yaxis=None,
):
    return _violin_plot(
        ndat.syn_all_df().query('direction == "pre"'),
        x_col="x",
        y_col=ndat.config.synapse_depth_column,
        name="Pre",
        side="positive",
        color=ndat.config.vis.axon_color,
        xaxis=xaxis,
        yaxis=yaxis,
    )


def synapse_soma_scatterplot(
    ndat,
    syn_depth_column,
    soma_depth_column,
    xaxis=None,
    yaxis=None,
):
    drop_columns = [syn_depth_column, soma_depth_column]
    targ_df = ndat.pre_syn_df_plus().dropna(subset=drop_columns)

    inhibitory_string_column = "inhib_string_column"
    targ_df[inhibitory_string_column] = ndat.config.vis.valence_string_map(
        targ_df[ndat.config.is_inhibitory_column]
    )

    panels = []
    valence_order = [
        ndat.config.vis.u_string,
        ndat.config.vis.e_string,
        ndat.config.vis.i_string,
    ]
    color_order = [
        ndat.config.vis.u_color,
        ndat.config.vis.e_color,
        ndat.config.vis.i_color,
    ]
    opacity_order = [
        ndat.config.vis.u_opacity,
        ndat.config.vis.e_opacity,
        ndat.config.vis.i_opacity,
    ]

    for val, color, alpha in zip(valence_order, color_order, opacity_order):
        targ_df_r = targ_df.query(f"{inhibitory_string_column}=='{val}'")
        panel = go.Scattergl(
            x=targ_df_r[soma_depth_column],
            y=targ_df_r[syn_depth_column],
            mode="markers",
            marker=dict(
                color=f"rgb{_format_color(color)}",
                line_width=0,
                size=5,
                opacity=alpha,
            ),
            xaxis=xaxis,
            yaxis=yaxis,
            name=val,
        )
        panels.append(panel)

    return panels


def bar_data(
    ndat,
    cell_type_column,
    num_syn_column,
):
    targ_df = ndat.partners_out().dropna(subset=[cell_type_column])
    return targ_df.groupby(cell_type_column)[num_syn_column].sum()


def _bar_plot(
    bar_data,
    name,
    color,
):
    return go.Bar(
        name=name,
        x=bar_data.values,
        y=bar_data.index,
        marker_color=f"rgb{color}",
        orientation="h",
    )


def _format_color(color, alpha=None):
    color = tuple(np.floor(255 * np.array(color)).astype(int))
    if alpha is None:
        return color
    else:
        return tuple(list(color) + [alpha])


def _prepare_bar_plot(
    ndat,
    cell_type_column,
    color,
    cell_types,
    valence,
):
    if valence == "u":
        if cell_types is None:
            cell_types = np.unique(
                ndat.property_data(ndat.cell_type_table)[cell_type_column]
            )
        name = "Targets"
    else:
        if valence == "i":
            map_ind = "i"
            name = "I Targets"
        elif valence == "e":
            map_ind = "e"
            name = "E Targets"

        if cell_types is None:
            cell_types = (
                ndat.property_data(ndat.cell_type_table)
                .groupby(ndat.valence_map["column"])
                .agg({cell_type_column: np.unique})
                .loc[ndat.valence_map[map_ind]][cell_type_column]
            )

    bdat = bar_data(ndat, cell_type_column, ndat.config.num_syn_col)

    # Fill in any cell types in the table
    for ct in cell_types:
        if ct not in bdat.index:
            bdat.loc[ct] = 0

    return _bar_plot(
        bdat.sort_index().loc[cell_types],
        name,
        _format_color(color),
    )


def excitatory_bar_plot(
    ndat,
    cell_type_column,
    cell_types=None,
):
    return _prepare_bar_plot(
        ndat, cell_type_column, ndat.config.vis.e_color, cell_types, "e"
    )


def inhibitory_bar_plot(
    ndat,
    cell_type_column,
    cell_types=None,
):
    return _prepare_bar_plot(
        ndat, cell_type_column, ndat.config.vis.i_color, cell_types, "i"
    )


def uniform_bar_plot(
    ndat,
    cell_type_column,
    cell_types=None,
):
    return _prepare_bar_plot(
        ndat, cell_type_column, ndat.config.vis.u_color, cell_types, "u"
    )