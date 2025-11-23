import pandas as pd
from math import nan

class Participant:
    def __init__(self, vorname: str, nachname: str, pfadiname: str, strasse: str, hausnummer: int, postfach: int,
                 plz: int, ort: str, land: str, hauptebene: str, funktion_im_jamboree: str, abteilung: str, kantonalverband: str):
        self.vorname = vorname
        self.nachname = nachname
        self.pfadiname = pfadiname if pd.notna(pfadiname) else ""
        self.strasse = strasse
        self.hausnummer = hausnummer
        self.postfach = postfach if pd.notna(postfach) else None
        self.plz = plz
        self.ort = ort
        self.land = land
        self.hauptebene = hauptebene
        self.funktion_im_jamboree = funktion_im_jamboree
        self.abteilung = abteilung
        self.kantonalverband = kantonalverband

        # Optional geo data to be filled later
        self.geo_data = None

        # Optional cluster assignment
        self.cluster = None

    def __repr__(self):
        return (f"Participant(vorname='{self.vorname}', nachname='{self.nachname}', "
                f"pfadiname='{self.pfadiname}', hauptebene='{self.hauptebene}')")

    def __str__(self):
        return f"{self.vorname} {self.nachname} ({self.pfadiname}) - {self.hauptebene}"

    def get_full_address(self):
        address_parts = []

        # Street and house number
        if self.strasse:
            street_line = self.strasse
            if self.hausnummer:
                street_line += f" {self.hausnummer}"
            address_parts.append(street_line)

        # P.O. Box
        if self.postfach:
            address_parts.append(f"Postfach {self.postfach}")

        # ZIP and city
        if self.plz or self.ort:
            city_line = f"{self.plz} {self.ort}".strip()
            address_parts.append(city_line)

        return ", ".join(address_parts)

    def to_dict(self):
        """Convert participant to dictionary."""
        return {
            'vorname': self.vorname,
            'nachname': self.nachname,
            'pfadiname': self.pfadiname,
            'strasse': self.strasse,
            'hausnummer': self.hausnummer,
            'postfach': self.postfach,
            'plz': self.plz,
            'ort': self.ort,
            'land': self.land,
            'hauptebene': self.hauptebene,
            'funktion_im_jamboree': self.funktion_im_jamboree,
            'abteilung': self.abteilung,
            'kantonalverband': self.kantonalverband
        }
