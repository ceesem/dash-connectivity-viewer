from dash_connectivity_viewer.connectivity_table import create_app

if __name__ == "__main__":
    app = create_app(config={"LIVE_VALUE_DEFAULT": 0})
    app.run_server(port=8050)
