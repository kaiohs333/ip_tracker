# ip_tracker/utils.py
import requests

def get_ip_info(ip_address: str) -> dict:
    """Obtém informações geográficas de um endereço IP usando uma API externa."""
    try:
        # Você estava pedindo 'city', mas a lógica só usava 'country'. 
        # Pedi apenas 'country' para ser mais eficiente.
        response = requests.get(f"http://ip-api.com/json/{ip_address}?fields=country")
        response.raise_for_status() # Lança exceção para erros HTTP
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Erro ao consultar API de IP: {e}")
        # Retorna um dict que o .get('country') do serviço tratará como None
        return {"status": "fail"}