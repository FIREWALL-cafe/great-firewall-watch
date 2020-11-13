# Great Firewall Watch

Automated tracking of censorship via image search results, for the [Firewall Cafe](https://firewallcafe.com/) project.

The scraper is designed to be called by a regular cron job, making its way through a list of terms to be searched on Google and Baidu. It relies on DigitalOcean spaces for the term list, as well as outputting logs and storing images.

## Using the scraper

TODO: how to update search terms, read logs, and collect image sets

## Modules

**scrape.py**: the main interface to the scraper.

**config.json**: specifies where to find the DigitalOcean Space, as well as the access keys.

**storage**: Interfaces with APIs, currently not really being used.

**spaces_interface.py**: used for reading and writing files to the Space. TODO: might want to move the machine_translate function to somewhere else.

**translate.py**: handles English <=> Mandarin translation. TODO: update to use with Firewall Cafe's babelfish translation.
