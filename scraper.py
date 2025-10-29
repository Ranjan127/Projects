import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import logging
import re
from urllib.parse import urljoin, urlparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self):
        self.session = requests.Session()

    def scrape_static(self, url, selector, attribute=None, headers=None):
        """
        Scrape a static webpage and extract data using CSS selector.
        """
        try:
            if headers:
                self.session.headers.update(headers)
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            data = self.extract_data(soup, selector, attribute)
            logger.info(f"Successfully scraped static page: {url}")
            return data
        except requests.RequestException as e:
            logger.error(f"Error scraping static page {url}: {e}")
            return []

    def scrape_dynamic(self, url, selector, attribute=None, wait_time=5):
        """
        Scrape a dynamic webpage and extract data using CSS selector.
        Requires ChromeDriver to be installed and in PATH.
        """
        try:
            options = Options()
            options.add_argument("--headless")  # Run in headless mode
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            service = Service()  # Assumes chromedriver is in PATH
            driver = webdriver.Chrome(service=service, options=options)

            driver.get(url)
            time.sleep(wait_time)  # Wait for dynamic content to load

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            data = self.extract_data(soup, selector, attribute)
            driver.quit()
            logger.info(f"Successfully scraped dynamic page: {url}")
            return data
        except Exception as e:
            logger.error(f"Error scraping dynamic page {url}: {e}")
            return []

    def extract_data(self, soup, selector, attribute=None):
        """
        Extract data from BeautifulSoup object using CSS selector.
        """
        try:
            elements = soup.select(selector)
            if attribute:
                data = [elem.get(attribute) for elem in elements if elem.get(attribute)]
            else:
                data = [elem.get_text(strip=True) for elem in elements]
            logger.info(f"Extracted {len(data)} items using selector: {selector}")
            return data
        except Exception as e:
            logger.error(f"Error extracting data with selector {selector}: {e}")
            return []

    def scrape_comprehensive_data(self, url, scrape_type='static'):
        """
        Scrape comprehensive data including emails, names, LinkedIn profiles, phone numbers, and social media links.
        """
        try:
            logger.info(f"Starting comprehensive scrape for URL: {url}")
            if scrape_type == 'dynamic':
                options = Options()
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                service = Service()
                driver = webdriver.Chrome(service=service, options=options)
                driver.get(url)
                time.sleep(5)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                driver.quit()
            else:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                response = self.session.get(url, headers=headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')

            data = []

            # Extract emails
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, soup.get_text())
            unique_emails = list(set(emails))
            if unique_emails:
                data.append("Emails found:")
                data.extend(unique_emails)
                data.append("")

            # Extract phone numbers
            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            phones = re.findall(phone_pattern, soup.get_text())
            unique_phones = list(set(phones))
            if unique_phones:
                data.append("Phone numbers found:")
                data.extend(unique_phones)
                data.append("")

            # Extract LinkedIn profiles
            linkedin_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'linkedin.com' in href and ('/in/' in href or '/company/' in href):
                    linkedin_links.append(urljoin(url, href))
            unique_linkedin = list(set(linkedin_links))
            if unique_linkedin:
                data.append("LinkedIn profiles found:")
                data.extend(unique_linkedin)
                data.append("")

            # Extract social media links (Twitter, Facebook, Instagram, etc.)
            social_platforms = ['twitter.com', 'facebook.com', 'instagram.com', 'youtube.com', 'linkedin.com']
            social_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                for platform in social_platforms:
                    if platform in href and href not in unique_linkedin:  # Avoid duplicating LinkedIn
                        social_links.append(urljoin(url, href))
            unique_social = list(set(social_links))
            if unique_social:
                data.append("Social media links found:")
                data.extend(unique_social)
                data.append("")

            # Extract potential names (simple heuristic)
            name_pattern = r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b'
            potential_names = re.findall(name_pattern, soup.get_text())
            unique_names = list(set(potential_names))
            if unique_names:
                data.append("Potential names found:")
                data.extend(unique_names[:50])  # Limit to 50 to avoid too much data
                data.append("")

            if not data:
                data = ["No comprehensive data found on the page."]

            logger.info(f"Successfully scraped comprehensive data from: {url}")
            return data
        except Exception as e:
            logger.error(f"Error scraping comprehensive data from {url}: {str(e)}")
            raise

    def scrape_all_headings_and_content(self, url, scrape_type='static'):
        """Scrape all headings and their associated content from the page."""
        try:
            logger.info(f"Starting full page scrape for URL: {url}")
            if scrape_type == 'dynamic':
                options = Options()
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                service = Service()
                driver = webdriver.Chrome(service=service, options=options)
                driver.get(url)
                time.sleep(5)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                driver.quit()
            else:
                response = self.session.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')

            data = []
            # Scrape all headings and their content
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                heading_text = heading.get_text(strip=True)
                content = []
                # Get content after the heading until next heading
                sibling = heading.find_next_sibling()
                while sibling and sibling.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if sibling.name in ['p', 'div', 'span', 'li']:
                        text = sibling.get_text(strip=True)
                        if text:
                            content.append(text)
                    sibling = sibling.find_next_sibling()
                content_text = ' '.join(content) if content else 'No content found'
                data.append(f"{heading.name.upper()}: {heading_text}")
                data.append(f"Content: {content_text}")
                data.append("")  # Empty line for separation

            if not data:
                data = ["No headings found on the page."]

            logger.info(f"Successfully scraped full page: {url}")
            return data
        except Exception as e:
            logger.error(f"Error scraping full page {url}: {str(e)}")
            raise

    def scrape_linkedin_people_by_industry(self, industry_name, max_people=None, location=None):
        """
        Scrape LinkedIn profiles of people working in a specific industry and optional location.
        """
        try:
            logger.info(f"Starting LinkedIn people scrape for industry: {industry_name}, location: {location}")

            people_data = []

            # Search strategies for LinkedIn people
            if location:
                search_strategies = [
                    f"people in {industry_name} industry {location} linkedin",
                    f"{industry_name} professionals {location} linkedin",
                    f"executives in {industry_name} {location} linkedin",
                    f"{industry_name} industry leaders {location} linkedin",
                    f"top {industry_name} experts {location} linkedin"
                ]
            else:
                search_strategies = [
                    f"people in {industry_name} industry linkedin",
                    f"{industry_name} professionals linkedin",
                    f"executives in {industry_name} linkedin",
                    f"{industry_name} industry leaders linkedin",
                    f"top {industry_name} experts linkedin"
                ]

            # Use Selenium with LinkedIn-friendly settings
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            service = Service()
            driver = webdriver.Chrome(service=service, options=options)

            # Execute JavaScript to remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            linkedin_profiles = set()

            for strategy in search_strategies:
                if max_people and len(linkedin_profiles) >= max_people:
                    break

                search_query = strategy
                search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}&num=50"

                page = 0
                max_pages_per_strategy = 3  # Fewer pages for LinkedIn

                while len(linkedin_profiles) < (max_people or float('inf')) and page < max_pages_per_strategy:
                    try:
                        current_url = f"{search_url}&start={page * 50}"
                        driver.get(current_url)
                        time.sleep(4 + page)  # Longer delay for LinkedIn

                        soup = BeautifulSoup(driver.page_source, 'html.parser')

                        # Extract LinkedIn profile URLs
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            if href.startswith('/url?q=') and 'linkedin.com/in/' in href:
                                profile_url = href.split('/url?q=')[1].split('&')[0]
                                if profile_url not in linkedin_profiles:
                                    linkedin_profiles.add(profile_url)
                                    if max_people and len(linkedin_profiles) >= max_people:
                                        break

                        page += 1
                        time.sleep(3 + page * 0.5)

                    except Exception as e:
                        logger.warning(f"Error on page {page} for strategy '{strategy}': {e}")
                        break

            driver.quit()

            linkedin_profiles = list(linkedin_profiles)
            logger.info(f"Found {len(linkedin_profiles)} LinkedIn profiles for {industry_name}")

            # Scrape each LinkedIn profile
            for i, profile_url in enumerate(linkedin_profiles):
                if max_people and i >= max_people:
                    break

                try:
                    logger.info(f"Scraping LinkedIn profile {i+1}/{len(linkedin_profiles)}: {profile_url}")
                    person_data = self.scrape_linkedin_profile(profile_url)
                    if person_data:
                        people_data.append(person_data)
                    time.sleep(5)  # Respectful delay for LinkedIn
                except Exception as e:
                    logger.warning(f"Failed to scrape LinkedIn profile {profile_url}: {e}")
                    continue

            # Structure the final data as list of dicts for Excel columns
            structured_data = []
            for person in people_data:
                structured_data.append({
                    'Name': person.get('name', 'Unknown'),
                    'Position': person.get('position', 'N/A'),
                    'Company': person.get('company', 'N/A'),
                    'Location': person.get('location', 'N/A'),
                    'LinkedIn URL': person.get('linkedin_url', 'N/A'),
                    'Email': person.get('email', 'N/A'),
                    'Phone': person.get('phone', 'N/A')
                })

            logger.info(f"Successfully scraped {len(people_data)} LinkedIn profiles for {industry_name}")
            return structured_data
        except Exception as e:
            logger.error(f"Error scraping LinkedIn people for {industry_name}: {str(e)}")
            raise

    def scrape_linkedin_profile(self, profile_url):
        """
        Scrape individual LinkedIn profile data.
        """
        try:
            logger.info(f"Scraping LinkedIn profile: {profile_url}")

            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            service = Service()
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(profile_url)
            time.sleep(5)  # Wait for LinkedIn to load

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            driver.quit()

            # Extract name
            name = "Unknown"
            name_elem = soup.find('h1', {'class': re.compile(r'text-heading-xlarge')})
            if name_elem:
                name = name_elem.get_text(strip=True)

            # Extract position and company
            position = "N/A"
            company = "N/A"
            experience_elem = soup.find('div', {'class': re.compile(r'pv-text-details__left-panel')})
            if experience_elem:
                position_elem = experience_elem.find('div', {'class': re.compile(r'text-body-medium')})
                if position_elem:
                    position = position_elem.get_text(strip=True)

                company_elem = experience_elem.find('span', {'class': re.compile(r'text-body-small')})
                if company_elem:
                    company = company_elem.get_text(strip=True)

            # Extract location
            location = "N/A"
            location_elem = soup.find('span', {'class': re.compile(r'text-body-small.*geo-region')})
            if location_elem:
                location = location_elem.get_text(strip=True)

            # Extract contact info (email and phone)
            email = "N/A"
            phone = "N/A"
            contact_text = soup.get_text()
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, contact_text)
            if emails:
                email = emails[0]  # Take first email found

            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            phones = re.findall(phone_pattern, contact_text)
            if phones:
                phone = phones[0]  # Take first phone found

            person_data = {
                'name': name,
                'position': position,
                'company': company,
                'location': location,
                'linkedin_url': profile_url,
                'email': email,
                'phone': phone
            }

            logger.info(f"Successfully scraped LinkedIn profile: {name}")
            return person_data
        except Exception as e:
            logger.error(f"Error scraping LinkedIn profile {profile_url}: {str(e)}")
            return None

    def scrape_company_personnel(self, company_url, scrape_type='static'):
        """
        Scrape personnel data from a company website.
        """
        try:
            logger.info(f"Scraping personnel from: {company_url}")
            if scrape_type == 'dynamic':
                options = Options()
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                service = Service()
                driver = webdriver.Chrome(service=service, options=options)
                driver.get(company_url)
                time.sleep(5)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                driver.quit()
            else:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                response = self.session.get(company_url, headers=headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')

            # Extract company name
            company_name = "Unknown"
            title_tag = soup.find('title')
            if title_tag:
                company_name = title_tag.get_text().split('|')[0].strip()

            # Extract emails
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, soup.get_text())
            unique_emails = list(set(emails))

            # Extract phone numbers
            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            phones = re.findall(phone_pattern, soup.get_text())
            unique_phones = list(set(phones))

            # Extract LinkedIn profiles
            linkedin_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if 'linkedin.com' in href:
                    linkedin_links.append(urljoin(company_url, href))

            # Extract potential names and positions
            personnel = []
            text = soup.get_text()
            name_pattern = r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b'
            potential_names = re.findall(name_pattern, text)
            unique_names = list(set(potential_names))

            # Look for common position titles near names
            positions = ['CEO', 'CTO', 'CFO', 'COO', 'President', 'Vice President', 'Director', 'Manager', 'Founder', 'Co-Founder']
            for name in unique_names[:20]:  # Limit to avoid too many false positives
                # Find context around the name
                name_index = text.find(name)
                if name_index != -1:
                    context_start = max(0, name_index - 100)
                    context_end = min(len(text), name_index + len(name) + 100)
                    context = text[context_start:context_end]

                    # Check for position titles in context
                    found_position = None
                    for pos in positions:
                        if pos.lower() in context.lower():
                            found_position = pos
                            break

                    # Find email near the name
                    nearby_emails = []
                    for email in unique_emails:
                        email_index = text.find(email)
                        if email_index != -1 and abs(email_index - name_index) < 200:  # Within 200 chars
                            nearby_emails.append(email)

                    # Find LinkedIn near the name
                    nearby_linkedin = []
                    for linkedin in linkedin_links:
                        if name.lower().replace(' ', '') in linkedin.lower():
                            nearby_linkedin.append(linkedin)

                    if found_position or nearby_emails or nearby_linkedin:
                        personnel.append({
                            'name': name,
                            'position': found_position or 'N/A',
                            'email': ', '.join(nearby_emails) if nearby_emails else 'N/A',
                            'linkedin': ', '.join(nearby_linkedin) if nearby_linkedin else 'N/A'
                        })

            # Extract address (simple heuristic)
            address = "N/A"
            address_keywords = ['address', 'location', 'headquarters']
            for keyword in address_keywords:
                addr_elem = soup.find(text=re.compile(keyword, re.IGNORECASE))
                if addr_elem:
                    parent = addr_elem.parent
                    address_text = parent.get_text() if parent else addr_elem
                    address = address_text.strip()
                    break

            company_data = {
                'company_name': company_name,
                'url': company_url,
                'address': address,
                'phone': ', '.join(unique_phones) if unique_phones else 'N/A',
                'personnel': personnel
            }

            logger.info(f"Successfully scraped personnel data from: {company_url}")
            return company_data
        except Exception as e:
            logger.error(f"Error scraping personnel from {company_url}: {str(e)}")
            return None

# Example usage
if __name__ == "__main__":
    scraper = WebScraper()

    # Example: Scrape a static page
    static_url = "https://example.com"
    data = scraper.scrape_static(static_url, 'h1')
    print("Titles:", data)

    # Example: Scrape a dynamic page (requires Selenium setup)
    # dynamic_url = "https://example-dynamic-site.com"
    # data = scraper.scrape_dynamic(dynamic_url, '.dynamic-class')
    # print("Dynamic data:", data)
