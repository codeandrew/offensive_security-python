import requests
import re
import urllib.parse as urlparse
from bs4 import BeautifulSoup

class Scanner:
    def __init__(self, url, ignore_links) -> None:
        self.session = requests.Session()
        self.target_url = url 
        self.target_links = []
        self.ignore_links = ignore_links

    def extract_links_from(self, url):
        # headers = {
        #     "Cookie": "PHPSESSID=oi7673bicmjlmcnthnrhvlmpt5; security=low; phpMyAdmin=6ff94ac6d748239b9c4f2a73c74f87ba; pma_lang=en; 5d89dac18813e15aa2f75788275e3588=bu0fc0d7ijh15nhknldosad50p"
        # }
        # response = requests.session(url, headers=headers)
        response = self.session.get(url)
        return re.findall('(?:href=")(.*?)"', response.text)

    def crawl(self, url=None):
        if url == None:
            url = self.target_url

        href_links = self.extract_links_from(url)
        for link in href_links:
            parsed_link = urlparse.urljoin(url, link)

            if "#" in parsed_link:
                parsed_link = parsed_link.split('#')[0]

            if self.target_url in parsed_link and parsed_link not in self.target_links and parsed_link not in self.ignore_links:
                self.target_links.append(parsed_link)
                print(parsed_link)
                self.crawl(parsed_link)

    def extract_csrf_token(self, session, url): 
        response = session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        # ALWAYS CHECK FOR CSRF FIELD this is DVWA 
        token = soup.find('input', {'name': 'user_token'})['value']
        return token

    def extract_forms(self, url):
        response = self.session.get(url)
        parsed_html = BeautifulSoup(response.content, features="html.parser")
        return parsed_html.findAll("form")

    def submit_form(self, form, value, url):
        action = form.get("action")
        method = form.get("method")
        post_url = urlparse.urljoin(url, action)

        print(
            f"URL: {post_url} : \n",
            "[+] Forms: \n"
            f"action: {action}",
            f"method: {method}"
        )
        # payload = "XSS TEST"
        
        input_list = form.findAll("input")
        post_data = {}
        for input in input_list:
            input_name = input.get('name')
            input_type = input.get('type')
            input_value = input.get('value')
            if input_type == 'text':
                input_value = value
            
            post_data[input_name] = input_value
        if method == 'post':
            return self.session.post(post_url,data=post_data)
        return self.session.get(post_url, params=post_data)


def dvwa_scan():
    # EXAMPLE ATTACK IF THERE's AUTHENTICATION 
    # DVWA TARGET 
    # docker run --rm -it -p 80:80 vulnerables/web-dvwa
    target_url = "http://localhost" # DVWA
    links_to_ignore = [
        'http://localhost/logout.php'
    ]

    vuln_scanner = Scanner(url=target_url,ignore_links=links_to_ignore)
    login = f"{target_url}/login.php"
    token = vuln_scanner.extract_csrf_token(vuln_scanner.session, url=login)
    dvwa_login = {
        "username": 'admin',
        "password": 'password',
        "Login": 'submit',
        "user_token": token
    }
    vuln_scanner.session.post(login, data=dvwa_login)
    # vuln_scanner.crawl()

    test_url = "http://localhost/vulnerabilities/xss_r/"
    forms = vuln_scanner.extract_forms(test_url)
    print(forms)
    response = vuln_scanner.submit_form(form=forms[0], value='testtest',url=test_url)
    print(response.text)



if __name__ == "__main__":
    dvwa_scan()
