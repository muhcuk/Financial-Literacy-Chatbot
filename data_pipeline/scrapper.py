import os
import time
import base64
import undetected_chromedriver as uc

# --- Configuration ---
OUTPUT_FOLDER = "pdfs" 

URLS_TO_SCRAPE = [
    {
        "url":"https://www.kwsp.gov.my/w/infographic/smart-budgeting-technique",
        "filename":"smart budgeting technique"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/first-salary-tips",
        "filename":"first salary tips"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/travelling-green-tips",
        "filename":"travelling green tips"
    },
    {
        "url":"https://www.kwsp.gov.my/w/infographic/insurance-tips",
     
        "filename":"insurance tips"
    },
    {
        "url":"https://www.kwsp.gov.my/w/infographic/savings-tips-for-gig-workers",
        "filename":"saving tips for gig worker"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/epf-death-assistance",
        "filename":"death assistance"
    },
    {
        "url":"https://www.kwsp.gov.my/w/infographic/multiply-savings-with-i-saraan",
        "filename":"multiple savings with i saraan"
    },
    {
       
         "url":"https://www.kwsp.gov.my/w/article/expenses-after-retired",
        "filename":"expense after retired"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/fomo-shopping",
        "filename":"fomo shopping"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/why-medical-insurance-is-important",
        "filename":"why medical insurance importance"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/buy-vs-rent-malaysia",
        "filename":"buy vs rent"
    },
    {
   
         "url":"https://www.kwsp.gov.my/w/article/fashion-on-a-budget",
        "filename":"fashion on a budget"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/50-30-20-rule",
        "filename":"budgeting rule"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/how-to-file-income-tax",
        "filename":"file income tax"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/compound-interest-benefits",
        "filename":"compound interest benefits"
    },
   
     {
        "url":"https://www.kwsp.gov.my/w/article/pay-yourself-first",
        "filename":"pay yourself first"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/new-year-financial-goals",
        "filename":"new year financial goals"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/master-your-finance",
        "filename":"master your finance"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/quick-ways-to-lose-savings",
        "filename":"quick ways to losing savings"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/surviving-on-paycheck",
        "filename":"surviving on paycheck"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/scam-red-flags",
        "filename":"scam red flags"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/vacation-on-budget",
        "filename":"vacation on budget"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/save-money-malaysian-ways",
        "filename":"save money malaysian ways"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/financial-independence",
        "filename":"financial independence"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/how-to-avoid-online-scam",
        "filename":"how to avoid online scam"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/buy-first-think-later",
        "filename":"buy first think later"
    },
    {
       
         "url":"https://www.kwsp.gov.my/w/article/income-and-your-savings",
        "filename":"income and your savings"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/retirement-planning-tips",
        "filename":"retirement planning tips"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/savings-and-inflation",
        "filename":"savings and inflation"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/achieve-money-goal",
        "filename":"achieve money goals"
    },
    {
  
         "url":"https://www.kwsp.gov.my/w/article/how-to-use-akaun-3",
        "filename":"how to use akaun 3"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/savings-for-festives",
        "filename":"saving for festives"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/simpanan-shariah-retirement",
        "filename":"shariah retirement"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/invest-smarter",
        "filename":"invest smarter"
    },
  
     {
        "url":"https://www.kwsp.gov.my/w/article/retirement-calculator",
        "filename":"retirement calculator"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/ensuring-wife-future",
        "filename":"ensuring wife future"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/epf-housing-withdrawal",
        "filename":"epf house"
    },
    {
        "url":"https//www.kwsp.gov.my/w/article/emergency-fund",
        "filename":"emergency fund"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/reward-yourself",
        "filename":"reward yourself"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/unwise-spending-habits",
        "filename":"unwise spending habits"
    },
    {
        "url":"httpsIn://www.kwsp.gov.my/w/article/boost-your-savings",
        "filename":"boost your savings"
    },
    {
        "url":"https://www.kwsp.gov.my/w/article/reasons-to-save-money",
        "filename":"reasons to save money"
     },
]
# --- End Configuration ---

def scrape_sites_to_pdf():
    print("Starting website scraping process...")
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36')

    try:
        # This will automatically download and patch the correct driver
        driver = uc.Chrome(options=options)
    except Exception as e:
        print(f"Error initializing WebDriver: {e}")
        print("Please ensure you have Chrome installed.")
        return

    try:
        for item in URLS_TO_SCRAPE:
            raw_url = item["url"]
            # Normalize and validate URL (fix common typos like missing ':' or wrong scheme)
            def normalize_url(u: str) -> str:
                if not u:
                    return u
                u = u.strip()
                # Fix common malformed schemes
                if u.lower().startswith("https//"):
                    u = u.replace("https//", "https://", 1)
                if u.lower().startswith("http:/") and not u.lower().startswith("http://"):
                    u = u.replace("http:/", "http://", 1)
                if u.lower().startswith("httpsin://"):
                    u = u.replace("httpsin://", "https://", 1)
                # Add scheme if missing
                if not (u.startswith("http://") or u.startswith("https://")):
                    if u.startswith("www."):
                        u = "https://" + u
                    else:
                        u = "https://" + u
                return u

            url = normalize_url(raw_url)
            if url != raw_url:
                print(f"Normalized URL: {raw_url} -> {url}")
            filename = item["filename"]
            if not filename.lower().endswith('.pdf'):
                filename = filename + '.pdf'
            output_path = os.path.join(OUTPUT_FOLDER, filename)
            
            print(f"  Navigating to: {url}")
            try:
                driver.get(url)
            except Exception as e:
                print(f"  ❌ Failed to load URL {url}: {e}")
                continue
 
            # Keep 15s wait for Cloudflare to resolve
            time.sleep(15) 

            print(f"  Scraping and saving to: {output_path}")
            print_options = {
                'printBackground': True,
                'preferCSSPageSize': True,
                'landscape': False,
 
            }
            result = driver.execute_cdp_cmd('Page.printToPDF', print_options)
            
            pdf_data = base64.b64decode(result['data'])
            
            with open(output_path, 'wb') as f:
                f.write(pdf_data)
            print(f"  Saved {filename}")
    finally:
        print("Scraping complete. Closing browser.")
        driver.quit()

if __name__ == "__main__":
    scrape_sites_to_pdf()