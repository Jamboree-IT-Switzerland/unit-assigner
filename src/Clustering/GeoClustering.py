import logging
import numpy as np
from sklearn.cluster import KMeans
from typing import List

from src.Participant import Participant

logger = logging.getLogger(__name__)

class GeoClustering:
    def __init__(self, n_clusters: int = 5, random_state: int = 42):
        self.n_clusters = n_clusters
        self.random_state = random_state
        self.kmeans = None
        self.cluster_centers = None

    def cluster_participants(self, participants: List[Participant]) -> dict:
        # Filter participants with valid geo_data
        valid_participants = [
            p for p in participants
            if p.geo_data is not None and hasattr(p.geo_data, 'x') and hasattr(p.geo_data, 'y')
        ]

        if not valid_participants:
            logger.warning("No participants with valid geo_data found")
            return {}

        if len(valid_participants) < self.n_clusters:
            logger.warning(
                f"Number of valid participants ({len(valid_participants)}) is less than "
                f"requested clusters ({self.n_clusters}). Adjusting n_clusters."
            )
            self.n_clusters = len(valid_participants)

        # Extract x, y coordinates
        coordinates = np.array([[p.geo_data.x, p.geo_data.y] for p in valid_participants])

        # Perform k-means clustering
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=self.random_state)
        cluster_labels = self.kmeans.fit_predict(coordinates)
        self.cluster_centers = self.kmeans.cluster_centers_

        # Assign cluster labels to participants
        for participant, label in zip(valid_participants, cluster_labels):
            participant.cluster = int(label)

        # Group participants by cluster
        clusters = {}
        for participant in valid_participants:
            cluster_id = participant.cluster
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(participant)

        logger.info(f"Successfully clustered {len(valid_participants)} participants into {self.n_clusters} clusters")
        for cluster_id, members in clusters.items():
            logger.info(f"Cluster {cluster_id}: {len(members)} participants")

        return clusters

    def get_cluster_statistics(self, clusters: dict) -> dict:
        stats = {}
        for cluster_id, members in clusters.items():
            coords = np.array([[p.geo_data.x, p.geo_data.y] for p in members])
            stats[cluster_id] = {
                'size': len(members),
                'center': self.cluster_centers[cluster_id].tolist(),
                'mean_x': float(np.mean(coords[:, 0])),
                'mean_y': float(np.mean(coords[:, 1])),
                'std_x': float(np.std(coords[:, 0])),
                'std_y': float(np.std(coords[:, 1]))
            }
        return stats
