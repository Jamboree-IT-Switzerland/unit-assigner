import requests

from .Geodata import Geodata

class LawmangerInteractor:
    def __init__(self, base_url: str):
        self.BASE_URL = base_url

    def search_address(self, search_query: str, k=1) -> Geodata | None:
        params = {"search": search_query}
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        response = response.json()

        if response["response"] == "success":
            results = response.get("addresses", [])
            if len(results) >= k:
                result = results[k - 1]
                return Geodata(
                    lat=result.get("lat"),
                    lon=result.get("lon"),
                    x=result.get("x"),
                    y=result.get("y")
                )
            else:
                return None
        else:
            raise Exception(f"Error from Lawmanger API: {response.get('message', 'Unknown error')}")
