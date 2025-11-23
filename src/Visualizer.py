import os
import logging
import folium
import pandas as pd
import numpy as np
from folium import plugins
from typing import List, Dict

from src.Participant import Participant

logger = logging.getLogger(__name__)

# Get the base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
kanton_overview = os.path.join(BASE_DIR, 'data', 'geodata', 'Switzerland_overview.csv')
kanton_geojson = os.path.join(BASE_DIR, 'data', 'geodata', 'switzerland.geojson')
kanton_data = pd.read_csv(kanton_overview)

class ParticipantVisualizer:
    # Swiss geographic center and bounds
    SWISS_CENTER = [46.8182, 8.2275]  # Center of Switzerland
    SWISS_BOUNDS = [[45.8, 5.9], [47.8, 10.5]]  # Southwest and Northeast corners

    def __init__(self):
        self.colors = [
            'red', 'blue', 'green', 'purple', 'orange',
            'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen',
            'cadetblue', 'darkpurple', 'pink', 'lightblue', 'lightgreen',
            'gray', 'black', 'lightgray'
        ]

    def create_interactive_map(self, participants: List[Participant],
                               clusters: Dict[int, List[Participant]] = None,
                               output_file: str = 'participant_map.html'):
        # Filter participants with valid geo_data
        valid_participants = [
            p for p in participants
            if p.geo_data is not None and hasattr(p.geo_data, 'lat') and hasattr(p.geo_data, 'lon')
        ]

        if not valid_participants:
            logger.error("No participants with valid geo_data found")
            return None

        # Create map centered on Switzerland
        map = folium.Map(
            location=self.SWISS_CENTER,
            zoom_start=8,
            tiles='OpenStreetMap'
        )

        # Add Swiss cantonal choropleth layer
        folium.Choropleth(
            geo_data=kanton_geojson,
            data=kanton_data,
            columns=['CantonNumber', 'Density'],
            key_on='feature.properties.KANTONSNUM',
            threshold_scale=[26, 100, 200, 500, 1000, 5072],
            fill_color='BuPu',
            fill_opacity=0.6,
            line_opacity=0.2,
            legend_name='Population Density (per km²)',
            name='Canton Density'
        ).add_to(map)

        # Add markers for each participant
        marker_cluster = plugins.MarkerCluster()

        for participant in valid_participants:
            geo = participant.geo_data

            # Determine marker color based on cluster
            if participant.cluster is not None:
                color = self.colors[participant.cluster % len(self.colors)]
            else:
                color = 'blue'

            # Create popup text
            popup_text = f"""
            <b>{participant.pfadiname or participant.vorname}</b><br>
            {participant.vorname} {participant.nachname}<br>
            {participant.plz} {participant.ort}<br>
            Abteilung: {participant.hauptebene}<br>
            Funktion: {participant.funktion_im_jamboree}<br>
            Kantonalverband: {participant.kantonalverband} <br>
            """

            if participant.cluster is not None:
                popup_text += f"<br>Cluster: {participant.cluster}"

            # Add marker
            folium.Marker(
                location=[geo.lat, geo.lon],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{participant.pfadiname or participant.vorname} - {participant.ort}",
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(marker_cluster)

        marker_cluster.add_to(map)

        # Add cluster centers if available
        if clusters:
            for cluster_id, members in clusters.items():
                if members:
                    # Calculate center from members
                    lats = [p.geo_data.lat for p in members]
                    lons = [p.geo_data.lon for p in members]
                    center_lat = np.mean(lats)
                    center_lon = np.mean(lons)

                    color = self.colors[cluster_id % len(self.colors)]

                    # Add circle for cluster center
                    folium.Circle(
                        location=[center_lat, center_lon],
                        radius=5000,  # 5km radius
                        popup=f'Cluster {cluster_id}<br>{len(members)} participants',
                        color=color,
                        fill=True,
                        fillOpacity=0.2
                    ).add_to(map)

                    # Add marker for cluster center
                    folium.Marker(
                        location=[center_lat, center_lon],
                        popup=f'<b>Cluster {cluster_id} Center</b><br>{len(members)} participants',
                        icon=folium.Icon(color=color, icon='star', prefix='fa')
                    ).add_to(map)

        # Add layer control
        folium.LayerControl().add_to(map)

        # Add fullscreen option
        plugins.Fullscreen().add_to(map)

        # Save map
        map.save(output_file)
        logger.info(f"Interactive map saved to {output_file}")
        logger.info(f"Total participants plotted: {len(valid_participants)}")

        return map
