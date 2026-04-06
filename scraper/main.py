from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd

ctr = 0
options = Options()
options.add_argument("user-agent=laight")
options.add_argument("--headless=new")
options.page_load_strategy = 'normal'
driver = webdriver.Chrome(options=options)

# consider all genres
def getGenre(soup):
    genres = [x.get_text(strip=True) for x in soup.select("li.show-genres a")]
    if len(genres) > 3:
        return genres[:3]
    return genres

# extract keywords from description
def getTags(soup):
    tags = [x.get_text(strip=True) for x in soup.select("li.show-tags a")]
    if len(tags) > 3:
        return tags[:3]
    return tags

# take in director, screenwriter
def getCrew(soup):
    director = soup.select_one("li:has(b:-soup-contains('Director')) a").get_text(strip=True)
    screenwriter = soup.select_one("li:has(b:-soup-contains('Screenwriter')) a").get_text(strip=True)
    return [director, screenwriter]

# take in three most popular actors (so should be two leads and considering one support lead)
def getLeads(soup):
    leads = [x.get_text(strip=True) for x in soup.find_all("b", attrs={'itempropx': "name"})]
    if len(leads) < 3:
        return leads
    return [leads[0], leads[1], leads[2]]

# main control loop
def extract(title):
    ret = [title]
    html = driver.page_source
    lil_soup = BeautifulSoup(html, "lxml")
    while True:
        try:
            ret.append(getGenre(lil_soup))
            break
        except:
            driver.refresh()
            html = driver.page_source
            lil_soup = BeautifulSoup(html, "lxml")
    while True:
        try:
            ret.append(getTags(lil_soup))
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
            ret.append(getLeads(lil_soup))
            break
        except:
            driver.refresh()
            html = driver.page_source
            lil_soup = BeautifulSoup(html, "lxml")
    return ret

# it can be helpful to batch the scraping because selenium is slow by nature, making the entire scraping process run for ~45 minutes
# can also add print line as checkpoint if desired
info = []
for i in range(1, 251):
    url = "https://mydramalist.com/shows/top?page=" + str(i)
    driver.get(url)
    big_html = driver.page_source
    soup = BeautifulSoup(big_html, "lxml")
    shows = soup.select(".text-primary.title")
    for show in shows:
        ctr += 1
        show = show.a
        link = "https://mydramalist.com/" + show["href"]
        driver.get(link)
        info.append(extract(show.string))

df = pd.DataFrame(info, columns=["Title", "Genres", "Tags", "Director", "Screenwriter", "Actors"])
filepath = 'drama_data.csv' # update as fit
df.to_csv(filepath, index=False)
