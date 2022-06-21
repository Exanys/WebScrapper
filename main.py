import os
from selenium.webdriver.firefox.service import Service
from selenium import webdriver
from bs4 import BeautifulSoup
import time
import pandas as pd
from selenium.webdriver.firefox.options import Options
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()

options = Options()
options.binary_location = os.getenv('PATH_TO_EXECUTE_FIREFOX')
options.headless = True
service = Service(executable_path='./geckodriver')
browser = webdriver.Firefox(service=service, options=options)
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(os.getenv('EMAIL'), os.getenv('PASSWORD'))

msg = MIMEMultipart('alternative')
msg['Subject'] = "Tvorba kvalitních webových stránek"
msg['From'] = os.getenv('EMAIL')

html = MIMEText(open('html.txt', 'r').read(), 'html')
msg.attach(html)

names = []
emails = []
fields = []
websites = []

SEARCH_FIELDS = ['ruhl', 'úklid', 'kotl', 'kotel', 'instala', 'klíč', 'zahrad', 'kurz', 'dezinf', 'podl', 'květ',
                 'stave', 'tisk', 'chov', 'okna', 'pivo', 'kosme', 'masá', 'cukrá', 'rest', 'kav', 'káv']


def get_only_unique(arr):
    new_arr = set(arr)
    return list(new_arr)


city = input('Where to search: ').split()
PAGE_FROM = int(input('Start page: '))
PAGE_TO = int(input('End page: '))

try:
    def format_field(hrefs):
        field = ''
        for href in hrefs:
            field += href.get_text().strip()
            if not (href.get_text() == hrefs[-1].get_text()):
                field += ', '
        return field


    def get_info(idicko, field_hrefs, default_win):
        browser.switch_to.new_window('tab')
        browser.get(f'https://www.zlatestranky.cz/profil/{idicko}')
        time.sleep(3)
        content = browser.page_source
        soup = BeautifulSoup(content, features="html.parser")
        name = soup.find('h1', attrs={'itemprop': 'name'})
        mail = soup.find('a', attrs={'itemprop': 'email'})
        website = soup.find('a', attrs={'itemprop': 'url'}, class_='t-c')
        if mail:
            field = format_field(field_hrefs.find_all('a'))
            names.append(name.get_text().strip())
            emails.append(mail.get_text().strip())
            fields.append(field)
            websites.append(website.get_text().strip() if website else '')
            print(f'{names[-1]} - {emails[-1]} - {field}')
        browser.close()
        browser.switch_to.window(default_win)


    def scrap_page(page):
        browser.get(
            f'https://www.zlatestranky.cz/firmy/kraj/Moravskoslezský%20kraj/okres/{city[0].capitalize()}/{page}')
        time.sleep(3)
        content = browser.page_source
        original_window = browser.current_window_handle
        soup = BeautifulSoup(content, features="html.parser")
        for li in soup.find_all('li', class_="list-listing"):
            text = li.find_all('li')[1]
            for word in SEARCH_FIELDS:
                if word in text.get_text().lower():
                    get_info(li.get('id')[8:], text, original_window)
                    break


    for i in range(PAGE_FROM, PAGE_TO + 1):
        scrap_page(i)
finally:
    browser.quit()
    df = pd.DataFrame({'Company': names, 'Field': fields, 'Email': emails, 'Website': websites})
    df.to_csv(f'contacts_{PAGE_TO}.csv', index=False, encoding='utf-8')

    unique_emails = get_only_unique(emails)
    server.sendmail(os.getenv('EMAIL'), unique_emails, msg.as_string())
    server.quit()
