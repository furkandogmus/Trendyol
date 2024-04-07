import time
import threading
from flask import Flask, request
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from sendemail import send_email
import os
from dotenv import load_dotenv
import hashlib
from jinja2 import Environment, FileSystemLoader

app = Flask(__name__)
CORS(app)
load_dotenv()
sender_email = os.getenv("SENDER_EMAIL")
app_password = os.getenv("APP_PASSWORD")

# Jinja2 environment setup
env = Environment(loader=FileSystemLoader('.'))

def load_tracked_products():
    tracked_products = set()
    with open('tracked_products.txt', 'r') as file:
        for line in file:
            tracked_products.add(line.strip())
    return tracked_products

def save_tracked_product(hash_code):
    with open('tracked_products.txt', 'a') as file:
        file.write(hash_code + '\n')

def generate_hash(email, product_name, current_price):
    hash_object = hashlib.md5()
    hash_object.update((email + product_name + str(current_price)).encode())
    return hash_object.hexdigest()

def check_price(url, target_price, user_email):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    products = soup.find_all("div", class_="p-card-wrppr")
    new_products = []
    tracked_products = load_tracked_products()

    for product in products:
        product_name = product.find("span", class_="prdct-desc-cntnr-name").get_text().strip()
        price_str = product.find("div", class_="prc-box-dscntd").get_text()
     
        current_price = float(price_str.replace(' TL', '').replace('.', '').replace(',', '.'))
        hash_code = generate_hash(user_email, product_name, current_price)

        if hash_code not in tracked_products and current_price < target_price:
            product_url = "https://www.trendyol.com" + product.find("a")["href"]
            new_products.append({"name": product_name, "price": current_price, "url": product_url})
            save_tracked_product(hash_code)

    if new_products:
        subject = "Yeni Ürünler Geldi!!!"
        email_body = render_email_template(new_products)
        send_email(sender_email, user_email, app_password, subject, email_body)
        return "Bildirim gönderildi!"
    else:
        return "Fiyat belirlenen seviyenin altında değil."

def render_email_template(products):
    template = env.get_template('email_template.html')
    return template.render(products=products)

def read_customers_info_from_file(file_path):
    customers_info = []
    with open(file_path, 'r') as file:
        for line in file:
            url, target_price, user_email = line.strip().split(';')
            customers_info.append((url, int(target_price), user_email))
    return customers_info

@app.route('/add_customer', methods=['POST'])
def add_customer():
    data = request.json
    if 'url' in data and 'target_price' in data and 'user_email' in data:
        url = data['url']
        target_price = data['target_price']
        user_email = data['user_email']
        check_price(url, int(target_price), user_email)
        with open('customers.txt', 'a') as file:
            file.write(f"{url};{target_price};{user_email}\n")
        
        return "Customer added successfully!"
    else:
        return "Missing required fields", 400

def run_price_check():
    
    customers = read_customers_info_from_file("customers.txt")
    for customer in customers:
        url, target_price, user_email = customer
        check_price(url, target_price, user_email)
    
# Start the price check function in a separate thread
price_check_thread = threading.Thread(target=run_price_check)
price_check_thread.daemon = True
price_check_thread.start()

# Define the route to trigger the price check manually if needed
@app.route('/check_prices')
def trigger_price_check():
    run_price_check()  # Trigger the price check immediately
    return "Price check completed!"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)