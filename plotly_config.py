def plotly_bersih():
    config = {
        "scrollZoom": True,  # Izinkan zoom dengan scroll
        "modeBarButtonsToRemove": [
            "zoom2d", "pan2d", "select2d", "lasso2d",
            "zoomIn2d", "zoomOut2d", "autoScale2d", 
            "sendDataToCloud", "hoverClosestCartesian",
            "hoverCompareCartesian"
        ],
        "displaylogo": False,  # Hapus logo Plotly
        "editable": True  # Membolehkan pengeditan langsung (opsional)
    }
    return config
