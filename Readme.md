# Unit Assigner

## Goals

## Installation

1. **Clone the repository**:
```bash
git clone https://github.com/Jamboree-IT-Switzerland/unit-assigner.git
cd unit-assigner
```

2. **Create a virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure the application**:
```bash
# Edit .env with your Midata API token and other settings
cp .env.example .env
```

## Development
## Run the unit assigner

```bash
python src\main.py
```


## Data
### Input
- event_participation_export.csv: Export from Midata with participant data.

# References
- [https://rsandstroem.github.io/tag/folium.html](https://rsandstroem.github.io/tag/folium.html)
