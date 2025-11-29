import os
import logging
import pickle
import pandas as pd

from dotenv import load_dotenv

from src.interactWithLawmanger import LawmangerInteractor
from src.Participant import Participant
from src.Clustering.GeoClusteringConstrained import GeoClusteringConstrained
from src.Clustering.GeoClustering import GeoClustering
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
            funktion_im_jamboree=row['Funktion_im_Jamboree'],
            abteilung=row['Abteilung'],
            kantonalverband=row['Kantonalverband'],
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

# Cluster participants based on geo coordinates
N_CLUSTERS = max(len(participants) // 36, 1)

# Filter based on participant function
participants = [p for p in participants if p.is_participant()]

if (CONSTRAINT_ENABLED):
    logger.info("\nClustering participants with constraints...")

    SIZE_MAX = min(36, len(participants))
    logger.info(f"Number of clusters: {N_CLUSTERS}, Max cluster size: {SIZE_MAX}")
    clusterer = GeoClusteringConstrained(n_clusters=N_CLUSTERS, size_min=None, size_max=SIZE_MAX)  # Adjust n_clusters, size_min, size_max as needed
else:
    logger.info("\nClustering participants without constraints...")
    logger.info(f"Number of clusters: {N_CLUSTERS}")
    clusterer = GeoClustering(n_clusters=N_CLUSTERS)  # Adjust n_clusters as needed
clusters = clusterer.cluster_participants(participants)

# Display cluster statistics
stats = clusterer.get_cluster_statistics(clusters)
logger.info("\nCluster Statistics:")
for cluster_id, cluster_stats in stats.items():
    logger.info(f"Cluster {cluster_id}:")
    logger.info(f"  Size: {cluster_stats['size']}")
    logger.info(f"  Center: ({cluster_stats['center'][0]:.2f}, {cluster_stats['center'][1]:.2f})")
    logger.info(f"  Mean: ({cluster_stats['mean_x']:.2f}, {cluster_stats['mean_y']:.2f})")
    logger.info(f"  Std Dev: ({cluster_stats['std_x']:.2f}, {cluster_stats['std_y']:.2f})")

# Visualize participants on map
logger.info("\nGenerating visualizations...")
visualizer = ParticipantVisualizer()

# Create interactive map
visualizer.create_interactive_map(participants, clusters, output_file='./export/participant_map.html')
