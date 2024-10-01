import csv
import traceback
import requests
from serpapi import GoogleSearch
from tqdm import tqdm


test_run = True

class GenerateLeads:
    def __init__(self, city, state, country, industry):
        self.city = city
        self.state = state
        self.country = country
        self.lat = None
        self.long = None
        self.industry = industry
        self.data = []

    def get_coordinates(self):
        try:
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    'q': f"{self.city}, {self.state}, {self.country}",
                    'format': 'json',
                    'addressdetails': 1,
                    'limit': 1
                },
                headers={'User-Agent': 'LeadGeneratorApp/1.0'}
            )
            response.raise_for_status()  # Raise an HTTPError for bad responses
            data = response.json()
            if data:
                self.lat = data[0]['lat']
                self.long = data[0]['lon']
            else:
                print("No data found for the given location.")
                raise ValueError("No data found for the given location.")
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None, None
        except ValueError as e:
            print(f"JSON decoding error: {e}")
            return None, None
        except KeyError as e:
            print(f"Key error: {e}")
            return None, None

    def get_search_results_from_serp(self, city, state, country, industry, page):
        try:
            params = {
                "api_key": "093aee5dc04d5fc6ab56270391a66fefe0760ba31a4cb4fa551881efe44d4999",
                "engine": "google_maps",
                "type": "search",
                "google_domain": "google.com",
                "q": f"{self.industry}",
                "ll": f"@{self.lat},{self.long},14z",
                "hl": "en",
                "start": str(20 * page)
            }
            search = GoogleSearch(params)
            results = search.get_dict()
            return results
        except Exception as e:
            print(f"Error fetching search results: {e}")
            return {}

    def get_data(self):
        if self.lat and self.long:
            pages = 5
            if test_run:
                pages = 1
            for page in tqdm(range(pages), desc="Fetching search results"):
                try:
                    results = self.get_search_results_from_serp(self.city, self.state, self.country, self.industry, page)
                    self.data.append(results.get('local_results', []))
                except Exception as e:
                    print(f"Error processing page {page}: {e}")
        else:
            print("Failed to get coordinates.")

    def filter_data(self):
        filtered_data = []
        seen_place_ids = set()

        for page in self.data:
            for item in page:
                try:
                    place_id = item.get('place_id')
                    if place_id and place_id not in seen_place_ids:
                        seen_place_ids.add(place_id)
                        name = item.get('title', '')
                        address = item.get('address', '')
                        city = self.city
                        state = self.state
                        country = self.country
                        tags = item.get('types', [])
                        phone = item.get('phone', '')
                        website = item.get('website', '')
                        email = item.get('email', '')   
                        filtered_data.append({
                            'name': name,
                            'address': address,
                            'city': city,
                            'state': state,
                            'country': country,
                            'tags': tags,
                            'phone': phone,
                            'email': email,
                            'website': website,
                        })
                except Exception as e:
                    print(f"Error processing item: {e}")
        return filtered_data
    
    def write_data_to_csv(self):
        try:
            with open('leads.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Company Name", "Company Address", "Company City", "Company State", "Tags", "Company Phone Number", "Company Website", "Company Facebook URL", "Company Instagram URLs", "Company LinkedIn URL", "Company Owner Email", "Company Owner Phone Number"])
                for item in self.filtered_data:
                    name = item.get('name', '')
                    address = item.get('address', '')
                    city = item.get('city', '')
                    state = item.get('state', '')
                    tags = ', '.join(item.get('tags', []))
                    phone = item.get('phone', '')
                    website = item.get('website', '')
                    
                    writer.writerow([name, address, city, state, tags, phone, website, "", "", "", "", ""])
        except Exception as e:
            print(f"Error saving data: {e}")

    def run(self):
        self.get_coordinates()
        self.get_data()
        self.filtered_data = self.filter_data()
        self.write_data_to_csv()
    
def main(city, state, country, industry):
    lead = GenerateLeads(city, state, country, industry)
    try:
        lead.run()
        print("Leads generated successfully.")
    except Exception as e:
        print(f"Error generating leads: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_run:
        city = "Cebu City"
        state = "Cebu"
        country = "Philippines"
        industry = "Dental Clinic"
    else:
        city = input("Enter city: ")
        state = input("Enter state: ")
        country = input("Enter country: ")
        industry = input("Enter industry: ")
    main(city, state, country, industry)
