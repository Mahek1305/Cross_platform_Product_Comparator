# 🛍️ Cross-Platform Product Comparator

# 📖 About

**Cross-Platform Product Comparator** is a **Streamlit-based tool** that compares **product images and prices** across major Indian e-commerce platforms — **Amazon**, **Flipkart**, **Myntra**, and **Nykaa**.

The app:

* Scrapes product data (titles, images, and prices) using **Selenium** and **BeautifulSoup**
* Compares **image similarity** using **Perceptual Hashing (pHash)**
* Displays **visually similar products** from other platforms, along with **price differences**, in a clean Streamlit interface

It helps users **find the same or similar products at better prices** across different platforms.

# ⚙️ Requirements
**Python Libraries:**
streamlit
selenium
webdriver-manager
beautifulsoup4
pillow
imagehash
pandas
requests
tqdm

# 🖥️ System Requirements
* **Python 3.10+**
* **Google Chrome** browser installed
* **Stable internet connection** (for live scraping)
* **Sufficient RAM/CPU** (multi-threaded scraping can be resource-intensive)

# 🧠 How It Works
1. **User Input:** Enter a product keyword (e.g., *“Nike shoes”*)
2. **Scraping:** The app scrapes product details from Amazon, Flipkart, Myntra, and Nykaa
3. **Image Hashing:** Computes **perceptual hashes (pHash)** of product images
4. **Comparison:** Finds visually similar items across all platforms
5. **Display:** Shows side-by-side comparisons with images, links, and prices


## 🖼️ Output



# 🚀 Future Improvements
* Add **more platforms** (Ajio, TataCliq)
* Implement **faster async scraping** (Playwright or asyncio)
* Add **search history and filtering**
* Deploy as a **web service** using Streamlit Cloud or AWS

 🧑‍💻 Author
Mahek Aggarwal
💼 Student & Developer | AI/ML & Automation Enthusiast
📧 Contact: mahekaggarwal05@gmail.com
