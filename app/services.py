import asyncio
import csv
import re
import traceback
import requests
from serpapi import GoogleSearch
from typing import List, Dict, Tuple
from playwright.async_api import async_playwright, Browser
import os
import aiomysql
from datetime import datetime
import config
from scraper import Scraper
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            tasks = [self.scrape_url(url, context) for url in self.urls]
            results = await asyncio.gather(*tasks)
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

    def filter_data(self, data) -> List[Dict]:
        filtered_data = []
        seen_place_ids = set()

        for item in data:
            try:
                place_id = item.get('place_id')
                if place_id and place_id not in seen_place_ids:
                    website = item.get('links', {}).get('website', '')
                    if website == '' or website == None:
                        website = self.get_missing_website_data(item.get('place_id_search'))
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
            conn = await aiomysql.connect(
                host=os.getenv('DB_HOST'),
                port=int(os.getenv('DB_PORT')),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                db=os.getenv('DB_NAME')
            )
            async with conn.cursor() as cur:
                for item in data:
                    try:
                        await cur.execute("""
                            INSERT INTO results (
                                location, industry, place_id, date_generated, name, address, city, state, country, tags, phone, email, website, lat, lng,
                                phones_from_website, emails_from_website, facebook, instagram, linkedin, owner_email, owner_phone
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            self.location, self.industry, item['place_id'], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), item['name'], item['address'], item['city'], item['state'], item['country'],
                            item['tags'], item['phone'], item['email'], item['website'], item.get('lat', ''),
                            item.get('lng', ''), item.get('phones_from_website', ''), item.get('emails_from_website', ''),
                            item.get('facebook', ''), item.get('instagram', ''), item.get('linkedin', ''), '', ''
                        ))
                        logger.info(f"Inserted item {item['place_id']} into database")
                    except Exception as e:
                        logger.error(f"Error inserting item {item['place_id']} into database: {e}")
                await conn.commit()
        except Exception as e:
            logger.error(f"Error connecting to the database: {e}")
        finally:
            if conn:
                conn.close()

    async def check_for_existing_results(self):
        try:
            conn = await aiomysql.connect(
                host=os.getenv('DB_HOST'),
                port=int(os.getenv('DB_PORT')),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                db=os.getenv('DB_NAME')
            )
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("SELECT * FROM results WHERE location = %s AND industry = %s", (self.location, self.industry))
                results = await cur.fetchall()
                if results:
                    conn.close()
                    return results
                else:
                    conn.close()
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
        try:
            url = serp_url
            headers = {'User-Agent': 'LeadGeneratorApp/1.0'}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get('local_results', [])[0]['links']['website']
        except Exception as e:
            raise ValueError(f"Error fetching missing website data: {e}")
        
    
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

    async def run(self) -> str:
        try:
            existing_results = await self.check_for_existing_results()
            filtered_data = []
            if existing_results == None:
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