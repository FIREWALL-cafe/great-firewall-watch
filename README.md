# Great Firewall Watch

Automated tracking of censorship via image search results, for the [Firewall Cafe](https://firewallcafe.com/) project.

The scraper is designed to be called by a regular cron job, making its way through a list of terms to be searched on Google and Baidu. It relies on DigitalOcean spaces for the term list, as well as outputting logs and storing images.

## Installing and deploying

To install and run, clone the repository and install via pip (preferably in a virtual environment): 

`pip install -r requirements.txt`

This was written with Python 3.8 and should be compatible with all versions of Python 3, but hasn't been tested extensively. 

The two other major dependencies for this project are DigitalOcean Spaces and the Firewall Cafe translation back end, babelfish. For the first, you'll need to set up a config file detailing the Spaces bucket name and region, as well as your DO access key and ID. If you have access to babelfish, you'll need to put the babelfish key ID into the config file. If you don't, you'll need to rewrite translate.py to use another translation service (or just do it manually when you put together your termlist). 

Make sure this is in the crontab:

`@hourly bash ~/great-firewall-watch/job.sh`

Replace the folder location with wherever the repo is located, and make sure your config file is filled out and the virtual environment is where the code expects it to be.

## Using the scraper

### Uploading a new list of terms

The term set is formatted as an Excel file (.xlsx format) with two columns, `english` and `chinese`, where each row is a word translated into both languages. The file should be named `termlist.xlsx` and uploaded to the DigitalOcean Space root directory. When uploading it, make sure it is marked as Public. You can leave cells blank and the scraper will do its best to translate the terms, relying on the `babelfish.firewallcafe.com/translate` endpoint, but some words might not successfully translate (in which case they'll be skipped until next time the scraper is run). The current max size for a term list is 4800 rows. 

### Running the scraper

The server is configured (in a cron job) to run the scraper once per day, which means each word in the term list is searched once per day on each search engine, in English for Google and Chinese for Baidu. 

### Getting results

Each time the scraper is run, it will generate a metadata JSON file for both Google and Baidu with the term, timestamp, and a list of image URLs. These JSON files are all stored in the `search_results` on the DO Space. It will then save a number of those top images into a folder, `images/<search engine>/<term>`. So, if we were searching for "kitten", the images for that search would be stored in `images/google/kitten` and `images/baidu/kitten` (the English word is used for both search engines). The date the image is from is contained in the file name. 

## Scraping method

The scraper relies on the simple `requests` library to get the pages from Google and Baidu, and then BeautifulSoup to extract the metadata from that HTML blob. By necessity, this means assuming that the pages returned by those respective search engines won't change in a way that makes the scraper fail. 

The default behavior of the scraper is to query a maximum of 200 requests per hour to each search engine, adding a bit of random jitter to the time between requests. Not much effort is put into hiding that this is a bot making these requests, with the assumption being that the number of overall requests is small.  

## Modules

**scrape.py**: the main interface to the scraper.

**config.json**: specifies where to find the DigitalOcean Space, as well as the access keys.

**storage**: Interfaces with APIs, currently not really being used.

**spaces_interface.py**: used for reading and writing files to the Space.

**translate.py**: handles English <=> Mandarin translation.