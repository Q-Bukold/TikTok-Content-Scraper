import requests
import browser_cookie3

def _innit_request_headers(self):
    # Request Headers
    self.headers = {'Accept-Encoding': 'gzip, deflate, sdch',
                    'Accept-Language': 'en-US,en;q=0.8',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Cache-Control': 'max-age=0',
                    'Connection': 'keep-alive',
                    'referer' : 'https://www.tiktok.com/'}

    self.context_dict = {'viewport': {'width': 0, 'height': 0},
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0'}

    self.cookies = dict()
    
    ''' # note for myself ; copied from pyktok
    soup = BeautifulSoup(r.text, "html.parser")
    tt_script = soup.find('script', attrs={'id':"__UNIVERSAL_DATA_FOR_REHYDRATION__"})
    tt_json = json.loads(tt_script.string)
    '''