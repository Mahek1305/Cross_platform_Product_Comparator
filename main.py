# Import required modules and scraping functions
import streamlit as st
import os
import pandas as pd
import urllib.parse
from PIL import Image
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from scrap import (
    create_folder, amazon, myntra, flipkart, nykaa,
    scrap_amazon_images, scrap_flipkart_images, scrap_myntra_images, is_valid_image,
    get_best_match_for_platform
)

# ---------- Streamlit App Configuration ----------
st.set_page_config(layout="wide")  # Set layout to wide
st.title("Cross-platform Product Comparator")  # App Title

# ---------- Session State Initialization ----------
if "platform_choice" not in st.session_state:
    st.session_state.platform_choice = None  # Used to remember the platform selected

# ---------- Sidebar Platform Selection ----------
st.sidebar.markdown("<h3 style='font-size:24px;'>Choose Platform : </h3>", unsafe_allow_html=True)

# Platform selection radio button
platform_choice = st.sidebar.radio(
    "", 
    ["Amazon", "Myntra", "Flipkart", "Nykaa"]
)

# ---------- Input Fields ----------
product_url = st.text_input("Enter Product URL")      # User enters the actual product page URL
product_name = st.text_input("Enter Product Name ")   # User enters product name for searching on other platforms

# ---------- Button Action: On "Search" Click ----------
if st.button("🔍Search"):
    if not product_url or not product_name:
        st.warning("Please fill in all fields.")  # Validation
    else:
        with st.spinner("Running comparison logic..."):

            # ---------- Generate Search URLs ----------
            encoded_product_name = urllib.parse.quote_plus(product_name)
            amazon_url = f"https://www.amazon.in/s?k={encoded_product_name}"
            flipkart_url = f"https://www.flipkart.com/search?q={encoded_product_name}"
            myntra_url = f"https://www.myntra.com/{encoded_product_name.replace('+', '%20')}"

            results = []

            # ---------- Platform Scraper Wrappers ----------
            def run_amazon():
                return "Amazon", *scrap_amazon_images(amazon_url, "amazon_images")
            def run_flipkart():
                return "Flipkart", *scrap_flipkart_images(flipkart_url, "flipkart_images")
            def run_myntra():
                return "Myntra", *scrap_myntra_images(myntra_url, "myntra_images")

            # Dictionary of target platforms (excluding the chosen one)
            target_platforms = {
                "Amazon": ("amazon_images", run_amazon),
                "Flipkart": ("flipkart_images", run_flipkart),
                "Myntra": ("myntra_images", run_myntra)
            }

            # Exclude chosen platform from comparison targets
            if platform_choice == "Nykaa":
                target_platforms = {k: v for k, v in target_platforms.items()}
            elif platform_choice in target_platforms:
                del target_platforms[platform_choice]

            # ---------- Prepare Folders ----------
            base_price = None
            base_folder = platform_choice.upper()  # Base folder to store reference product images
            create_folder(base_folder)             # Reset folder for base platform images
            create_folder("amazon_images")
            create_folder("flipkart_images")
            create_folder("myntra_images")

            # ---------- Download Base Product Images ----------
            if platform_choice == "Amazon":
                base_price = amazon(product_url, base_folder)
            elif platform_choice == "Flipkart":
                base_price = flipkart(product_url, base_folder)
            elif platform_choice == "Myntra":
                base_price = myntra(product_url, base_folder)
            elif platform_choice == "Nykaa":
                base_price = nykaa(product_url, base_folder)

            # ---------- Display Layout ----------
            st.markdown("## 🔍 Best Matching Products")
            col_keys = list(target_platforms.keys())
            cols = st.columns(len(col_keys))  # Dynamically create columns per platform

            result_placeholders = {}  # For showing image and details
            progress_bars = {}        # For individual progress indicators

            # Create progress bar and placeholder for each column
            for idx, platform in enumerate(col_keys):
                with cols[idx]:
                    st.markdown(f"### {platform}")
                    progress_bars[platform] = st.progress(0)
                    result_placeholders[platform] = st.empty()

            # ---------- Run Comparison Logic in Background Threads ----------
            with ThreadPoolExecutor(max_workers=3) as executor:
                # Submit scraper jobs to executor
                future_to_platform = {
                    executor.submit(scraper_func): (platform, folder)
                    for platform, (folder, scraper_func) in target_platforms.items()
                }

                # Process each completed future
                for future in as_completed(future_to_platform):
                    platform, folder = future_to_platform[future]
                    try:
                        # Show 50% progress after scraping done
                        progress_bars[platform].progress(50)

                        platform_name, product_links, price_data = future.result()

                        # Perform image similarity comparison
                        result = get_best_match_for_platform(
                            base_folder, folder, product_links, platform_name, price_data
                        )

                        placeholder = result_placeholders[platform]
                        with placeholder.container():
                            if result.get("Product_Image") and os.path.exists(result["Product_Image"]):
                                st.markdown(f"**Similarity:** {result.get('Similarity')}%")
                                st.markdown(f"**Price:** {result.get('Price')}")

                                link = result.get('Product_Link', '#')
                                st.markdown(f"**Link:** [Product Link]({link})", unsafe_allow_html=True)

                                img = Image.open(result["Product_Image"]).resize((300, 300))
                                st.image(img)
                            else:
                                st.warning("No valid product image found.")

                        # Mark progress as done
                        progress_bars[platform].progress(100)

                    except Exception as e:
                        result_placeholders[platform].error(f" Error loading {platform}: {e}")
                        progress_bars[platform].progress(100)
