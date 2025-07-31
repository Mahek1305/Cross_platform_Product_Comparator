from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image , UnidentifiedImageError
from io import BytesIO
import requests
from bs4 import BeautifulSoup
import os
import imagehash
import time
import pandas as pd
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import pprint
import shutil
from tqdm import tqdm

# Creates (or resets) a folder for saving images.
# If the folder exists, all its contents are deleted.
# If not, the folder is created fresh.
def create_folder(folder_name):
    if os.path.exists(folder_name):
        for filename in os.listdir(folder_name):
            file_path = os.path.join(folder_name, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    else:
        os.makedirs(folder_name)

def amazon(url , folder):
# Scrapes product images and price from a specific Amazon product page.
# Uses Selenium to load the page and extract high-resolution images and price.
# Downloads images and saves them to the specified folder.
# Returns the product price as a string.
    
    options = Options()
    options.add_argument('--headless=new')  
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.get(url)

    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.a-button-thumbnail"))
    )

    spans = driver.find_elements(By.CSS_SELECTOR, "span.a-button-thumbnail")
    amazon_image_srcs = []

    for span in spans:
        try:
            img = span.find_element(By.TAG_NAME, "img")
            raw_src = img.get_attribute("src")
            large_src = re.sub(r"\._[A-Z]{2,4}\d+_", "._SL1500_", raw_src)

            amazon_image_srcs.append(large_src)
        except:
            continue

    try:
        price_whole = driver.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
        cost = f"₹{price_whole}"
    except Exception as e:
        cost = "Price not found"
        print(f"Error fetching price: {e}")

    print(f"Product Price: {cost}")

    driver.quit()

    for i, url in enumerate(amazon_image_srcs):
        try:
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            output_path = os.path.join(folder, f"amazon_image_{i+1}.png")
            img.save(output_path)
            print(f"Saved: {output_path}")
        except Exception as e:
            print(f" Error downloading image {url}: {e}")
            
    return cost

def flipkart(url, folder):
# Scrapes product images and price from a specific Flipkart product page.
# Uses BeautifulSoup to parse image URLs and download them in higher resolution.
# Saves the images to the given folder and returns the product price.

    options = Options()
    options.add_argument('--headless=new') 
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    driver.get(url)
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "_0DkuPH"))
    )

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    images = soup.find_all('img', {'class': '_0DkuPH'})

    for idx, img in enumerate(images, start=1):
        img_url = img.get('src') or img.get('data-src')
        if not img_url:
            continue

        if "/128/128/" in img_url:
            img_url = img_url.replace("/128/128/", "/832/832/")
        elif "/128/" in img_url:
            img_url = img_url.replace("/128/", "/832/")

        try:
            response = requests.get(img_url, timeout=10)
            if response.status_code == 200:
                img_path = os.path.join(folder, f"flipkart_image_{idx}.jpg")

                img_pil = Image.open(BytesIO(response.content)).convert("RGB")
                img_pil.save(img_path, format='JPEG')  

                print(f" Saved: {img_path}")
            else:
                print(f"Failed to download: {img_url}")
        except Exception as e:
            print(f"Error downloading image {idx}: {e}")

    try:
        price_tag = soup.find('div', class_='Nx9bqj CxhGGd') 
        price = price_tag.text.strip() if price_tag else "Price not found"
    except Exception as e:
        price = f"Error fetching price: {e}"

    driver.quit()
    return price


def myntra(url, folder):
# Scrapes images and price of a specific product from Myntra.
# Uses BeautifulSoup to extract image URLs from inline style attributes.
# Downloads images and saves them, and returns the product price.
    
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.get(url)
    time.sleep(5)  

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    image_divs = soup.find_all("div", class_="image-grid-image")
    image_urls = []

    for div in image_divs:
        style_attr = div.get("style", "")
        match = re.search(r'url\("(.+?)"\)', style_attr)
        if match:
            image_urls.append(match.group(1))

    for url in image_urls:
        print(url)

    for i, url in enumerate(image_urls):
        img_data = requests.get(url).content
        with open(os.path.join(folder, f"myntra_image_{i+1}.jpg"), 'wb') as handler:
            handler.write(img_data)

    print("Images downloaded successfully.")

    try:
        price = driver.find_element(By.CLASS_NAME, "pdp-price").text
        print(f"Product Price: {price}")

    except Exception as e:
        print("Price not found:", e)
        
    driver.quit()
    
    return price

def nykaa(url, folder):
# Scrapes product images and price from a specific Nykaa product page.
# Finds image tags with 'product-thumbnail' alt attribute.
# Downloads and saves the images, and returns the product price.
   
    options = Options()
    options.add_argument('--headless=new')  
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    driver.get(url)
    time.sleep(5)
    
    image_tags = driver.find_elements(By.XPATH, "//img[@alt='product-thumbnail']")

    for idx, img_tag in enumerate(image_tags, start=1):
        img_url = img_tag.get_attribute('src')
        if img_url:
            print(f"Nykaa Image {idx}: {img_url}")
            response = requests.get(img_url)
            if response.status_code == 200:
                with open(os.path.join(folder, f"image_{idx}.png"), 'wb') as f:
                    f.write(response.content)
            
    try:
        price_element = driver.find_element(By.CLASS_NAME, "css-1jczs19")
        product_price = price_element.text
        print(f"Product Price: {product_price}")

    except Exception as e:
        print("Price not found:", e)

    driver.quit()
    print("\n✅ Nykaa images downloaded.\n")
    
    return product_price

def scrap_amazon_images(searchUrl, folder):
# Performs a search on Amazon and collects links for up to 40 product pages.
# For each product:
#   - Visits the page
#   - Extracts and downloads high-resolution images
#   - Retrieves and stores the product price and link
# Returns:
#   - A dictionary mapping image filenames to product links
#   - A list of product data dictionaries (link and price)

    def get_driver():
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    driver = get_driver()
    product_data = []
    product_image_map = {}

    try:
        driver.get(searchUrl)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.a-link-normal.s-no-outline"))
        )
        link_elements = driver.find_elements(By.CSS_SELECTOR, "a.a-link-normal.s-no-outline")
        href_links = [link.get_attribute('href') for link in link_elements if link.get_attribute('href')]
        print(f"Total product links found: {len(href_links)}")
    except Exception as e:
        print("Error collecting product links:", e)
        driver.quit()
        return {}

    for idx, link in enumerate(href_links[:40]):  
        print(f"\nVisiting Product {idx+1}: {link}")
        try:
            driver.get(link)
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.a-button-thumbnail"))
            )
        except Exception as e:
            print(f"Error loading product page: {e}")
            continue

        try:
            spans = driver.find_elements(By.CSS_SELECTOR, "span.a-button-thumbnail")
            amazon_image_srcs = []
            for span in spans:
                try:
                    img = span.find_element(By.TAG_NAME, "img")
                    raw_src = img.get_attribute("src")
                    large_src = re.sub(r"\._[A-Z]{2,4}\d+_", "._SL1500_", raw_src)
                    amazon_image_srcs.append(large_src)
                except:
                    continue

            for i, url in enumerate(amazon_image_srcs):
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        img = Image.open(BytesIO(response.content))
                        image_filename = f"product_{idx+1}_image_{i+1}.png"
                        output_path = os.path.join(folder, image_filename)
                        img.save(output_path)
                        print(f"Saved: {output_path}")
                        product_image_map[image_filename] = link
                except Exception as e:
                    print(f"Error downloading image {url}: {e}")
        except:
            print("No thumbnails found, skipping.")
            continue

        try:
            price_whole = driver.find_element(By.CSS_SELECTOR, "span.a-price-whole").text
            cost = f"₹{price_whole}"
        except:
            cost = "Price not found"

        product_data.append({
            "Product Link": link,
            "Price": cost
        })
        print(f"Product Price: {cost}")
        
        print("\n Stored Amazon product links and prices in memory")
    driver.quit()
    return product_image_map, product_data

def scrap_flipkart_images(searchUrl, folder):
# Performs a search on Flipkart and extracts up to 40 product links.
# For each product:
#   - Opens the product page
#   - Downloads high-res images (replacing low-res URLs)
#   - Extracts and stores the product price
# Returns:
#   - A dictionary mapping index to product links
#   - A list of product data dictionaries (link and price)
    
    options = Options()
    options.add_argument('--headless=new')  
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    driver.get(searchUrl)
    driver.implicitly_wait(5)

    try:
        close_button = driver.find_element(By.XPATH, "//button[contains(text(),'✕')]")
        close_button.click()
    except:
        pass

    possible_classes = ["VJA3rP", "CGtC98", "_1fQZEK", "wjcEIp", "rPDeLR"]
    anchor_tags = []

    for class_name in possible_classes:
        anchor_tags.extend(driver.find_elements(By.CLASS_NAME, class_name))

    product_links = [tag.get_attribute('href') for tag in anchor_tags if tag.get_attribute('href')]

    print(f"\nTotal product links found: {len(product_links)}")

    product_data = []
    product_link_map = {}
    
    for idx, link in enumerate(product_links[:40]):
        product_link_map[idx] = link
        product_number = idx + 1
        print(f"\nVisiting Product {product_number}: {link}")

        driver.get(link)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "_0DkuPH"))
        )

        try:
            close_button = driver.find_element(By.XPATH, "//button[contains(text(),'✕')]")
            close_button.click()
        except:
            pass

        time.sleep(2)

        images = driver.find_elements(By.CLASS_NAME, "_0DkuPH")
        product_images = [img.get_attribute("src") for img in images if img.get_attribute("src")]

        if not product_images:
            print("No images found for this product.")
        else:
            for img_idx, image_src in enumerate(product_images):
                try:
                    if "/128/128/" in image_src:
                        image_src = image_src.replace("/128/128/", "/832/832/")
                    elif "/128/" in image_src:
                        image_src = image_src.replace("/128/", "/832/")

                    print(f"Downloading image: {image_src}")
                    img_response = requests.get(image_src)
                    img_pil = Image.open(BytesIO(img_response.content)).convert("RGB")
                    
                    filename = os.path.join(folder, f"product_{product_number}_image_{img_idx+1}.jpg")
                    img_pil.save(filename, format='JPEG')
                    print(f" Saved as {filename}")
                except Exception as e:
                    print(f" Failed to download image: {e}")

        try:
            price_tag = driver.find_element(By.CLASS_NAME, 'Nx9bqj')  # main price class
            price = price_tag.text
        except:
            price = "Price not found"

        print(f"Product Price: {price}")

        product_data.append({
            "Product Link": link,
            "Price": price
        })

    driver.quit()
    return product_link_map, product_data

def scrap_myntra_images(searchUrl, folder):
# Performs a search on Myntra and collects product links from the search results.
# For each product:
#   - Opens the product page
#   - Extracts and downloads all image URLs from inline styles
#   - Extracts product price
# Returns:
#   - A dictionary mapping image filenames to product links
#   - A list of product data dictionaries (link and price)

    options = Options()
    options.add_argument('--headless=new') 
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    driver.get(searchUrl)
    time.sleep(5)

    for _ in range(10):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    product_elements = driver.find_elements(By.CSS_SELECTOR, "ul.results-base li.product-base a")
    product_links = list(set([elem.get_attribute("href") for elem in product_elements if elem.get_attribute("href")]))

    print(f"Found {len(product_links)} product links.")

    product_data = []
    image_product_map = {}

    for idx, link in enumerate(product_links):  
        print(f"\nProcessing product {idx+1}: {link}")
        driver.get(link)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        image_divs = soup.find_all("div", class_="image-grid-image")
        image_urls = []
        for div in image_divs:
            style_attr = div.get("style", "")
            match = re.search(r'url\("(.+?)"\)', style_attr)
            if match:
                image_url = match.group(1)
                if image_url not in image_urls:
                    image_urls.append(image_url)

        print(f"Found {len(image_urls)} images.")

        for i, img_url in enumerate(image_urls):
            try:
                response = requests.get(img_url, timeout=10)
                if response.status_code == 200:
                    image_filename = f"product_{idx+1}_image_{i+1}.png"
                    image_path = os.path.join(folder, image_filename)
                    with open(image_path, 'wb') as f:
                        f.write(response.content)
                    print(f"Saved image: {image_filename}")
                    image_product_map[image_filename] = link
                else:
                    print(f"Failed to fetch image: {img_url} (Status code: {response.status_code})")
            except Exception as e:
                print(f"Failed to download image {img_url}: {e}")

        print(f"Downloaded {len(image_urls)} images for product {idx+1}.")

        try:
            price_element = driver.find_element(By.CLASS_NAME, "pdp-price")
            price = price_element.text
            print(f"Product Price: {price}")
        except Exception as e:
            price = "Price not found"
            print(f"Error fetching price: {e}")

        product_data.append({
            "Product Link": link,
            "Price": price
        })
        
        print("\n Stored Myntra product links and prices in memory")

    driver.quit()
    return image_product_map, product_data

# IMAGE COMPARISON 

def is_valid_image(path):
# Checks if an image file is valid and not corrupted.
# Used to filter out bad files before comparison.
# Returns True if the image can be opened and verified.
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except (UnidentifiedImageError, IOError, FileNotFoundError):
        return False

def get_best_match_for_platform(base_folder, platform_folder, product_links, platform_name, price_df=None):
# Compares a base image folder (Amazon) with a given platform folder (e.g., Flipkart).
# Uses perceptual hashing to compare image similarity.
# Returns the best matching image across all platform images:
#   - Includes similarity percentage
#   - Corresponding product link
#   - Price (if provided via price_df)
#   - Image path
# Attempts to retrieve the link from a filename map or fallback to product index.

    TARGET_SIZE = (512, 512)
    MAX_HASH_DIFF = 64

    best_match = {
        "Platform": platform_name,
        "Product_Image": None,
        "Product_Link": None,
        "Similarity": 0,
        "Price": "N/A"
    }

    base_images = [
        f for f in os.listdir(base_folder)
        if f.endswith(('.jpg', '.png')) and is_valid_image(os.path.join(base_folder, f))
    ]
    compare_images = [
        f for f in os.listdir(platform_folder)
        if f.endswith(('.jpg', '.png')) and is_valid_image(os.path.join(platform_folder, f))
    ]

    for base_img in base_images:
        base_path = os.path.join(base_folder, base_img)
        try:
            img1 = Image.open(base_path).convert("RGB").resize(TARGET_SIZE)
        except Exception as e:
            print(f"[WARNING] Skipping base image '{base_path}': {e}")
            continue

        for comp_img in compare_images:
            comp_path = os.path.join(platform_folder, comp_img)
            try:
                img2 = Image.open(comp_path).convert("RGB").resize(TARGET_SIZE)
            except Exception as e:
                print(f"[WARNING] Skipping comparison image '{comp_path}': {e}")
                continue

            try:
                hash1 = imagehash.phash(img1)
                hash2 = imagehash.phash(img2)
                diff = abs(hash1 - hash2)
                similarity = round((1 - diff / MAX_HASH_DIFF) * 100, 2)
            except Exception as e:
                print(f"[ERROR] Failed to compare images: {e}")
                continue

            if similarity > best_match["Similarity"]:
                link = product_links.get(comp_img)

                if not link:
                    match = re.search(r'product_(\d+)_image', comp_img)
                    if match:
                        index = int(match.group(1)) - 1
                        link = product_links.get(index)

                price = "N/A"
                if price_df is not None and link:
                    for row in price_df:
                        if row.get("Product Link") == link:
                            price = row.get("Price", "N/A")
                            break

                best_match.update({
                    "Product_Image": comp_path,
                    "Product_Link": link if link else "Link not found",
                    "Similarity": similarity,
                    "Price": price
                })

    return best_match
