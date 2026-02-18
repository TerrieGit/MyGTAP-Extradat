# MyGTAP-Extradat
MyGTAP Python code for preparing Extradat.har data for relevant year and version.

This is a Python program intended to help you construct Extradat.har for the MyGTAP mulitple household and single household programs.
Extradat.har must be updated with each new version of the GTAP database and/or year. Updates include updating the year and the mapping file.

To Run:
Use pip -m install requirements.txt
Then run the following Jupyter lab file: MyGTAPextra.ipynb
This will call any relevant excel files and functions in DataFunctions.py.

Issues:
1. can we bring down IMF data using API?  Currently use a downloaded excel file of compensation of employees 
2. TWN data is inputed separately - Data on GDP and Population are unavailable from the World Bank website and therefore must be entered mannually for all years.  
3. Currently the aggregated data is sent to an excel file.  The data then needs to be copied manually into the ExtraDat.har file used in MyGTAP.

Terms and conditions are located in Terms and Condition on the use and supply of the MyGTAP Framework.pdf
