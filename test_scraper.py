from scraper import WebScraper

# Test LinkedIn people scraping by industry
scraper = WebScraper()
industry = "Technology"
print(f"Testing LinkedIn people scraping for: {industry} (limited to 2 people)")
try:
    data = scraper.scrape_linkedin_people_by_industry(industry, max_people=2)
    print("Scraped data:")
    for item in data:
        print(item)
    print(f"\nTotal items scraped: {len(data)}")
except Exception as e:
    print("LinkedIn scraping failed:", e)
    import traceback
    traceback.print_exc()
