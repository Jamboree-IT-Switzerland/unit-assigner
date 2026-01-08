import logging
import numpy as np

from math import ceil
from k_means_constrained import KMeansConstrained
from typing import List

from src.Participant import Participant

logger = logging.getLogger(__name__)

class DepartmentGeoClustering:

    def __init__(self, size_max: int = 36, random_state: int = 42):
        self.size_max = size_max
        self.random_state = random_state
        self.cluster_info = {}  # Store department info for each cluster

    def cluster_participants(self, participants: List[Participant]) -> dict:
        # Filter participants with valid geo_data
        valid_participants = [
            p for p in participants
            if p.geo_data is not None and hasattr(p.geo_data, 'x') and hasattr(p.geo_data, 'y')
        ]

        if not valid_participants:
            logger.warning("No participants with valid geo_data found")
            return {}

        # Group participants by department
        dept_groups = {}
        for participant in valid_participants:
            dept = participant.abteilung if participant.abteilung else "UNKNOWN"
            if dept not in dept_groups:
                dept_groups[dept] = []
            dept_groups[dept].append(participant)

        logger.info(f"Found {len(dept_groups)} unique departments")
        for dept, members in dept_groups.items():
            logger.info(f"  Department '{dept}': {len(members)} participants")

        # Process each department
        clusters = {}
        cluster_id = 0

        for dept, dept_participants in dept_groups.items():
            dept_size = len(dept_participants)

            if dept_size <= self.size_max:
                # Department fits in one cluster
                logger.info(
                    f"Department '{dept}' ({dept_size} participants) fits in single cluster"
                )
                for participant in dept_participants:
                    participant.cluster = cluster_id
                clusters[cluster_id] = dept_participants
                self.cluster_info[cluster_id] = {
                    'department': dept,
                    'sub_cluster': None
                }
                cluster_id += 1
            else:
                # Department needs to be split geographically
                n_sub_clusters = ceil(dept_size / self.size_max)
                logger.info(
                    f"Department '{dept}' ({dept_size} participants) needs to be split "
                    f"into {n_sub_clusters} geographic sub-clusters"
                )

                # Extract coordinates for this department
                coordinates = np.array([
                    [p.geo_data.x, p.geo_data.y] for p in dept_participants
                ])

                # Apply constrained k-means clustering
                size_min = max(1, dept_size // n_sub_clusters - 5)  # Allow some flexibility
                kmeans = KMeansConstrained(
                    n_clusters=n_sub_clusters,
                    size_min=size_min,
                    size_max=self.size_max,
                    random_state=self.random_state
                )

                try:
                    sub_labels = kmeans.fit_predict(coordinates)

                    # Assign cluster IDs and group participants
                    for participant, sub_label in zip(dept_participants, sub_labels):
                        participant.cluster = cluster_id + sub_label

                    # Create cluster groups
                    for sub_label in range(n_sub_clusters):
                        current_cluster_id = cluster_id + sub_label
                        sub_cluster_members = [
                            p for p in dept_participants
                            if p.cluster == current_cluster_id
                        ]
                        clusters[current_cluster_id] = sub_cluster_members
                        self.cluster_info[current_cluster_id] = {
                            'department': dept,
                            'sub_cluster': sub_label + 1
                        }
                        logger.info(
                            f"  Sub-cluster {sub_label + 1}/{n_sub_clusters}: "
                            f"{len(sub_cluster_members)} participants"
                        )

                    cluster_id += n_sub_clusters

                except Exception as e:
                    logger.error(
                        f"Failed to split department '{dept}' geographically: {e}. "
                        f"Falling back to single large cluster."
                    )
                    # Fallback: keep as single cluster even if oversized
                    for participant in dept_participants:
                        participant.cluster = cluster_id
                    clusters[cluster_id] = dept_participants
                    self.cluster_info[cluster_id] = {
                        'department': dept,
                        'sub_cluster': None
                    }
                    cluster_id += 1

        logger.info(
            f"Successfully created {len(clusters)} initial clusters from "
            f"{len(valid_participants)} participants across {len(dept_groups)} departments"
        )

        # Merge small clusters based on geographic proximity
        clusters = self._merge_small_clusters(clusters)

        return clusters

    def _merge_small_clusters(self, clusters: dict) -> dict:
        logger.info("\nMerging small clusters based on geographic proximity...")

        # Define threshold for what's considered a "small" cluster
        # We'll try to merge clusters that are less than half the max size
        merge_threshold = self.size_max // 2

        # Sort clusters by size (smallest first)
        sorted_cluster_ids = sorted(clusters.keys(), key=lambda cid: len(clusters[cid]))

        merged_count = 0
        clusters_to_remove = set()

        for cluster_id in sorted_cluster_ids:
            if cluster_id in clusters_to_remove:
                continue

            cluster = clusters[cluster_id]
            cluster_size = len(cluster)

            # Only consider merging if cluster is small
            if cluster_size >= merge_threshold:
                continue

            # Calculate centroid of this cluster
            coords = np.array([[p.geo_data.x, p.geo_data.y] for p in cluster])
            centroid = np.mean(coords, axis=0)

            # Find the nearest cluster that can accommodate these participants
            best_merge_candidate = None
            best_distance = float('inf')

            for other_cluster_id in sorted_cluster_ids:
                if other_cluster_id == cluster_id or other_cluster_id in clusters_to_remove:
                    continue

                other_cluster = clusters[other_cluster_id]
                other_size = len(other_cluster)

                # Check if merge would respect size constraint
                if cluster_size + other_size > self.size_max:
                    continue

                # Calculate distance between centroids
                other_coords = np.array([[p.geo_data.x, p.geo_data.y] for p in other_cluster])
                other_centroid = np.mean(other_coords, axis=0)
                distance = np.linalg.norm(centroid - other_centroid)

                if distance < best_distance:
                    best_distance = distance
                    best_merge_candidate = other_cluster_id

            # Perform merge if a suitable candidate was found
            if best_merge_candidate is not None:
                # Merge cluster into best_merge_candidate
                clusters[best_merge_candidate].extend(cluster)

                # Update cluster assignments for participants
                for participant in cluster:
                    participant.cluster = best_merge_candidate

                # Update cluster info to reflect multiple departments if needed
                current_info = self.cluster_info[best_merge_candidate]
                merging_info = self.cluster_info[cluster_id]

                if current_info['department'] != merging_info['department']:
                    # Mixed departments - flatten to list of department names
                    current_depts = current_info['department'] if isinstance(current_info['department'], list) else [current_info['department']]
                    merging_depts = merging_info['department'] if isinstance(merging_info['department'], list) else [merging_info['department']]

                    # Combine and deduplicate
                    all_depts = list(set(current_depts + merging_depts))
                    current_info['department'] = all_depts
                    current_info['sub_cluster'] = None  # No longer a simple sub-cluster

                clusters_to_remove.add(cluster_id)
                merged_count += 1

                logger.info(
                    f"Merged cluster {cluster_id} (size {cluster_size}) into "
                    f"cluster {best_merge_candidate} (new size: {len(clusters[best_merge_candidate])})"
                )

        # Remove merged clusters
        for cluster_id in clusters_to_remove:
            del clusters[cluster_id]
            del self.cluster_info[cluster_id]

        # Reassign cluster IDs to be sequential
        new_clusters = {}
        new_cluster_info = {}
        for new_id, old_id in enumerate(sorted(clusters.keys())):
            new_clusters[new_id] = clusters[old_id]
            new_cluster_info[new_id] = self.cluster_info[old_id]
            # Update participant cluster assignments
            for participant in new_clusters[new_id]:
                participant.cluster = new_id

        logger.info(
            f"Merged {merged_count} clusters. Final cluster count: {len(new_clusters)}"
        )

        self.cluster_info = new_cluster_info
        return new_clusters

    def get_cluster_statistics(self, clusters: dict) -> dict:
        stats = {}
        for cluster_id, members in clusters.items():
            coords = np.array([[p.geo_data.x, p.geo_data.y] for p in members])

            cluster_info = self.cluster_info.get(cluster_id, {})
            dept_name = cluster_info.get('department', 'UNKNOWN')
            sub_cluster = cluster_info.get('sub_cluster')

            # Format department name(s) for display
            if isinstance(dept_name, list):
                # Flatten any nested lists and convert all to strings
                flat_depts = []
                for d in dept_name:
                    if isinstance(d, list):
                        flat_depts.extend([str(x) for x in d])
                    else:
                        flat_depts.append(str(d))
                dept_display = f"Mixed ({len(flat_depts)} depts: {', '.join(flat_depts[:3])}{'...' if len(flat_depts) > 3 else ''})"
            else:
                dept_display = str(dept_name)

            stats[cluster_id] = {
                'size': len(members),
                'department': dept_display,
                'sub_cluster': sub_cluster,
                'mean_x': float(np.mean(coords[:, 0])),
                'mean_y': float(np.mean(coords[:, 1])),
                'std_x': float(np.std(coords[:, 0])),
                'std_y': float(np.std(coords[:, 1])),
                'min_x': float(np.min(coords[:, 0])),
                'max_x': float(np.max(coords[:, 0])),
                'min_y': float(np.min(coords[:, 1])),
                'max_y': float(np.max(coords[:, 1]))
            }

        return stats
