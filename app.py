import logging
from flask import Flask, render_template, jsonify, request
import pandas as pd
import plotly.graph_objects as go

app = Flask(__name__)

try:
    # Setup logging
    logging.basicConfig(level=logging.DEBUG)

    # Log the beginning of the application
    app.logger.info("Starting the Flask application")

    # Load the dataset
    df = pd.read_excel('istanbul_market_data/pazar_verisi.xlsx')
    app.logger.info("Dataset loaded successfully")

    # Split the coordinates into separate latitude and longitude columns
    df[['Latitude', 'Longitude']] = df['Koordinat'].str.split(',', expand=True)
    df['Latitude'] = df['Latitude'].astype(float)
    df['Longitude'] = df['Longitude'].astype(float)
    app.logger.info("Coordinates split successfully")

    # Create a combined list of unique markers for days
    unique_days = df['Gün'].unique()
    symbols = ['circle', 'square', 'diamond', 'cross', 'x', 'triangle-up', 'triangle-down', 'triangle-left', 'triangle-right']
    day_to_symbol = {day: symbols[i % len(symbols)] for i, day in enumerate(unique_days)}
    app.logger.info("Day to symbol mapping created successfully")

    def create_map(selected_days, selected_types):
        fig = go.Figure()

        # Filter the dataset based on the selected days and market types
        filtered_df = df[(df['Gün'].isin(selected_days)) & (df['Pazar Tipi'].isin(selected_types))]
        app.logger.info("Filtered the dataset successfully")

        # Add traces for each market type with unique symbols for each day
        for market_type in filtered_df['Pazar Tipi'].unique():
            for day in filtered_df['Gün'].unique():
                day_type_df = filtered_df[(filtered_df['Pazar Tipi'] == market_type) & (filtered_df['Gün'] == day)]
                fig.add_trace(go.Scattermapbox(
                    lat=day_type_df['Latitude'],
                    lon=day_type_df['Longitude'],
                    mode='markers',
                    marker=go.scattermapbox.Marker(
                        size=9,
                        symbol=day_to_symbol[day]
                    ),
                    name=f"{market_type} ({day})",
                    text=day_type_df['Pazar Adı'],
                    hoverinfo='text'
                ))
        app.logger.info("Map created successfully")

        # Set up the map layout
        fig.update_layout(
            mapbox=dict(
                style="carto-positron",
                zoom=10,
                center=dict(lat=df['Latitude'].mean(), lon=df['Longitude'].mean())
            ),
            showlegend=True,
            legend_title_text='Market Type and Day',
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        
        return fig.to_html(full_html=False)

    @app.route('/')
    def index():
        app.logger.info("Index route accessed")
        return render_template('index.html', days=unique_days, types=df['Pazar Tipi'].unique())

    @app.route('/update_map', methods=['POST'])
    def update_map():
        app.logger.info("Update map route accessed")
        data = request.json
        selected_days = data['days']
        selected_types = data['types']
        map_html = create_map(selected_days, selected_types)
        return jsonify({'map_html': map_html})

except Exception as e:
    app.logger.error("Unhandled Exception: %s", e, exc_info=True)

if __name__ == '__main__':
    app.run(debug=True)
