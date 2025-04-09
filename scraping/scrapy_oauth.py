import scrapy
import requests
import json

TOKEN_URL = 'https://example.com/oauth/token'  # Replace with your token endpoint
CLIENT_ID = 'your_client_id'
CLIENT_SECRET = 'your_client_secret'

class OAuthSpider(scrapy.Spider):
    name = 'oauth_spider'
    start_urls = ['https://example.com/protected/resource']  # Replace with your target

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token = self.get_oauth_token()

    def get_oauth_token(self):
        response = requests.post(
            TOKEN_URL,
            data={
                'grant_type': 'client_credentials',
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET
            }
        )
        response.raise_for_status()
        return response.json()['access_token']

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                headers={
                    'Authorization': f'Bearer {self.token}'
                }
            )

    def parse(self, response):
        # Example: just print the page title
        page_title = response.xpath('//title/text()').get()
        self.log(f'Page title: {page_title}')
