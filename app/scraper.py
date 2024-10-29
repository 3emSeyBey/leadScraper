import argparse
import traceback
from typing import Dict
from playwright.async_api import async_playwright, Page
import re
import asyncio

class Scraper:
    def __init__(self, url):
        self.url = url
        self.result = None
        self.company_name = url.split(".")[1]
        self.emails = []
        self.phone_numbers = []
        self.social_media_links = {
            'facebook': [],
            'instagram': [],
            'linkedin': []
        }
    
    async def scrape(self, page):
        try:
            await page.goto(self.url, wait_until='load')
            await self.scrape_phone_from_page(page)
            await self.scrape_email_from_page(page)
            await self.scrape_social_links_from_page(page)
            self.result = {
            'contact': {
                'emails': self.emails,
                'phone_numbers': self.phone_numbers,
                'website': self.url,
                'social_media': self.social_media_links
                }
            }
        except Exception as e:
            traceback.print_exc()
            self.result = {'url': self.url, 'success': False, 'error': str(e)}

    def get_result(self):
        return self.result

    async def scrape_phone_from_page(self, page: Page):
        body = await page.query_selector('body')
        body_text = await body.inner_text()

        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}(?:\s?(?:ext|x|extension)\s?\d{1,5})?'
        ]
        phone_texts = await page.locator('body >> text=/phone|telephone/i').element_handles()
        phone_links = await page.locator('body >> a[href^="tel:"]').element_handles()

        for element in phone_texts + phone_links:
            text_content = await element.text_content()
            number = text_content.strip()  # Corrected: strip() is called after awaiting
            if any(re.match(pattern, number) for pattern in phone_patterns):
                self.phone_numbers.append(number)

        for pattern in phone_patterns:
            numbers_found = re.findall(pattern, body_text)
            self.phone_numbers.extend(numbers_found)

        self.phone_numbers = [number for number in self.phone_numbers if len(number) > 8]
        self.phone_numbers = list(set(self.phone_numbers))

    async def scrape_email_from_page(self, page: Page):
        page_content = await page.content()

        # Updated regex to include a domain part that contains at least one letter
        email_patterns = [r'[\w\.-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}']

        # Collect potential email texts from the page
        email_texts = await page.locator('text=/email|contact|info|mail/i').element_handles()
        email_links = await page.locator('a[href^="mailto:"]').element_handles()

        for element in email_texts + email_links:
            text_content = await element.text_content()
            email_candidate = text_content.strip()  # Properly call strip() after awaiting
            if any(re.match(pattern, email_candidate) for pattern in email_patterns):
                self.emails.append(email_candidate)

        for pattern in email_patterns:
            emails_found = re.findall(pattern, page_content)
            self.emails.extend(emails_found)

        # Filter out emails with purely numeric domains
        self.emails = [
            email for email in set(self.emails)
            if not re.match(r'^[\w\.-]+@[0-9]+\.[\w\.-]+$', email)
        ]

        self.emails = list(set(self.emails))
        
    async def scrape_social_links_from_page(self, page: Page):
        social_url_patterns = ["facebook.com", "instagram.com", "linkedin.com"]

        anchors = await page.locator('a[href]').element_handles()

        for anchor in anchors:
            href = await anchor.get_attribute('href')
            if href:
                href = href.strip()  
            for pattern in social_url_patterns:
                if pattern in href:
                    if "facebook.com" in href:
                        self.social_media_links['facebook'].append(href)
                    elif "instagram.com" in href:
                        self.social_media_links['instagram'].append(href)
                    elif "linkedin.com" in href:
                        self.social_media_links['linkedin'].append(href)

        for platform in self.social_media_links:
            self.social_media_links[platform] = list(set(self.social_media_links[platform]))

    async def visit_page(self, url: str) -> Dict:
        async with self.semaphore:
            page = await self.browser.new_page()
            try:
                await page.goto(url, wait_until='load')
                await self.scrape_phone_from_page(page)
                await self.scrape_email_from_page(page)
                await self.scrape_social_links_from_page(page)
            except Exception as e:
                traceback.print_exc()
                print(f"Error visiting {url}: {e}")
            finally:
                await page.close()
        
        return {
            'contact': {
                'emails': self.emails,
                'phone_numbers': self.phone_numbers,
                'website': self.company_url,
                'social_media': self.social_media_links
            }
        }