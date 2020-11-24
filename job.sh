#! /bin/bash
date
cd ~
source environments/firewall/bin/activate
cd great-firewall-watch
python scrape.py
