# Topos Data Engineer Intern Assignment
# Ning Xia

from bs4 import BeautifulSoup
import requests
import urllib
import pandas as pd
import re
import json

def blurb(query):
    '''A function using wikipedia API to get a brief introduction of the query (city)'''

    URI = "https://en.wikipedia.org/w/api.php"
    p = {
        "action": "opensearch",
        "search": query,
        "limit": 1,
        "redirects": "resolve",
        "format": "json"
    }

    response = requests.get(URI, params=p)
    data = json.loads(response.text)

    if len(data[2]) <= 0:
        return "Not found"

    description = data[2][0]
    return description

def getWebsite(url):
    '''A function getting the official website url from city wikipedia page'''

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    table = soup.select(".infobox.geography")[0]
    # website in cell [-1, -2, -6]:
    linkLine = table.findAll('tr')[-1]
    if 'Website' not in linkLine.text:
        linkLine = table.findAll('tr')[-2]
    if 'Website' not in linkLine.text:
        linkLine = table.findAll('tr')[-6]
    linkAttr = linkLine.find('a')
    if linkAttr is None:
        return 'No website found'
    return linkAttr.attrs['href']

url = "https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'lxml')
table = soup.select(".wikitable.sortable")[0] # there are 4 tables in the current page; only the 1st is what I need

rows = table.findAll('tr')
columns = rows[0]

columnLabel = []
for th in columns.findAll('th')[:-1]: # not including location
    # Need to clean the column names if any side note exists
    ex = re.search("\[\S\]",th.text)
    if ex is not None:
        columnLabel.append(th.text[:ex.start()])
    else:
        columnLabel.append(th.text.strip())

columnLabel.append("briefDescription")
columnLabel.append('website')
tableContent = []
tableContent.append(columnLabel)

for row in rows[1:151]: # including only the first 150 cities
    tdList = row.findAll('td')
    content = []
    for i in range(len(tdList)):
        if i != 7 and i != 9 and i != 10: # excluding unwanted columns
            text = tdList[i].text.strip()
            cleaned = text.replace(',', '').replace('+', '').replace('%', '')
            note = re.search("\[\S\]",cleaned)
            if note is not None:
                cleaned = cleaned[:note.start()]
            if "sq\xa0mi" in cleaned:
                cleaned = re.findall('(\d+\.?\d+)', cleaned)[0]
            content.append(cleaned)
    # get the url of the page of the city for website
    atags = tdList[1].find('a')
    city_page = urllib.parse.urljoin('https://en.wikipedia.org', atags.attrs['href'])
    website = getWebsite(city_page)
    # including briefDescription and website
    content.append(blurb(content[1]+' '+content[2]))
    content.append(website)
    tableContent.append(content)

# output as a csv file
df = pd.DataFrame(tableContent[1:], columns=columnLabel)
df.to_csv('wikiOutput.csv', encoding='utf-8', index=False)
