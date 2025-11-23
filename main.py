import os
import logging
import pandas as pd

from dotenv import load_dotenv

from src.interactWithLawmanger import LawmangerInteractor
from src.Participant import Participant
from src.Clustering import GeoClusterer
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

lawmangerInteractor = LawmangerInteractor(base_url=os.getenv("LAWMANAGER_BASE_URL"))

# Read csv
df = pd.read_csv('data/event_participation_export-dev.csv', sep=';')

# Display basic information about the dataset
logger.info("Dataset Information:")
logger.info(f"Total rows: {len(df)}")
logger.info(f"Total columns: {len(df.columns)}")
logger.info("\nColumn names:")
logger.info(df.columns.tolist())

participants = []

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

    geo_data=lawmangerInteractor.search_address(participant.get_full_address(), k=1)
    participant.geo_data = geo_data
    participants.append(participant)
    logger.info(f"Created participant: {participant}")

logger.info(f"\nTotal participants created: {len(participants)}")

# Cluster participants based on geo coordinates
clusterer = GeoClusterer(n_clusters=2)  # Adjust n_clusters as needed
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
