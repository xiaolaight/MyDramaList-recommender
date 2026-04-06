from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd

ctr = 0
options = Options()
options.add_argument("user-agent=laightly")
# uncomment below line to optimize the webscraping process but lose ability to see the driver window
# options.add_argument("--headless=new")
options.page_load_strategy = 'normal'
mp = {}
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)

# consider three most dominant genres
def getGenres(soup):
    genres = [x.get_text(strip=True) for x in soup.select("li.show-genres a")]
    if len(genres) > 3:
        return genres[:3]
    if (len(genres) == 0):
        return -1
    return genres

# extract three most popular keywords from tags
def getTags(soup):
    tags = [x.get_text(strip=True) for x in soup.select("li.show-tags a")]
    if len(tags) > 3:
        return tags[:3]
    if (len(tags) == 0):
        return -1
    return tags

# take in all directors and screenwriters
def getCrew(soup):
    try:
        director = [x.get_text(strip=True) for x in soup.select("li:has(b:-soup-contains('Director')) a")]
    except:
        director = []
    try:
        screenwriter = [x.get_text(strip=True) for x in soup.select("li:has(b:-soup-contains('Screenwriter')) a")]
    except:
        screenwriter = director
    return [director, screenwriter]

# take in top three actors (so should be two leads and considering one support lead)
def getLeads(soup):
    leads = [x.get_text(strip=True) for x in soup.find_all("b", attrs={'itempropx': "name"})]
    if len(leads) < 3:
        return leads
    if (len(leads) == 0):
        return -1
    return [leads[0], leads[1], leads[2]]

# webscraper control function for each individual drama
def extract(title):
    ret = [title]
    html = driver.page_source
    lil_soup = BeautifulSoup(html, "lxml")
    while True:
        try:
            cur = getGenres(lil_soup)
            if (cur == -1):
                driver.refresh()
                html = driver.page_source
                lil_soup = (html, "lxml")
                continue
            ret.append(cur)
            break
        except:
            driver.refresh()
            html = driver.page_source
            lil_soup = BeautifulSoup(html, "lxml")
    while True:
        try:
            cur = getTags(lil_soup)
            if (cur == -1):
                driver.refresh()
                html = driver.page_source
                lil_soup = (html, "lxml")
                continue
            ret.append(cur)
            break
        except:
            driver.refresh()
            html = driver.page_source
            lil_soup = BeautifulSoup(html, "lxml")
    while True:
        try:
            L = getCrew(lil_soup)
            for p in L:
                ret.append(p)
            break
        except:
            driver.refresh()
            html = driver.page_source
            lil_soup = BeautifulSoup(html, "lxml")
    while True:
        try:
            cur = getLeads(lil_soup)
            if (cur == -1):
                driver.refresh()
                html = driver.page_source
                lil_soup = (html, "lxml")
                continue
            ret.append(cur)
            break
        except:
            driver.refresh()
            html = driver.page_source
            lil_soup = BeautifulSoup(html, "lxml")
    return ret

# a full run could take more than an hour, so splitting them up into batches could be an option you consider.
info = []
for i in range(1, 251):
    url = "https://mydramalist.com/shows/top?page=" + str(i)
    driver.get(url)
    big_html = driver.page_source
    soup = BeautifulSoup(big_html, "lxml")
    shows = soup.select(".text-primary.title")
    while len(shows) == 0:
        driver.refresh()
        big_html = driver.page_source
        soup = BeautifulSoup(big_html, "lxml")
        shows = soup.select(".text-primary.title")
    for show in shows:
        ctr += 1
        show = show.a
        link = "https://mydramalist.com/" + show["href"]
        driver.get(link)
        info.append(extract(show.string))
    print(i)

# export to drama_data.csv, or any filepath you would like to choose
df = pd.DataFrame(info, columns=["Title", "Genres", "Tags", "Director", "Screenwriter", "Actors"])
df.to_csv('drama_data.csv', index=False)
