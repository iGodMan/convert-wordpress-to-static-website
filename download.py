import os
import subprocess
import shutil
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# Full path to the wget executable
wget_path = r'tool\wget.exe'

# Function to download assets using wget
def download_assets(url):
    # Download assets using wget
    subprocess.run([
        wget_path,
        "--recursive",
        "--level=1",
        "--page-requisites",
        "--convert-links",
        "--no-parent",
        url
    ])

# Function to parse HTML and download referenced assets
def parse_html_and_download_assets(html_file, base_url):
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Parse HTML content
    soup = BeautifulSoup(html_content, "html.parser")

    # Find all tags that reference assets (like img, script, link)
    asset_tags = soup.find_all(["img", "script", "link"])

    # Download each referenced asset into the root domain folder
    for tag in asset_tags:
        if tag.name == "img":
            attribute = "src"
        elif tag.name == "script" or tag.name == "link":
            attribute = "src" if tag.name == "script" else "href"

        asset_url = tag.get(attribute)
        if asset_url:
            asset_url = urljoin(base_url, asset_url)
            download_asset(asset_url, base_url)

            # Remove the root domain from the asset URL
            relative_path = urlparse(asset_url).path.replace(urlparse(base_url).path, "").lstrip("/")

            # Update the attribute value in the HTML content
            tag[attribute] = relative_path

    # Write the modified HTML content back to the file
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(str(soup))

# Function to download an individual asset
def download_asset(url, base_url):
    try:
        # Get the file path of the asset relative to the root domain
        asset_relative_path = urlparse(url).path.lstrip("/")
        # Construct the absolute path where the asset should be saved
        save_path = os.path.join(base_url, asset_relative_path)
        # Ensure the directory structure exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Download the asset
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            print(f"Downloaded: {url} to {save_path}")
        else:
            print(f"Failed to download: {url} - Status code: {response.status_code}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

# Function to download linked pages recursively
def download_linked_pages(base_url, current_url):
    # Get the HTML content of the current URL
    response = requests.get(current_url)
    if response.status_code == 200:
        html_content = response.text
        # Parse HTML content
        soup = BeautifulSoup(html_content, "html.parser")
        # Find all anchor tags
        anchor_tags = soup.find_all("a", href=True)
        # Download each linked page recursively
        for anchor_tag in anchor_tags:
            link = anchor_tag["href"]
            # Skip email and tel href attributes
            if link.startswith("mailto:") or link.startswith("tel:"):
                continue
            # If the link is a relative URL, make it absolute
            if not link.startswith("http"):
                link = urljoin(base_url, link)
            # Ensure the link belongs to the same domain
            if urlparse(link).netloc == urlparse(base_url).netloc:
                try:
                    # Create the directory structure for the linked page
                    relative_path = urlparse(link).path.lstrip("/")
                    directory_path = os.path.join(os.path.dirname(base_url), relative_path)
                    os.makedirs(directory_path, exist_ok=True)
                    # Download the linked page
                    download_assets(link)
                    parse_html_and_download_assets(os.path.join(directory_path, "index.html"), base_url)
                    # Recursively download linked pages
                    download_linked_pages(base_url, link)
                except Exception as e:
                    print(f"Error downloading linked page: {link} - {e}")





# Main function
def main():
    # URL of the WordPress page
    wordpress_url = "http://intouchstudio.com/"
    
    # Convert WordPress page to static HTML
    subprocess.run([
        wget_path,
        "--page-requisites",
        "--convert-links",
        "--no-parent",
        wordpress_url
    ])
    
    # Extract the base URL
    base_url = urlparse(wordpress_url).netloc
    
    # Download assets
    download_assets(wordpress_url)

    # Parse HTML and download referenced assets
    parse_html_and_download_assets(os.path.join(base_url, "index.html"), base_url)

    # Download linked pages recursively
    download_linked_pages(base_url, wordpress_url)

# Execute the main function
if __name__ == "__main__":
    main()
