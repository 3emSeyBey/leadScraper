import asyncio
import csv
import re
import traceback
import requests
from serpapi import GoogleSearch
from typing import List, Dict, Tuple
from playwright.async_api import async_playwright, Browser
from fastapi.security import OAuth2PasswordBearer
from fastapi import Request
import os
import asyncpg
from asyncpg import create_pool
from datetime import datetime, timedelta
from typing import Optional
import config
from urllib.parse import urlparse, parse_qs
from scraper import Scraper
import logging
from models import User
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class OAuth2PasswordBearerCookie(OAuth2PasswordBearer):
    def __init__(self, tokenUrl: str, cookie_name: str = "access_token"):
        super().__init__(tokenUrl=tokenUrl)
        self.cookie_name = cookie_name

    async def __call__(self, request: Request):
        token = request.cookies.get(self.cookie_name)
        if not token:
            return await super().__call__(request)
        return token
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

class ScraperService:
    def __init__(self, urls: List[str]):
        self.urls = urls
        self.semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent tasks

    async def scrape_url(self, url, context):
        async with self.semaphore:
            page = await context.new_page()
            scraper = Scraper(url)
            await scraper.scrape(page)
            result = scraper.get_result()
            await page.close()
            return result
    
    async def run(self):
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                tasks = [self.scrape_url(url, context) for url in self.urls]
                results = await asyncio.gather(*tasks)
            except Exception as e:
                traceback.print_exc()
                raise ValueError(f"Error scraping websites: {e}")
            await context.close()
            await browser.close()
            return results

class GenerateLeadsService:
    def __init__(self, location: str, industry: str, min_results: int):
        self.location = location
        self.industry = industry
        self.min_results = min_results
        self.data = []
        self.existing_data = []
        self.db_pool = None
        
    
    async def init_db_pool(self):
        """Initialize the database connection pool."""
        self.db_pool = await create_pool(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT')),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )

    async def close_db_pool(self):
        """Close the database connection pool."""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("Database connection pool closed.")

    async def fetch_all_results(self) -> List[Dict]:
        query = "SELECT * FROM results;"
        records = await self.db_pool.fetch(query)
        return [dict(record) for record in records]
    
    async def get_search_results_from_serp(self, page: int) -> Dict:
        params = {
            "api_key": config.SERP_API_KEY,
            "engine": "google_local",
            "type": "search",
            "google_domain": "google.com",
            "q": f"{self.industry}",
            "hl": "en",
            "location": f"{self.location}",
            "start": str(20 * page)
        }
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            return results
        except Exception as e:
            raise ValueError(f"Error fetching search results: {e}")

    async def get_data(self):
        data = []
        page = 1
        while True:
            try:
                results = await self.get_search_results_from_serp(page)
                for res in results.get('local_results', []):
                    if res.get('place_id') not in [item.get('place_id') for item in data]:
                        if self.existing_data:
                            if res.get('place_id') not in self.existing_data:
                                data.append(res)
                        else:
                            data.append(res)
                if len(data) >= self.min_results:
                    return data
                page += 1
            except Exception as e:
                raise ValueError(f"Error processing page {page}: {e}")             

    def extract_city_state_country_from_address(self, address: str) -> Tuple[str, str, str]:
        parts = [part.strip() for part in address.split(',')]
        if len(parts) >= 4:
            country = parts[-1]
            state = parts[-3]
            city = parts[-4]
            return city, state, country
        return None, None, None

    async def filter_data(self, data) -> List[Dict]:
        filtered_data = []
        seen_place_ids = set()

        for item in data:
            try:
                place_id = item.get('place_id')
                if place_id and place_id not in seen_place_ids:
                    website = item.get('links', {}).get('website', '')
                    if website == '' or website == None:
                        website = await self.get_missing_website_data(item.get('place_id_search'))
                    seen_place_ids.add(place_id)
                    place_id = item.get('place_id', '')
                    name = item.get('title', '')
                    tags = item.get('type', '')
                    phone = item.get('phone', '')
                    email = ', '.join(item.get('email', []))
                    lat = item.get('gps_coordinates', {}).get('latitude')
                    lng = item.get('gps_coordinates', {}).get('longitude')
                    address = self.get_address_from_latlng(lat, lng)
                    
                    # Extract city and state from address
                    city, state, country = self.extract_city_state_country_from_address(address) if address else (None, None, None)
                    
                    filtered_data.append({
                        'name': name,
                        'place_id': place_id,
                        'address': address,
                        'city': city,
                        'state': state,
                        'country': country,
                        'tags': tags,
                        'phone': phone,
                        'email': email,
                        'website': website,
                        'lat': lat,
                        'lng': lng
                    })
            except Exception as e:
                traceback.print_exc()
                raise ValueError(f"Error processing item: {e}")
                    
        return filtered_data
    
    def get_address_from_latlng(self, lat: float, lng: float) -> str:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}"
        headers = {'User-Agent': 'LeadGeneratorApp/1.0'}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            if 'error' not in data:
                address = data['display_name']
                return address
        except Exception as e:
            return None
        return None
    
    def generate_csv(self, data, file_path: str):
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Name", "Address", "City", "State", "Country", "Tags", 
                    "Phone Number 1", "Phone Number 2", "Phone Number 3", 
                    "Email 1", "Email 2", 
                    "Website", "Facebook URL", "Instagram URLs", "LinkedIn URL", 
                    "Owner Email", "Owner Phone Number"
                ])
                
                for item in data:
                    # Split phone numbers
                    phone_numbers = item.get('phones_from_website', '').split(', ')
                    phone_number_1 = item.get('phone', '')
                    phone_number_2 = phone_numbers[0] if len(phone_numbers) > 0 else ''
                    phone_number_3 = ', '.join(phone_numbers[1:]) if len(phone_numbers) > 1 else ''
                    
                    # Split emails
                    emails = item.get('emails_from_website', '').split(', ')
                    email_1 = emails[0] if len(emails) > 0 else ''
                    email_2 = ', '.join(emails[1:]) if len(emails) > 1 else ''
                    
                    writer.writerow([
                        item['name'],
                        item['address'],
                        item['city'],
                        item['state'],
                        item['country'],
                        item['tags'],
                        phone_number_1,
                        phone_number_2,
                        phone_number_3,
                        email_1,
                        email_2,
                        item['website'],
                        item.get('facebook', ''),
                        item.get('instagram', ''),
                        item.get('linkedin', ''),
                        "",
                        ""
                    ])
        except Exception as e:
            raise ValueError(f"Error writing CSV file: {e}")

    async def save_results_to_db(self, data: List[Dict]):
        try:
            async with self.db_pool.acquire() as conn:
                async with conn.transaction():
                    for item in data:
                        try:
                            sql_command = """
                                INSERT INTO results (
                                    location, industry, place_id, date_generated, name, address, city, state, country, tags, phone, email, website, lat, lng,
                                    phones_from_website, emails_from_website, facebook, instagram, linkedin, owner_email, owner_phone
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22)
                            """
                            params = (
                                str(self.location), str(self.industry), str(item['place_id']), datetime.now(),
                                str(item.get('name', '')), str(item.get('address', '')), str(item.get('city', '')), str(item.get('state', '')), str(item.get('country', '')), str(item.get('tags', '')),
                                str(item.get('phone', '')), str(item.get('email', '')), str(item.get('website', '')),
                                str(item.get('lat', '')), str(item.get('lng', '')),  # Convert lat and lng to strings
                                str(item.get('phones_from_website', '')), str(item.get('emails_from_website', '')),
                                str(item.get('facebook', '')), str(item.get('instagram', '')), str(item.get('linkedin', '')), '', ''
                            )

                            await conn.execute(sql_command, *params)
                            logger.info(f"Inserted item {item['place_id']} into database")
                        except Exception as e:
                            logger.error(f"Error inserting item {item['place_id']} into database: {e}. Item details: {item}")
        except Exception as e:
            logger.error(f"Error connecting to the database: {e}")

    async def check_for_existing_results(self):
        try:
            conn = await asyncpg.connect(
                host=os.getenv('DB_HOST'),
                port=int(os.getenv('DB_PORT')),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME')
            )
            query = "SELECT * FROM results WHERE location = $1 AND industry = $2"
            results = await conn.fetch(query, self.location, self.industry)
            await conn.close()
            if results:
                return results
            else:
                return None
        except Exception as e:
            logger.error(f"Error connecting to the database: {e}")
            return None
            
    def format_phone_number(self, phone_number: str) -> str:
        # Pattern to match 3 digits followed by a closing parenthesis or a dash
        pattern = re.compile(r'(\d{3})(\)|-)')
        match = pattern.search(phone_number)
        if match:
            # Insert '(' before the matched 3 digits if followed by a closing parenthesis
            if match.group(2) == ')':
                formatted_number = phone_number[:match.start()] + '(' + phone_number[match.start():]
            # Insert '(' before the matched 3 digits if followed by a dash
            elif match.group(2) == '-':
                formatted_number = phone_number[:match.start()] + '(' + phone_number[match.start():match.end()] + ')' + phone_number[match.end():]
            return formatted_number
        return phone_number

    async def get_missing_website_data(self, serp_url: str) -> Dict:
        ludo_cid = serp_url.split('ludocid=')[1].split('&')[0]
        params = {
            "api_key": config.SERP_API_KEY,
            "engine": "google_local",
            "type": "search",
            "google_domain": "google.com",
            "q": f"{self.industry}",
            "hl": "en",
            "location": f"{self.location}",
            "ludocid": ludo_cid
        }
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            website = results.get('local_results', [])[0].get('links', {}).get('website', '')
            return website if website else ''
        except Exception as e:
            raise ValueError(f"Error fetching search results: {e}")

    def rank_items_by_completeness(self, data):
        def completeness_score(item):
            score = 0
            if item.get('phones_from_website'):
                score += 1
            if item.get('emails_from_website'):
                score += 1
            if item.get('facebook'):
                score += 1
            if item.get('instagram'):
                score += 1
            if item.get('linkedin'):
                score += 1
            return score

        # Sort by completeness score in descending order
        data.sort(key=completeness_score, reverse=True)
        return data

    async def run(self) -> str:
        try:
            existing_results = await self.check_for_existing_results()
            filtered_data = []
            if existing_results == None:
                self.data = await self.get_data()
                filtered_data = await self.filter_data(self.data)
                urls = [item.get('website') for item in filtered_data if item.get('website')]

                # Scrape all URLs at once
                results = []
                if urls:
                    try:
                        scraper = ScraperService(urls)
                        results = await scraper.run()
                    except Exception as e:
                        print(f"Error scraping websites: {e}")

                # Map the results back to filtered data
                url_to_contact = {res['contact']['website']: res['contact'] for res in results if res.get('contact')}
                for item in filtered_data:
                    url = item.get('website')
                    if url in url_to_contact:
                        contact_info = url_to_contact[url]
                        phone_numbers = contact_info.get('phone_numbers', [])
                        emails = ', '.join(contact_info.get('emails', []))  # Convert list to comma-separated string
                        facebook = ', '.join(contact_info.get('social_media', {}).get('facebook', []))
                        instagram = ', '.join(contact_info.get('social_media', {}).get('instagram', []))
                        linkedin = ', '.join(contact_info.get('social_media', {}).get('linkedin', []))
                        formatted_phone_numbers = ', '.join(self.format_phone_number(phone) for phone in phone_numbers)
                        item['phones_from_website'] = formatted_phone_numbers
                        item['emails_from_website'] = emails
                        item['facebook'] = facebook
                        item['instagram'] = instagram
                        item['linkedin'] = linkedin

                # Generate CSV file
                await self.save_results_to_db(filtered_data)    
            else:
                self.existing_data = [item.get('place_id') for item in existing_results]
                if len(existing_results) < self.min_results:
                    result_to_fetch = self.min_results - len(existing_results)
                    self.min_results = result_to_fetch
                    self.data = await self.get_data()
                    filtered_data = self.filter_data(self.data)
                    urls = [item.get('website') for item in filtered_data if item.get('website')]
                    # Scrape all URLs at once
                
                    results = []
                    if urls:
                        try:
                            scraper = ScraperService(urls)
                            results = await scraper.run()
                        except Exception as e:
                            print(f"Error scraping websites: {e}")
        
                    # Map the results back to filtered data
                    url_to_contact = {res['contact']['website']: res['contact'] for res in results if res.get('contact')}
                    for item in filtered_data:
                        url = item.get('website')
                        if url in url_to_contact:
                            contact_info = url_to_contact[url]
                            phone_numbers = contact_info.get('phone_numbers', [])
                            emails = ', '.join(contact_info.get('emails', []))  # Convert list to comma-separated string
                            facebook = ', '.join(contact_info.get('social_media', {}).get('facebook', []))
                            instagram = ', '.join(contact_info.get('social_media', {}).get('instagram', []))
                            linkedin = ', '.join(contact_info.get('social_media', {}).get('linkedin', []))
                            formatted_phone_numbers = ', '.join(self.format_phone_number(phone) for phone in phone_numbers)
                            item['phones_from_website'] = formatted_phone_numbers
                            item['emails_from_website'] = emails
                            item['facebook'] = facebook
                            item['instagram'] = instagram
                            item['linkedin'] = linkedin
                            
                    await self.save_results_to_db(filtered_data)
                    filtered_data.extend(existing_results)
                else:
                    filtered_data.extend(existing_results[:self.min_results])

            file_path = f"leads{self.location}.csv"
            tobewritten = self.rank_items_by_completeness(filtered_data)[:self.min_results]
            self.generate_csv(tobewritten, file_path)
            return file_path
        except Exception as e:
            traceback.print_exc()

if __name__ == "__main__":
    lead = GenerateLeadsService(None, None, None)

    results = asyncio.run(lead.get_missing_website_data('https://serpapi.com/search.json?device=desktop&engine=google_local&gl=us&google_domain=google.com&hl=en&ludocid=1298802850896623899&q=coffee'))
    print(results)