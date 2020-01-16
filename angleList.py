# Import the following packages

from bs4 import BeautifulSoup as soup
import pandas as pd
import numpy as np
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

#----------------- A Class To Scrape Companies ---------------------#
class scrape_angle:
    '''
    Use this class to get a dataset of companies based on your searchkeys from AngelList (https://angel.co/companies)
    1. 'Name' (name of the company)
    2. 'Type' (e.g., start-up)
    3. 'Joined' (the year when the company joined to AngelList)
    4. 'Headquarter' (e.g., Toronto)
    5. 'Market' (e.g., Marketing)
    6. 'Size' (company size, e.g., 1-10 employees)
    7. 'Funding Stage' (Pre-Seed, Seed, Series A to F, Acquired, IPO, Clsoed, Unknown, NaN)
    8. 'Raised' (total fund raised by the company)
    9. 'Website' (company's URL)
    10. 'Link' (to the company's AngleList profile page)
    11. 'Pitch' (a description provided by the owner)
    '''

    def __init__(self, driver, query=None, type=None, stage=None, location=None):
        '''
        :param driver:  A Chrome webdriver
        :param query:  Your query to seach the companies
        :param type:  The type of companies you are looking for:
                types = ['Startup', 'Private Company', 'SaaS', 'Mobile App', None]
        :param stage: The funding stage of companies in query
                stages = ['Pre-Seed','Seed', 'Series A', 'Series B', 'Series C', 'Acquired', None]
        :param location: The city where the companies in query are located
        '''
        self.driver = driver
        self.query = query
        if self.query:
            self.query = self.query.replace(' ', '+')
        self.type = type
        self.stage = stage
        self.location = location

    def get_results(self):

        url = 'https://angel.co/companies'

        if self.type:
            self.type = self.type.replace(' ', '+')
            url = url + '?company_types[]=' + self.type
            if self.stage:
                url = url + '&stage=' + self.stage
            if self.location:
                url = url + '&locations[]=' + self.location
            if self.query:
                url = url + '&keywords=' + self.query
        elif self.stage:
            url = url + '?stage=' + self.stage
            if self.location:
                url = url + '&locations[]=' + self.location
            if self.query:
                url = url + '&keywords=' + self.query
        elif self.location:
            url = url + '?locations[]=' + self.location
            if self.query:
                url = url + '&keywords=' + self.query
        elif self.query:
            url = url + '&keywords=' + self.query



        self.driver.get(url)
        time.sleep(20)

        if self.query:
            search_box = driver.find_element_by_class_name("search-box")
            search_box.click()

            input_bar = driver.find_element_by_class_name('keyword-input')
            input_bar.send_keys(self.query)
            input_bar.send_keys(Keys.ENTER)
            time.sleep(3)

        while True:
            try:
                source = driver.page_source
                load_more_button = driver.find_element_by_class_name('more')
                load_more_button.click()
                time.sleep(10)
            except:
                break

        driver.close()

        try:
            soup_lxml = soup(source, 'lxml')
            result_list = soup_lxml.find_all('div', {'class': 'results'})[0]
            results = result_list.find_all('div', {'data-_tn': 'companies/row'})
        except:
            print('Could not get results')
            return

        return results

    def parse_results(self, results):
        df = pd.DataFrame(
            columns=['Name', 'Type', 'Joined', 'Headquarter', 'Market', 'Size', 'Funding Stage', 'Raised', 'Website',
                     'Link', 'Pitch'],
            index=[0])
        for result in results[1:]:
            try:
                dic = {}
                try:
                    dic['Name'] = result.a['title']
                except:
                    dic['Name'] = None

                try:
                    dic['Type'] = result.a['data-type']
                except:
                    dic['Type'] = None

                try:
                    dic['Joined'] = result.find('div', {'data-column': 'joined'}).text.split('Joined')[1].strip()
                except:
                    dic['Joined'] = None

                try:
                    dic['Location'] = result.find('div', {'data-column': 'location'}).text.split('Location')[1].strip()
                except:
                    dic['Location'] = None

                try:
                    dic['Market'] = result.find('div', {'data-column': 'market'}).text.split('Market')[1].strip()
                except:
                    dic['Market'] = None

                try:
                    dic['Size'] = result.find('div', {'data-column': 'company_size'}).text.split()[1]
                except:
                    dic['Size'] = None

                try:
                    dic['Stage'] = result.find('div', {'data-column': 'stage'}).text.split('Stage')[1].strip()
                except:
                    dic['Stage'] = None

                try:
                    dic['Raised'] = result.find('div', {'data-column': 'raised'}).text.split('Raised')[1].strip()
                except:
                    dic['Raised'] = None

                try:
                    dic['Website'] = result.find('div', {'data-column': 'website'}).text.split()[1]
                except:
                    dic['Website'] = None

                try:
                    dic['Link'] = result.a['href']
                except:
                    dic['Link'] = None

                try:
                    dic['Pitch'] = result.find('div', {'class': 'pitch'}).text
                except:
                    dic['Pitch'] = None

                df = df.append(pd.DataFrame(dic, index=[0]), sort=True)

            except:
                pass

        df = df.reset_index(drop=True)
        return df

    def clean_dataset(self, dataset):
        dataset.drop(dataset.index[0], inplace=True)
        dataset['Pitch'] = [p.replace('\n', '') for p in dataset['Pitch']]

        dataset['Raised'] = [r.replace(',', '') for r in dataset['Raised']]
        dataset['Raised'] = [r[1:] if len(r) > 1 else r for r in dataset['Raised']]
        dataset = dataset.replace('-', np.nan)
        dataset['Raised'] = dataset['Raised'].astype('float')

        joined_split = [s.split(' ') for s in dataset['Joined']]
        dataset['Joined'] = [s[1] for s in joined_split]
        dataset['Joined'] = [s.replace('’', '20') for s in dataset['Joined']]
        dataset['Joined'] = dataset['Joined'].astype('int16')

        dataset.fillna(value=pd.np.nan, inplace=True)

        dataset.drop(columns=['Website'], inplace=True)

        dataset = dataset[['Name', 'Type', 'Joined', 'Location', 'Market', 'Size', 'Stage', 'Raised', 'Link', 'Pitch']]

        dataset.reset_index(inplace=True, drop=True)

        return dataset

    def get_companies(self):
        results = self.get_results()
        if results:
            dataset = self.parse_results(results)
            dataset = self.clean_dataset(dataset=dataset)
            return dataset


#----------------- A Class To Scrape Funding Info ---------------------#

class scrape_angle_profile_funding:
    '''
    This class will get the following features about a given company by scrapping its profile pagee:
    - First funding date
    - Latest funding date
    - Number of rounds
    - Operating status (Active/Closed)
    - Values of all funding raised
    - Dates of all funding raised
    - etc.

In the follwoing chunk, I've written a class to scrape a given company profile page to get the above information.
    '''
    def __init__(self, url_page, driver, sleeptime=2):
        '''
        :param url_page: the link to a company's AngleList profile page
        :param driver: Chrome webdriver
        :param sleeptime: in seconds
        '''
        self.url_page = url_page + '/funding'
        self.driver = driver
        self.sleeptime = sleeptime
        self.source = self.get_source()

    def get_source(self):

        self.driver.get(self.url_page)
        time.sleep(self.sleeptime)

        source = self.driver.page_source
        soup_lxml = soup(source, 'lxml')
        return soup_lxml

    def quit_source(self):
        self.driver.quit()

    def extract_status(self):
        status = 'Active'
        try:
            closed = self.source.find('span', {'class': 'styles_component__1YnyN closedFlair_a3c49 styles_red__1FvCF styles_sm__xD9Ye'})
            status = closed.text
        except:
            pass

        return status


    def get_kind_info(self):
        item_list = self.source.find_all('span', {'class': 'statName_ad44e'})
        items = []
        for item in item_list:
            try:
                items.append(item.get("data-label"))
            except:
                pass

        return items

    def get_total_raised(self):
        value_list = self.source.find_all('span', {'class': 'value_638f7'})
        try:
            total_raised = value_list[0].text
        except:
            total_raised = None

        return total_raised

    def get_number_rounds(self):
        try:
            rounds_list = self.source.find_all('div', {'class': 'metadata_8df39'})
        except:
            print("Couldn't get the number of funding rounds for " + self.url_page)
            print('------------------------------------------')
            rounds_list = []

        return len(rounds_list)



    def get_rounds_values(self):
        try:
            rounds_values = self.source.find_all('span', {'class': 'amountRaised_3c2b1'})
        except:
            rounds_values = None

        values = []
        for v in rounds_values:
            try:
                values.append(v.text)
            except:
                pass

        return values

    def get_rounds_dates(self):
        rounds_list = []
        try:
            rounds_list = self.source.find_all('div', {'class': 'metadata_8df39'})
        except:
            pass

        round_dates = []
        for item in rounds_list:
            try:
                d = item.find_all('span', {'class': 'part_318cf'})[1].text
                round_dates.append(d)
            except:
                pass

        return round_dates

    def get_rounds_stages(self):
        rounds_list = []
        try:
            rounds_list = self.source.find_all('div', {'class': 'metadata_8df39'})
        except:
            pass

        round_stages = []
        for item in rounds_list:
            try:
                s = item.find_all('span', {'class': 'part_318cf'})[0].text
                round_stages.append(s)
            except:
                pass

        return round_stages

    def get_latest_round_date(self):
        try:
            latest_date = self.get_rounds_dates()[0]
        except:
            print("Couldn't get the latest fudning date for " + self.url_page)
            print('------------------------------------------')
            latest_date = None

        return latest_date

    def get_latest_round_stage(self):
        try:
            latest_stage = self.get_rounds_stages()[0]
        except:
            print("Couldn't get the latest fudning stage for " + self.url_page)
            print('------------------------------------------')
            latest_stage = None

        return latest_stage

    def get_first_round_date(self):
        rounds_date = self.get_rounds_dates()
        try:
            first_date = rounds_date[len(rounds_date) - 1]
        except:
            print("Couldn't get the first fudning date for " + self.url_page)
            print('------------------------------------------')
            first_date = None

        return first_date


# ----------------- A Class To Scrape the main profile page ---------------------#
class scrape_angle_profile:
    '''
    This class is used to scrape the main profile pages to get the following information
    1. All Markets
    2. Social Media URLs (Twitter, LinkedIn, Facebook)
    3. Number of founders
    '''
    def __init__(self, url_page, driver, sleeptime=2):
        self.url_page = url_page
        self.driver = driver
        self.sleeptime = sleeptime
        self.source = self.get_source()

    def get_source(self):

        self.driver.get(self.url_page)
        time.sleep(self.sleeptime)

        try:
            show_more = self.driver.find_element_by_class_name("component_7ede2")
            show_more.click()
            time.sleep(2)
        except:
            print("Couldn't click on 'Show More' button")
            pass

        source = self.driver.page_source
        soup_lxml = soup(source, 'lxml')
        return soup_lxml

    def quit_source(self):
        self.driver.quit()

    def get_social(self):
        twitter = ''
        linkedin = ''
        facebook = ''

        try:
            hrefs = self.source.find_all('a', {'class': 'component_21e4d'})

            for item in hrefs:
                h = item.get('href')

                if 'twitter.com' in h:
                    if twitter == '':
                        if h != 'http://twitter.com/angellist':
                            twitter = h

                if 'facebook.com' in h:
                    if facebook == '':
                        facebook = h

                if 'linkedin.com' in h:
                    if linkedin == '':
                        linkedin = h
        except:
            pass

        return [linkedin, twitter, facebook]

    def get_all_markets(self):
        markets = ''
        try:
            markets_scraped = self.source.find_all('a', {'class': "styles_component__3BR-y styles_anchor__wiFvS"})

            markets_list = []
            for item in markets_scraped:
                if item.text not in markets_list:
                    markets_list.append(item.text)

            markets = ''
            if len(markets_list) > 0:
                markets = markets_list[0]
                for m in markets_list[1:]:
                    markets = markets + ', ' + m
        except:
            pass

        return markets

    def get_num_founders(self):
        try:
            founders = self.source.find_all('div', {'class': "component_ee038 component_64ce3 regular_8285b"})
        except:
            return 1

        return len(founders)

#---------------- EXAMPLE ----------------#
# Uncomment to see how it works

# ##----- get a dataset of comapnies -----##
#
# ### change the executable_path
# driver = webdriver.Chrome(executable_path=
#                                   'D:\Python Projects & Learning\Startups Success Prediction App\scrap-data\chromedriver.exe')
#
# obj = scrape_angle(driver=driver, stage='Seed', location='12591-Hamilton,+Ontario')
# dataset = obj.get_companies()
# driver.quit()
# ##----- get all other information about companies -----##
#
# for i in range(len(dataset)):
#     base_url = dataset.iloc[i].Link
#
#     # Scrap Funding (put if raised != 0 or stage not Null)
#     page_url = base_url + '/funding'
#     obj = scrape_angle_profile_funding(url_page=page_url, driver=driver)
#     rounds_number = obj.get_number_rounds()
#
#     latest_round_date = obj.get_latest_round_date()
#
#     first_round_date = obj.get_first_round_date()
#
#     latest_round_stage = obj.get_latest_round_stage()
#
#     ## Update the corresponding rows in the main dataset
#     dataset.at[dataset.iloc[i]['index'], 'Rounds'] = rounds_number
#     dataset.at[dataset.iloc[i]['index'], 'First Round'] = first_round_date
#     dataset.at[dataset.iloc[i]['index'], 'Latest Round'] = latest_round_date
#     if pd.isna(dataset.iloc[dataset.iloc[i]['index']].Stage):
#         dataset.at[dataset.iloc[i]['index'], 'Stage'] = latest_round_stage
#     driver.quit()
#
#     # Scrape Other info
#     page_url = base_url
#     obj = scrape_angle_profile(url_page=page_url, driver=driver)
#
#     ## Social Media
#     social_media = obj.get_social()
#
#     ## Update the corresponding rows in the main dataset
#     dataset.at[i, 'LinkedIn'] = social_media[0]
#     dataset.at[i, 'Twitter'] = social_media[1]
#     dataset.at[i, 'Facebook'] = social_media[2]
#     n = 0
#     if len(social_media[0]) > 0:
#         n = n+1
#     if len(social_media[1]) > 0:
#         n = n+1
#     if len(social_media[2]) > 0:
#         n = n+1
#
#     dataset.at[i, 'Social Media'] = n
#
#     ## get all markets
#     markets = obj.get_all_markets()
#     ## Update the corresponding rows in the main dataset
#     dataset.at[i, 'All Markets'] = markets
#
#     ## get number of founders
#     founders = obj.get_num_founders()
#     ## Update the corresponding rows in the main dataset
#     if founders > 0:
#         dataset.at[i, 'Founder'] = founders
#
#     print(format(i + 1) + ':  DONE!')
#     print()
#
#     time.sleep(3)
#
#     ## if you want to pickle, uncomment the following and change the path
#     if (i + 1) % 10 == 0:
#     #     dataset.to_pickle('datasets/angel_CA_v4.pkl')
#         print('----------------------------------')
#         print('pickled!')
#         print('----------------------------------')
#
#
# ## if you want to pickle, uncomment the following and change the path
# # dataset.to_pickle('datasets/angel_CA_v4.pkl')
# driver.quit()


