import requests

class FHIRClient:
    """
    Custom HTTP Client for raw FHIR interactions.
    Useful for debugging or specific operations not supported by wrappers.
    """
    def __init__(self, base_url):
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/fhir+json',
            'Accept': 'application/fhir+json'
        }

    def get_raw_resource(self, resource_type, params=None):
        """
        Executes a raw GET request.
        Returns: Python Dictionary (Raw JSON data).
        """
        url = f"{self.base_url}/{resource_type}"
        try:
            print(f"📡 [RAW CLIENT] Request: GET {url} | Params: {params}")
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ [RAW CLIENT] Network Error: {e}")
            return None

    def post_raw_resource(self, resource_type, resource_json):
        """
        Executes a raw POST request to create a resource.
        """
        url = f"{self.base_url}/{resource_type}"
        try:
            print(f"📡 [RAW CLIENT] Request: POST {url}")
            response = requests.post(url, headers=self.headers, json=resource_json)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ [RAW CLIENT] Creation Error: {e}")
            return None