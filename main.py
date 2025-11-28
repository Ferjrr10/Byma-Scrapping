from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time

def scrape_angular_datatable():
    """Scrape the Angular datatable component"""
    chrome_options = Options()
    # Remove headless for debugging
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        print("Navigating to page...")
        driver.get("https://open.bymadata.com.ar/#/issuers-negociable-securities-information")
        
        # Wait for Angular to load
        wait = WebDriverWait(driver, 30)
        time.sleep(8)
        
        print("Looking for Angular datatable...")
        
        # Wait for the datatable rows to be present
        rows = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "div.datatable-row-center.datatable-row-group")
        ))
        
        print(f"Found {len(rows)} data rows")
        
        data = []
        
        for i, row in enumerate(rows):
            try:
                # Extract all cells from this row
                cells = row.find_elements(By.CSS_SELECTOR, "datatable-body-cell")
                
                if len(cells) >= 6:
                    row_data = {
                        "Fecha": extract_cell_text(cells[0]),
                        "Especie": extract_cell_text(cells[1]),
                        "Referencia": extract_cell_text(cells[2]),
                        "Descarga": extract_download_icon(cells[3]),
                        "Tipo de": extract_cell_text(cells[4]),
                        "Emisor": extract_cell_text(cells[5])
                    }
                    data.append(row_data)
                    print(f"Processed row {i+1}: {row_data['Especie']} - {row_data['Emisor']}")
                
            except Exception as e:
                print(f"Error processing row {i}: {e}")
                continue
        
        return pd.DataFrame(data)
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        # Take screenshot for debugging
        driver.save_screenshot("error_debug.png")
        return None
    finally:
        driver.quit()

def extract_cell_text(cell_element):
    """Extract text from a datatable cell"""
    try:
        # The text is inside mdp-data-table-cell -> div.content
        content_div = cell_element.find_element(By.CSS_SELECTOR, "mdp-data-table-cell div.content")
        return content_div.text.strip()
    except:
        return ""

def extract_download_icon(cell_element):
    """Extract download icon information"""
    try:
        # Check if there's a download icon
        icon = cell_element.find_element(By.CSS_SELECTOR, "i.glyphicon-download-alt")
        return "Download available"
    except:
        return ""

def scrape_with_scroll():
    """Alternative method that scrolls to load all data"""
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get("https://open.bymadata.com.ar/#/issuers-negociable-securities-information")
        wait = WebDriverWait(driver, 30)
        time.sleep(10)
        
        # Scroll to bottom to trigger lazy loading
        print("Scrolling to load all data...")
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        for i in range(5):  # Scroll up to 5 times
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            print(f"Scroll {i+1}, new height: {new_height}")
        
        # Now extract data
        return extract_all_data(driver)
        
    except Exception as e:
        print(f"Error in scroll method: {e}")
        return None
    finally:
        driver.quit()

def extract_all_data(driver):
    """Extract all data after page is fully loaded"""
    wait = WebDriverWait(driver, 10)
    
    try:
        # Wait for rows to be present
        rows = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "div.datatable-row-center.datatable-row-group")
        ))
        
        print(f"Total rows found: {len(rows)}")
        
        data = []
        
        for i, row in enumerate(rows):
            try:
                cells = row.find_elements(By.CSS_SELECTOR, "datatable-body-cell")
                
                if len(cells) >= 6:
                    row_data = {
                        "Fecha": extract_cell_text(cells[0]),
                        "Especie": extract_cell_text(cells[1]),
                        "Referencia": extract_cell_text(cells[2]),
                        "Descarga": "Yes" if has_download_icon(cells[3]) else "No",
                        "Tipo de": extract_cell_text(cells[4]),
                        "Emisor": extract_cell_text(cells[5])
                    }
                    data.append(row_data)
                    
                    # Print progress every 10 rows
                    if (i + 1) % 10 == 0:
                        print(f"Processed {i + 1} rows...")
                
            except Exception as e:
                print(f"Error in row {i}: {e}")
                continue
        
        return pd.DataFrame(data)
        
    except Exception as e:
        print(f"Error extracting data: {e}")
        return None

def has_download_icon(cell_element):
    """Check if cell has download icon"""
    try:
        cell_element.find_element(By.CSS_SELECTOR, "i.glyphicon-download-alt")
        return True
    except:
        return False

def main():
    print("Starting Angular datatable scraping...")
    
    # Try the basic method first
    print("=== Method 1: Basic Extraction ===")
    df = scrape_angular_datatable()
    
    if df is not None and not df.empty:
        print(f"✅ Success! Scraped {len(df)} rows with basic method")
    else:
        print("❌ Basic method failed, trying scroll method...")
        print("=== Method 2: Scroll to Load All Data ===")
        df = scrape_with_scroll()
    
    if df is not None and not df.empty:
        print(f"✅ Final result: {len(df)} rows scraped")
        print("\nFirst 10 rows:")
        print(df.head(10))
        
        # Save to CSV
        filename = "bymadata_angular_table.csv"
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"\nData saved to '{filename}'")
        
        # Show some statistics
        print(f"\n📊 Summary:")
        print(f"Total records: {len(df)}")
        print(f"Unique emisores: {df['Emisor'].nunique()}")
        print(f"Unique especies: {df['Especie'].nunique()}")
        print(f"Files available for download: {df[df['Descarga'] == 'Yes'].shape[0]}")
        
    else:
        print("❌ All methods failed")
        print("Please check:")
        print("1. Is the website accessible?")
        print("2. Is there any popup or login required?")
        print("3. Check the browser screenshot for debugging")

if __name__ == "__main__":
    main()