import pandas as pd
from math import nan

from .Geodata import Geodata

class Participant:
    def __init__(self, vorname: str, nachname: str, pfadiname: str, strasse: str, hausnummer: int, postfach: int,
                 plz: int, ort: str, land: str, hauptebene: str, funktion_im_jamboree: str, abteilung: str, kantonalverband: str):
        self.vorname = vorname if pd.notna(vorname) else ""
        self.nachname = nachname if pd.notna(nachname) else ""
        self.pfadiname = pfadiname if pd.notna(pfadiname) else ""
        self.strasse = strasse if pd.notna(strasse) else None
        self.hausnummer = hausnummer if pd.notna(hausnummer) else None
        self.postfach = postfach if pd.notna(postfach) else None
        self.plz = plz if pd.notna(plz) else None
        self.ort = ort if pd.notna(ort) else ""
        self.land = land if pd.notna(land) else ""
        self.hauptebene = hauptebene if pd.notna(hauptebene) else ""
        self.funktion_im_jamboree = funktion_im_jamboree if pd.notna(funktion_im_jamboree) else ""
        self.abteilung = abteilung if pd.notna(abteilung) else ""
        self.kantonalverband = kantonalverband if pd.notna(kantonalverband) else ""

        # Optional geo data to be filled later
        self.geo_data: Geodata | None = None

        # Optional cluster assignment
        self.cluster = None

    def __repr__(self):
        return (f"Participant(vorname='{self.vorname}', nachname='{self.nachname}', "
                f"pfadiname='{self.pfadiname}', hauptebene='{self.hauptebene}')")

    def __str__(self):
        return f"{self.vorname} {self.nachname} ({self.pfadiname}) - {self.hauptebene}"

    def get_full_name(self):
        return f"{self.vorname} {self.nachname} - {self.pfadiname}"

    def get_full_address(self):
        address_parts = []

        # Street and house number
        if self.strasse:
            street_line = self.strasse
            if self.hausnummer:
                street_line += f" {self.hausnummer}"
            address_parts.append(street_line)

        # P.O. Box
        #if self.postfach:
        #    address_parts.append(f"Postfach {self.postfach}")

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

    def has_valid_geo(self):
        return self.geo_data is not None and self.geo_data.lat is not None and self.geo_data.lon is not None

    def is_participant(self):
        return bool(self.funktion_im_jamboree.strip() == "Teilnehmer:in / participant·e / partecipante")

    def is_leader(self):
        return bool(self.funktion_im_jamboree.strip() == "UL (Unit Lead)")
