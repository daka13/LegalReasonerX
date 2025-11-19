"""
CourtListener API utilities for legal citation lookup and analysis.
"""
import requests
from functools import lru_cache
import concurrent.futures
from typing import Dict, List, Optional, Tuple, Set, Any
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET


class CourtListenerAPI:
    """Wrapper for CourtListener API interactions."""

    BASE_URL = "https://www.courtlistener.com/api/rest/v4"

    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {'Authorization': f'Token {api_token}'}

    def make_get_request(self, url: str) -> Optional[Dict]:
        """Make a GET request to the CourtListener API."""
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")

    @lru_cache(maxsize=1024)
    def make_get_request_cached(self, url: str) -> Optional[Dict]:
        """Cached version of make_get_request."""
        return self.make_get_request(url)

    def verify_citation_in_text(self, text: str) -> Optional[Dict]:
        """Verify citations within text using the Citation Lookup API."""
        url = f"{self.BASE_URL}/citation-lookup/"
        headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"text": text}

        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")

    def fetch_all_urls_parallel(self, urls: List[str], max_workers: int = 10) -> Dict[str, Any]:
        """Fetch multiple URLs in parallel using ThreadPoolExecutor."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(self.make_get_request_cached, url): url
                for url in urls
            }
            results = {}
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    results[url] = future.result()
                except Exception as exc:
                    print(f"Error fetching {url}: {exc}")
                    results[url] = None
        return results


def extract_text_from_html(html_string: str) -> str:
    """Parse HTML and extract text content."""
    if not html_string:
        return ""

    try:
        soup = BeautifulSoup(html_string, 'html.parser')
        text = soup.get_text()

        # Normalize whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text
    except Exception as e:
        print(f"Error processing HTML: {e}")
        return ""


def extract_text_from_xml(xml_string: str) -> str:
    """Parse XML and extract text content."""
    if not xml_string:
        return ""

    try:
        root = ET.fromstring(xml_string)
        text_list = _extract_text_recursive(root)

        # Normalize whitespace
        text = '\n'.join(line.strip() for line in text_list if line.strip())
        text = text.replace('\n\n', '\n')

        return text
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return ""
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return ""


def _extract_text_recursive(element) -> List[str]:
    """Recursively extract text from an XML element and its children."""
    text_list = []
    if element.text:
        text_list.append(element.text)
    for child in element:
        text_list.extend(_extract_text_recursive(child))
    if element.tail:
        text_list.append(element.tail)
    return text_list


def extract_opinion(data: Dict) -> str:
    """Extract opinion text from various formats."""
    if data.get("html_with_citations", ""):
        return extract_text_from_html(data.get("html_with_citations"))
    elif data.get("html_columbia", ""):
        return extract_text_from_html(data.get("html_columbia"))
    elif data.get("html_lawbox", ""):
        return extract_text_from_html(data.get("html_lawbox"))
    elif data.get("xml_harvard", ""):
        return extract_text_from_xml(data.get("xml_harvard"))
    elif data.get("html_anon_2020", ""):
        return extract_text_from_html(data.get("html_anon_2020"))
    elif data.get("html", ""):
        return extract_text_from_html(data.get("html"))
    else:
        return data.get("plain_text", "")


def get_opinion_type_map(opinion_type: str) -> str:
    """Map opinion type codes to readable names."""
    type_map = {
        "010combined": "Combined Opinion",
        "020lead": "Lead Opinion",
        "030concurrence": "Concurrence Opinion",
        "040dissent": "Dissent",
        "015unamimous": "Unanimous Opinion",
        "025plurality": "Plurality Opinion",
        "035concurrenceinpart": "In Part Opinion",
        "050addendum": "Addendum",
        "060remittitur": "Remittitur",
        "070rehearing": "Rehearing",
        "080onthemerits": "On the Merits",
        "090onmotiontostrike": "On Motion to Strike Cost Bill",
        "100trialcourt": "Trial Court Document"
    }
    return type_map.get(opinion_type, "Unknown Opinion Type")
