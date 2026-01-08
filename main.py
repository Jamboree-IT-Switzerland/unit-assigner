import os
import logging
import pickle
import pandas as pd

from dotenv import load_dotenv

from src.interactWithLawmanger import LawmangerInteractor
from src.Participant import Participant
from src.Clustering.GeoClusteringConstrained import GeoClusteringConstrained
from src.Clustering.GeoClustering import GeoClustering
from src.Clustering.DepartmentGeoClustering import DepartmentGeoClustering
from src.Visualizer import ParticipantVisualizer

logging.basicConfig(
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='UnitAssigner.log',
    filemode='w',
    encoding='utf-8',
    format='%(asctime)s %(levelname)-8s %(message)s'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s'))

logger = logging.getLogger()
logger.addHandler(console)
logger.setLevel(logging.INFO)

load_dotenv()

CONSTRAINT_ENABLED = os.getenv("CONSTRAINT_ENABLED", "False").lower() in ("true", "1", "t")
IS_DEV = os.getenv("IS_DEV", "False").lower() in ("true", "1", "t")
RELOAD_DATA = os.getenv("RELOAD_DATA", "False").lower() in ("true", "1", "t")
LAWMANAGER_BASE_URL = os.getenv("LAWMANAGER_BASE_URL")

EXPORT_PKL_PATH = './export/participants_with_geo.pkl'
lawmangerInteractor = LawmangerInteractor(base_url=LAWMANAGER_BASE_URL)

# Read csv
if IS_DEV:
    logger.info("Loading development dataset...")
    df = pd.read_csv('./data/event_participation_export-dev.csv', sep=';', na_values=[''])
else:
    logger.info("Loading production dataset...")
    df = pd.read_csv('./data/event_participation_export.csv', sep=';', na_values=[''])

# Display basic information about the dataset
logger.info("Dataset Information:")
logger.info(f"Total rows: {len(df)}")
logger.info(f"Total columns: {len(df.columns)}")
logger.info("\nColumn names:")
logger.info(df.columns.tolist())

participants = []
participants_with_no_geo = []

if not RELOAD_DATA and os.path.exists(EXPORT_PKL_PATH):
    logging.info("Attempting to load participants from existing pickle file...")
    try:
        with open(EXPORT_PKL_PATH, 'rb') as f:
            participants = pickle.load(f)
            logger.info(f"Loaded {len(participants)} participants from pickle file.")
    except FileNotFoundError:
        logger.info("Pickle file not found. Proceeding to create participants from CSV.")
else:
    logger.info("RELOAD_DATA is enabled. Proceeding to create participants from CSV.")
    for index, row in df.iterrows():
        participant = Participant(
            vorname=row['Vorname'],
            nachname=row['Nachname'],
            pfadiname=row['Pfadiname'],
            strasse=row['Strasse'],
            hausnummer=row['Hausnummer'],
            postfach=row['Postfach'],
            plz=row['PLZ'],
            ort=row['Ort'],
            land=row['Land'],
            hauptebene=row['Hauptebene'],
            funktion_im_jamboree=row['3) In welcher Funktion meld...'],
            abteilung=row['5) Aus welcher Pfadiabteilu...'],
            kantonalverband=row['9) Mein Kantonalverband / M...'],
        )

        full_address = participant.get_full_address()

        if not full_address:
            logger.warning(f"Participant {participant.get_full_name()} does not have a valid address. Skipping geocoding.")
            participants_with_no_geo.append(participant)
            continue

        geo_data=lawmangerInteractor.search_address(full_address, k=1)
        participant.geo_data = geo_data

        if not participant.has_valid_geo():
            logger.warning(f"Participant {participant.get_full_name()} does not have valid geo coordinates. Address: {participant.get_full_address()}")
            participants_with_no_geo.append(participant)
        else:
            participants.append(participant)
            logger.info(f"Created participant: {participant}")

    # dump to exported file pkl
    logger.info(f"\nSaving participants to pickle file at {EXPORT_PKL_PATH}...")
    with open(EXPORT_PKL_PATH, 'wb') as f:
        pickle.dump(participants, f)

logger.info(f"\nTotal participants created: {len(participants)}")

# Filter based on participant function
participants = [p for p in participants if p.is_participant()]

# Cluster participants by department first, then by geography
logger.info("\nClustering participants by department and geographic location...")
SIZE_MAX = 36
logger.info(f"Max cluster size: {SIZE_MAX}")
clusterer = DepartmentGeoClustering(size_max=SIZE_MAX)
clusters = clusterer.cluster_participants(participants)

# Display cluster statistics
stats = clusterer.get_cluster_statistics(clusters)
logger.info("\nCluster Statistics:")
for cluster_id, cluster_stats in stats.items():
    dept_name = cluster_stats['department']
    sub_cluster = cluster_stats['sub_cluster']
    cluster_label = f"Cluster {cluster_id} - {dept_name}"
    if sub_cluster:
        cluster_label += f" (Sub-cluster {sub_cluster})"

    logger.info(f"{cluster_label}:")
    logger.info(f"  Size: {cluster_stats['size']}")
    logger.info(f"  Geographic Center: ({cluster_stats['mean_x']:.2f}, {cluster_stats['mean_y']:.2f})")
    logger.info(f"  Geographic Spread: (σx={cluster_stats['std_x']:.2f}, σy={cluster_stats['std_y']:.2f})")

# Export clusters to CSV
logger.info("\nExporting clusters to CSV...")
csv_output_path = './export/clusters_export.csv'
csv_separator = ';'
with open(csv_output_path, 'w', encoding='utf-8') as f:
    # Write header
    header = csv_separator.join(["Cluster", "Vorname", "Nachname", "Pfadiname", "Strasse", "Hausnummer", "PLZ", "Ort", "Abteilung", "Kantonalverband"]) + "\n"
    f.write(header)

    # Write each participant with their cluster assignment
    for cluster_id, cluster_participants in clusters.items():
        for participant in cluster_participants:
            f.write(f"{cluster_id};{participant.to_csv(separator=csv_separator)}\n")

logger.info(f"Clusters exported to {csv_output_path}")

# Visualize participants on map
logger.info("\nGenerating visualizations...")
visualizer = ParticipantVisualizer()

# Create interactive map
visualizer.create_interactive_map(participants, clusters, output_file='./export/participant_map.html')
