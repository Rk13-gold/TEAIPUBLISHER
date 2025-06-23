import requests

def get_gumroad_products(access_token):
    url = "https://api.gumroad.com/v2/products"
    params = {"access_token": access_token}
    response = requests.get(url, params=params)
    return response.json().get("products", [])

def get_gumroad_sales(access_token):
    url = "https://api.gumroad.com/v2/sales"
    params = {"access_token": access_token}
    response = requests.get(url, params=params)
    return response.json().get("sales", [])