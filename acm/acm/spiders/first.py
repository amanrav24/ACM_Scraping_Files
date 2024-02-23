import scrapy
import json
import requests
import json
from bs4 import BeautifulSoup

#Instructions
'''

First Part:
Comment out all the scrapy code(Line signal below)
Then run python3 first.py
Make sure to have beautifulSoup and other dependencies(Requirements.txt file)

Second Part:
Comment out all the Part 1 BS4 code and Part3:Combining Files(bottom part)
###Make sure to have Scrapy pip installed
You can either run all yield statements in parse and/or parse_conf_links, or comment out the ones you dont want to see different parts
- Each of the yield statements in parse and parse_conf_links have comments indicating their purpose
- How I ran this code was that I ran it 4 different times, commenting out different combinations of yield statements
    -Then I combined all four files(conferences,meta_data,proceedings, subject_area) into one file, info.json
    - I got conferences by commenting out the first yield line in Parse function and 2nd line in conf_links function
    - I got meta_data by commenting out the 2nd and 3rd yield lines in Parse function
    - I got proceedings by commenting out first yield line in Parse and first yield line  in conf_links
    - I got subject_areas from commenting out first 2 yield lines in parse, and leaving the third
    - ALl these lines can then be run with: scrapy crawl first -o whateverFileName.json in terminal

Part 3:
Comment out first two parts
Run with python3 first.py
This is where all the files are combined into info.json
Chnage the file paths of the four json files according to the file you named and their respective paths

'''


###
#Part1: BeautifulSoup
###

url = 'https://dl.acm.org/conferences'
html = requests.get(url).text
soup = BeautifulSoup(html, 'lxml')


my_json = {}
Rtitles = []
descriptions = []
#Goes through and picks up all titles and descriptions
containers = soup.find('ul', class_="search-result__body items-results container search-result__browse search-result--tile")
for li in containers.find_all('li'):
    for title in li.find_all('span', class_ = 'browse-title'):
        Rtitles.append(title.string)
    for descrip in li.find_all('div', class_ = 'meta__abstract meta__abstract--dynamic'):
        descriptions.append(descrip.string.strip().replace("\n",''))
#Processes titles and descriptions
for t, d in zip(Rtitles, descriptions):
    my_json[t] = d
#formats json.titles in proper way
def dictionary_json(dict):
    json_string = "{\n"
    for key, val in dict.items():
        json_string += "\t" + '"' + key + '"' + ":{\n"
        json_string += '\t\t"Description":' + json.dumps(val) + "\n"
        json_string += "\t" + "}," + "\n"
    json_string = json_string[:-2] + json_string[-1]
    json_string += "}\n"
    return json_string
#Turns python dictionary to json format
output = dictionary_json(my_json)

file_path = "titles.json"
with open(file_path, "w") as file:
    file.write(output)

######
#COMMENT OUT EVERYTHING ABOVE OR BELOW WHEN RUNNING CODE-WILL MIGHT NOT WORK TOGETHER(originally two different files)
####
    
#Part 2: Scrapy

class FirstSpider(scrapy.Spider):
    name = "first"
    allowed_domains = ["dl.acm.org"]
    start_urls = ["https://dl.acm.org/conferences"]


    #function that goes through a gets all 125 links for each ACM SIG
    def parse(self, response):
        for sigs in response.css('h4.search__item-title'):
            title = sigs.css('::attr(title)').get()
            links = sigs.css('::attr(href)')

            #Links for getting metadata
            #yield response.follow(links.get(), callback=self.parse_pages, meta = {'name': title})
            #Links for getting confereneces, proceedings
            yield response.follow(links.get(), callback=self.parse_conf_links, meta = {'name': title})
            #Links for getting subject_areas
            #yield response.follow(links.get(), callback=self.subject_areas, meta = {'name': title})

    #Function that gets the MetaData
    def parse_pages(self, response):
        title = response.meta['name']#gets the SIG name and passes them through 
        output = {}
        six_details = response.css('div.bibliometrics__count')
        product = six_details.css('span::text').getall()
        #These two lines remove the two fields we dont want, downloads 6, 12
        product.pop(6)
        product.pop(6)
        output = {
            'Publication Years': product[0],
            'Publication Count': product[1],
            'Available for Download': product[2],
            'Citation Count': product[3],
            'Downloads (cumulative)': product[4],
            'Average Citation per Article': product[5],
            'Average Downloads per Article': product[6]
        }
        yield {title: output}

    #This function gets two links to view more proceedings, and conferences
    def parse_conf_links(self, response):
        title = response.meta['name']
        conflinks = response.css('div.more-link a::attr(href)').getall()
        #Gets Upcoming conferences
        yield response.follow(conflinks[0], callback = self.conferencesLink, meta = {'name': title})
        #Gets proceedings
        #yield response.follow(conflinks[1], callback = self.proceedings, meta = {'name': title})


    #function that processes conferences from the "view all conferences page"
    def conferencesLink(self, response):
        upcoming_conferences = {}
        upcoming_conferencesOut = {}
        title1 = response.meta['name']#gets the SIG name
        list = response.css('li.search__item.card--shadow.search__item--event')# Each of the conferences
        for index, conf in enumerate(list):
            left = conf.css('div.right--block')#intermediate for title
            title = left.css('span::text').get()#title

            right1 = conf.css('div.info.calender')#intermdiate tag for date
            date = right1.css('span::text')#date
            clean = date.get().strip()#date cleaned

            right2 = conf.css('div.info.map')
            city = right2.css('span.hlFld-CityTextFieldLang::text').get().strip()#get city
            country = right2.css('span.hlFld-CountryTextFieldLang::text').get().strip()#get state
            location = city + country # combination

            upcoming_conference = {
                "name" : title,
                "date" : clean,
                "location" : location
            }
            upcoming_conferences[index] = upcoming_conference
            upcoming_conferencesOut = {'upcoming_conferences' : upcoming_conferences}
        yield {title1:upcoming_conferencesOut}
    

    def proceedings(self, response):
        #Function that processes the view all proceedings page
        proceedings = {}
        proceedingsOut = {}
        title = response.meta['name']#gets the SIG name
        proceedingList = response.css('li.conference__proceedings')
        for index, proceed in enumerate(proceedingList):
            proceeding_name = proceed.css('a::text').get()
            upcoming_proceeding = {
                'title' : proceeding_name
            }
            proceedings[index] = upcoming_proceeding
        proceedingsOut = {'proceedings' : proceedings}
        yield {title: proceedingsOut }

    def subject_areas(self, response):
        title = response.meta['name']#gets the SIG name
        subject_areas = {}
        tags = response.css('div[data-tags]::attr(data-tags)').get()
        list = json.loads(tags)
        area = []
        for i in list:
            area.append(i['label'])
        subject_areas = {'subject_areas' : area}

        yield {title : subject_areas}

###
#Part 3: Combining json files
###   


#Change these paths according to actual file paths, these are my absolute paths
file_path_titles = '/Users/amanr/ScrapyProj/acm/titles.json'
file_path_meta_data = '/Users/amanr/ScrapyProj/acm/meta_data.json'
file_path_proceedings = '/Users/amanr/ScrapyProj/acm/proceedings.json'
file_path_conferences = '/Users/amanr/ScrapyProj/acm/conferences.json'
file_path_subjectAreas = '/Users/amanr/ScrapyProj/acm/subject_area.json'

with open(file_path_titles, 'r') as file:
    titles = json.load(file)

with open(file_path_meta_data, 'r') as file:
    meta_data = json.load(file)

with open(file_path_proceedings, 'r') as file:
    proceedings = json.load(file)

with open(file_path_conferences, 'r') as file:
    conferences = json.load(file)

with open(file_path_subjectAreas, 'r') as file:
    subject_areas = json.load(file)

info_json2 = {}
info_json = {}

for meta_datas in meta_data:
    conference_name = list(meta_datas.keys())[0]
    json_copy = meta_datas.copy()

    # Find and merge matching conference info
    for conference in conferences:
        if conference_name in conference:
            json_copy[conference_name].update(conference[conference_name])
            break

    # Find and merge matching proceedings info
    for proceeding in proceedings: 
        if conference_name in proceeding:
            json_copy[conference_name].update(proceeding[conference_name])
            break

    for items in subject_areas:
        if conference_name in items:
            json_copy[conference_name].update(items[conference_name])
            break

    # Add to info_json
    info_json.update(json_copy)

file_path_to_save = '/Users/amanr/ScrapyProj/acm/infoTest.json' #Change this path

# Save the combined JSON to a file
with open(file_path_to_save, 'w') as file:
    json.dump(info_json, file, indent=4) 
