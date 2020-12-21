# PRDemoAnalysis
* Downloads & Parses Project Reality Tracker files (much of the parsing code comes from [Mineral](https://github.com/WouterJansen/PRDemoStatsParser))
* Creates a sqlite3 database to contain the information gathered from the files
* Uses this data for a dashboard made with Dash for further analysis 

[Here](https://pr-analysis.herokuapp.com/) is the link for the dash board.

## Files Included
* ```ap.py``` This is the code for the dashboard in with Dash
* ```harvest_demos.py``` This code downloads PR Tracker files from several popular servers, parses them and then loads them into a SQLite3 database.
* ```map_modes_tickets.csv``` Spreadsheet listing which teams play for each map, mode and layer.
* ```parse_one.py``` Parses a single tracker. Used in ```harvest_demos.py```. The code here is mostly from [here](https://github.com/WouterJansen/PRDemoStatsParser), but was changed to Python 3, and to work with newer versions of PR.
* ```pr.db``` The database from trackers that have been collected so far. There are two tables. One that contains the most recently attempted download for each server, and another that contains all of the data gathered from the parsed trackers.
