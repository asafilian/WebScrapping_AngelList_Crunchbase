from requests import request
import re
import pandas as pd
import os
from selenium import webdriver
from time import sleep
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup as soup
import numpy as np
###################################################################################
#------------- START: A Class to scrap the Crunchbase Open Data Map (ODM) -------------#
class cruncbase_odm():
    '''
    This class is used to scrap the Crunchbase Open Data Map (ODM) via the Crunchbase's API.
    We need to a URL to the API (`base_url`), a user key to the API (`user_key`), and
    the type of organisations to be scrap.
    The get a right result, do as follows:
    1. Initialize an object:
        `crunchbase_obj = cruncbase_odm(base_url, user_key, org_type)`
    2. To scrap each page and pickle it:
        `crunchbase_obj.pickle_crunchbase_pages()`
    3. To concat all the pages to get a single data frame:
        `crunchbase_obj.concat_crunchbase_dfs(end_page=crunchbase_obj.number_pages)`
    4. To clean the data:
        `runchbase_obj.clean_crunchbase()`
    '''
    def __init__(self, base_url, user_key, org_type):
        self.base_url = base_url
        self.user_key = user_key
        self.org_type = org_type
        paging_info = self.get_paging_info()
        self.total_items = paging_info[0]
        self.number_pages = paging_info[1]

    def get_paging_info(self):
        params = {"user_key": self.user_key, "organization_types": self.org_type}

        data = request("GET", self.base_url, params=params).text
        #data = str(data.replace("null", "\"null\""))

        paging = re.findall("\"paging\":\{(.*?)\}", data)
        paging_split = re.split(',', str(paging[0]))
        total_items = int(re.split(':', paging_split[0])[1])
        number_of_pages = int(re.split(':', paging_split[1])[1])

        return [total_items, number_of_pages]


    def extract_data_per_page(self, page_num=1, pickle=True, path='pickles'):
        # set parameters
        params = {"user_key": self.user_key, "organization_types": self.org_type, "page": page_num}

        # get the data
        data = request("GET", self.base_url, params=params).text
        data = str(data.replace("null", "\"null\""))

        # properties
        properties = re.findall("\"properties\":\{(.*?)\}", data)

        # get the features
        names = []
        web_paths = []
        desciptions = []
        websites = []
        facebook_urls = []
        twitter_urls = []
        linkedin_urls = []
        cities = []
        regions = []
        countries = []
        # status = []
        # founded_on = []
        for i in range(len(properties)):
            country = 'null'
            country_text = re.findall("\"country_code\":\"(.*?)\"", properties[i])
            if country_text:
                country = country_text[0]

            name = 'null'
            name_text = re.findall("\"name\":\"(.*?)\"", properties[i])
            if name_text:
                name = name_text[0]

            web_path = 'null'
            web_path_text = re.findall("\"web_path\":\"(.*?)\"", properties[i])
            if web_path_text:
                web_path = web_path_text[0]

            description = 'null'
            description_text = re.findall("\"short_description\":\"(.*?)\"", properties[i])
            if description_text:
                description = description_text[0]

            website = 'null'
            website_text = re.findall("\"homepage_url\":\"(.*?)\"", properties[i])
            if website_text:
                website = website_text[0]

            facebook_url = 'null'
            facebook_url_text = re.findall("\"facebook_url\":\"(.*?)\"", properties[i])
            if facebook_url_text:
                facebook_url = facebook_url_text[0]

            twitter_url = 'null'
            twitter_url_text = re.findall("\"twitter_url\":\"(.*?)\"", properties[i])
            if twitter_url_text:
                twitter_url = twitter_url_text[0]

            linkedin_url = 'null'
            linkedin_url_text = re.findall("\"linkedin_url\":\"(.*?)\"", properties[i])
            if linkedin_url_text:
                linkedin_url = linkedin_url_text[0]

            city = 'null'
            city_text = re.findall("\"city_name\":\"(.*?)\"", properties[i])
            if city_text:
                city = city_text[0]

            region = 'null'
            region_text = re.findall("\"region_name\":\"(.*?)\"", properties[i])
            if region_text:
                region = region_text[0]
            # extra_info = self.get_info_com_page(web_path)
            # f_on = extra_info[0]
            # st = extra_info[1]

            names.append(name)
            web_paths.append(web_path)
            desciptions.append(description)
            websites.append(website)
            facebook_urls.append(facebook_url)
            twitter_urls.append(twitter_url)
            linkedin_urls.append(linkedin_url)
            cities.append(city)
            regions.append(region)
            countries.append(country)
            # founded_on.append(f_on)
            # status.append(st)

        # create a DataFrame
        data_df = pd.DataFrame({'Name': names,
                                'Country': countries,
                                'City': cities,
                                'Region': regions,
                                # 'Status': status,
                                # 'Founded_on': founded_on,
                                'URL': websites,
                                'Facebook': facebook_urls,
                                'Twitter': twitter_urls,
                                'LinkedIn': linkedin_urls,
                                'Crunch_page': web_paths,
                                'Description': desciptions})

        if pickle:
            if not os.path.isdir(path):
                print("Couldn't pickle the data frame, as the given path ('"+path+"') doesn't exist.")
            else:
                data_df.to_pickle(path+'/crunchbase_p'+format(page_num)+'.pkl')

        return data_df

    def pickle_crunchbase_pages(self, start_page=1, path='pickles'):
        if not os.path.isdir(path):
            raise ValueError("The given path (')"+path+"') doesn't exist.")

        for i in np.arange(start_page, self.number_pages + 1):
            self.extract_data_per_page(page_num=i, pickle=True, path=path)

        print(format(self.number_pages - start_page + 1) + ' pages of ODM Database was scraped.')
        print('Each was pickled as a DataFrame.')
        print('Total number of companies scraped is ' + format((self.number_pages - start_page + 1)*100))
        print('-------------------------------')

    def concat_crunchbase_dfs(self, end_page, start_page=1, path='pickles', pickle=True, dest_path='pickles'):
        if self.number_pages < end_page:
            raise ValueError("'end_page' must be less than number of pages (i.e., " + format(self.number_pages) + ").")

        if start_page > end_page:
            raise ValueError("'start_page' must be less than 'end_page'.")

        if not os.path.isdir(path):
            raise ValueError("The given path ('" + path + "') doesn't exist.")

        integrated_df = None
        for i in np.arange(start_page, end_page + 1):
            file_path = path + '/cruchbase_p' + format(i) + '.pkl'
            if not os.path.isfile(file_path):
                print("The file '" + file_path + "' doesn't exist!")
            else:
                df = pd.read_pickle(file_path)
                integrated_df = pd.concat([integrated_df, df])

        if pickle:
            if not os.path.isdir(dest_path):
                print("Couldn't pickle the data frame, as the given path ('" + dest_path + "') doesn't exist.")
            else:
                integrated_df.to_pickle(
                    dest_path + '/crunchbase_pp' + format(start_page) + '-' + format(end_page) + '.pkl')
                print("The result was pickled as " + dest_path + '/crunchbase_pp' +
                      format(start_page) + '-' + format(end_page) + '.pkl')

        return integrated_df

    def clean_crunchbase(self, file_path='pickles/crunchbase_pp1-8275.pkl',
                         country_keep=True,
                         city_keep=True,
                         region_keep=True,
                         url_keep=True,
                         facebook_keep=False,
                         twitter_keep=False,
                         linkedIn_keep=True,
                         crunchpage_keep=True,
                         description_keep=False,
                         social_make=True,
                         least_num_percountry=None,
                         pickle=True,
                         dest_pickle='pickles'):
        '''
        `*_keep` --> False: exclude form the dataset and True: keep
        `*_make` --> True: make a corresponding column in the dataset
        `social_make` --> make a column 'Social' stating the number of active social profile pages
        `least_num_percountry=n` --> keep those countries that has at least n companies registered
        `pickle` --> True: pickel
        '''

        # read the pickled dataset
        if not os.path.isfile(file_path):
            raise ValueError("The given file path ('" + file_path + "') doesn't exist.")

        # make sure, if given, 'least_num_percountry' is a valid integer
        if least_num_percountry:
            if not isinstance(least_num_percountry, int):
                raise ValueError("'least_num_percountry' must be an integer.")

        crunchbase_data = pd.read_pickle(file_path)

        # repalce 'null' with NaN
        crunchbase_data = crunchbase_data.replace('null', np.nan)

        # drop rows with NaN in Crunch_page or Country
        crunchbase_data = crunchbase_data.dropna(axis=0, subset=['Crunch_page'])
        crunchbase_data = crunchbase_data.dropna(axis=0, subset=['Country'])
        crunchbase_data.reset_index(inplace=True, drop=True)

        # add a column 'Social' with 0, 1, 2, 3 showing the number of active social profile pages
        if social_make:
            temp = crunchbase_data[['Facebook', 'Twitter', 'LinkedIn']]
            crunchbase_data['Social'] = 3 - temp.isnull().sum(axis=1)
            # rearrange the columns order
            crunchbase_data = crunchbase_data[['Name', 'Country', 'City', 'Region', 'URL',
                                               'Social', 'Facebook', 'Twitter', 'LinkedIn',
                                               'Crunch_page', 'Description']]

        # keep those companies belonging to countries with at least 'least_num_percountry' registered companies
        if least_num_percountry:
            count_countries = crunchbase_data.groupby('Country')[['Name']].count()
            count_countries.rename(columns={'Name': 'Companies'}, inplace=True)
            crunchbase_data = pd.merge(crunchbase_data, count_countries,
                                       how='left', left_on='Country', right_on='Country')
            crunchbase_data = crunchbase_data[crunchbase_data['Companies'] >= least_num_percountry]
            crunchbase_data.drop('Companies', axis=1, inplace=True)

        # drop some columns
        if not country_keep:
            crunchbase_data.drop('Country', axis=1, inplace=True)
        if not city_keep:
            crunchbase_data.drop('City', axis=1, inplace=True)
        if not region_keep:
            crunchbase_data.drop('Region', axis=1, inplace=True)
        if not url_keep:
            crunchbase_data.drop('URL', axis=1, inplace=True)
        if not facebook_keep:
            crunchbase_data.drop('Facebook', axis=1, inplace=True)
        if not twitter_keep:
            crunchbase_data.drop('Twitter', axis=1, inplace=True)
        if not linkedIn_keep:
            crunchbase_data.drop('LinkedIn', axis=1, inplace=True)
        if not crunchpage_keep:
            crunchbase_data.drop('Crunch_page', axis=1, inplace=True)
        if not description_keep:
            crunchbase_data.drop('Description', axis=1, inplace=True)

        if pickle:
            if os.path.isdir(dest_pickle):
                path = dest_pickle + '/crunchbase_odm_clean.pkl'
                crunchbase_data.to_pickle(path)
                print("The clean dataset is pickled at '" + path + "'" )
            else:
                print("Cannot pickle it, as the destination path doesn't exist")

        return crunchbase_data

#------------- END: A Class to scrap the Crunchbase Open Data Map (ODM) -------------#



#######################################################################################
#------------- START: A Class to scrape the Companies Pages on Cruncbase -------------#
class scrape_crunchbase_profiles:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        #self.driver = webdriver.Chrome(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(executable_path=
                                       'D:\Python Projects & Learning\Startups Success Prediction App\scrap-data\chromedriver.exe')
        self.info_kind = ['Categories', 'Founded', 'Size', 'Operating Status', 'IPO Status', 'Type']
        self.login()

    def login(self):
        # navigate to the sign-in page
        self.driver.get('https://www.crunchbase.com/login')
        sleep(5)

        # locate email form by_id
        username = self.driver.find_element_by_xpath('//*[@type="email"]')

        # send_keys() to simulate key strokes for username
        username.send_keys(self.username)
        sleep(5)

        # locate password form by_id
        password = self.driver.find_element_by_xpath('//*[@type="password"]')

        # send_keys() to simulate key strokes for password
        password.send_keys(self.password)
        sleep(5)

        # locate submit button by_xpath
        log_in_button = self.driver.find_element_by_xpath('//*[@type="submit"]')

        # .click() to mimic button click
        log_in_button.click()
        sleep(10)

    def quit(self):
        self.driver.quit()

    def scrape_single_overview(self, url):
        url = 'https://www.crunchbase.com/' + url
        USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
        req = Request(url, headers={'User-Agent': USER_AGENT})
        u = urlopen(req)
        page_html = u.read()
        u.close()

        page_soup = soup(page_html, 'html.parser')
        founded_on_html = page_soup.find_all("span", {
            "class": "component--field-formatter field-type-date_precision ng-star-inserted"})
        status_html = page_soup.find_all("span", {
            "class": "component--field-formatter field-type-enum ng-star-inserted"})
        founded_date = 'null'
        status = 'null'
        if founded_on_html:
            founded_date = founded_on_html[0].text.strip()
        if status_html:
            status = status_html[0].text.strip()
        return [founded_date, status]

#------------- END: A Class to scrape the Companies Pages on Cruncbase -------------#
#######################################################################################
