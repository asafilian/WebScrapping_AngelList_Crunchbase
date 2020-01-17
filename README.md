# WebScrapping (AngelList, Crunchbase)
In this repository, you can find some Python classes showing how to scrape AngelList (https://angel.co/) and Crunchbase (https://www.crunchbase.com/).


## Crunchbase
I have used the Crunchbase API, the free one, to get the general information about companies registered on Crunchbase. I also show how to scrape the Crunchbase profile page for a given company to get more information. To this end, you first need to let the class have your username and password to let it login through the app. This is because you cannot get access to the profile pages of companies without siging in. Again, this could be illegal, and you want to make sure that you already got permission to scrape companies profile pages via your app. 

## AngleList
Scrapping AngleList is bit more tricky. You first need to scrape the general information about companies from the ‘companies’ page by providing some search keywords, automatically click on the ‘More’ button, and so on. To avoid being blocked, you need to make the app sleep between scrapping two pages. Moreover, it doesn’t show more than 400 results per search. So, you need to filter out your search so that you can get as mush data as you can from your scrapping. Then, to get more information about each company (e.g., fundraising rounds, social media pages, size, etc), you need to scrape its profile page on Angel. I have shown how to do so in the corresponding class. 
