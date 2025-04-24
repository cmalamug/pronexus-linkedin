import requests

def get_from_backend(path: str) -> dict:
    response = requests.get(f"https://api.example.com/{path}")
    return response.json()

def update_in_backend(path: str, data: dict) -> dict:
    response = requests.put(f"https://api.example.com/{path}", json=data)
    return response.json()

def send_to_backend(path: str, data: dict) -> dict:
    response = requests.post(f"https://api.example.com/{path}", json=data)
    return response.json()
