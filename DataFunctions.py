# these programs require the following
import pandas as pd
import wbgapi as wb
import openpyxl

# Here are some functions used to extract, fill and aggregated World Bank data to prepare it for use with GTAP.
# To call this file in the python program use one of the following
#          import DataFunctions
#          import DataFunctions as XX (e.g., import DataFunctions as DF)

def GetDatWBTS(WBcode,Year): 
# This function obtains time series data from the world bank - all data after a particular year 
# To run the function: 
#          DataFunction.GetDatWBTS('WBcode',Year) (e.g., DataFunction.GetDatWBTS('NY.GDP.MKTP.KD',2015))
#    Parameters
#      WBcode : str or list-like. World Bank indicator code accepted by wbgapi. It is the world bank data indicator code: 
#               e.g., NY.GDP.MKTP.KD is GDP in constrant US dollars 
#               To find codes you can use the search command: 
#                 wb.search('XXX') (e.g., wb.search('primary income'))
#     year : the year from which you obtain data for that year and after    

#    Returns a pandas.DataFrame

    df = wb.data.DataFrame(WBcode,index='economy')
    df = pd.DataFrame(df)
    
    df = df.interpolate(method='linear',axis=1)
    
    df.columns = df.columns.astype(str).str.replace(r'^YR', '', regex=True)
    cols_to_drop = [
        col for col in df.columns
            if col.isdigit() and int(col) < Year
    ]
    df = df.drop(columns=cols_to_drop)
    df = df.dropna(how='all')

    df.info()
    return df

def GetDatWB(WBcode, years):
# This function retrieve World Bank data and keeps multiple years.
# To run the function: 
#          DataFunction.GetDatWB('WBcode',[Year1,Years2]) (e.g., DataFunction.GetDatWB('NY.GDP.MKTP.KD',[2015, 2023]))
#    Parameters
#      WBcode : str or list-like. World Bank indicator code accepted by wbgapi. It is the world bank data indicator code: 
#               e.g., NY.GDP.MKTP.KD is GDP in constrant US dollars (2015 dollars at time of writing)
#               To find codes you can use the search command: 
#                 wb.search('XXX') (e.g., wb.search('primary income'))
#      years : tuple/list [y1, y2, y3, ...] -> explicit list of years to keep.  

#    Returns pandas.DataFrame

    df = wb.data.DataFrame(WBcode, index='economy')
    df = pd.DataFrame(df)

    df = df.interpolate(method='linear', axis=1)

    df.columns = df.columns.astype(str).str.replace(r'^YR', '', regex=True)
    years = [str(y) for y in years]
    df = df[years]

    df = df.dropna(how='all')

    df.info()
    return df

def GetDatIMFex(filename, indicator, BOPType, years):
# This function retrieves data from excel file from IMF excel file.  It is meant to deal with BoPS data where there is data for payments and receipts by country.
# It takes from an excel file as I was unable to get the IMF API to work
# To run the function: 
#          DataFunction.GetDatIMFex(filename, indicator, BOPType, years]) 
# e.g., DataFunction.GetDatIMFex(filename = 'dataset_2026-02-11WComp.xlsx', indicator = 'Compensation of employees', BOPType = 'DB_T', years = [year]))
#    Parameters
#      filename : name of excel file
#      indicator : longname in file for the indicator needed
#      BOPType : debit (DB_T) or credit (CD_T)
#      years : tuple/list [y1, y2, y3, ...] -> explicit list of years to keep

#    Returns pandas.DataFrame

    df = pd.read_excel(filename)

    df = df.set_index('SERIES_CODE')
    df = df[df['INDICATOR'] == indicator]

    df.columns = df.columns.astype(str).str.replace(r'^YR', '', regex=True)

    df.columns = df.columns.map(str)
    year_cols = [y for y in df.columns if y.isdigit()]
    year_cols = sorted(year_cols)
    
    df = df[year_cols].interpolate(method='linear', axis=1)
    years = [str(y) for y in years]

    #IMF data in millions 
    df = df[years]*1000000

    df = df.reset_index(names = "SERIES_CODE")
    df[["economy", "BOPAcct", "D1", "Currency", "FREQ"]] = df["SERIES_CODE"].str.split(".", expand=True)
    df = df.set_index('economy')

    dftype = df[df['BOPAcct'] == BOPType]
    
    dftype = dftype.drop(['SERIES_CODE','BOPAcct','D1','Currency','FREQ'], axis=1)

    dftype.info()
    dftype = dftype.dropna(how='all')
    
    return dftype

# This function takes a dataframe and fills missing values using using aggregate ratios obtained using a mapping file.
# For instance, missing remittances data are filled using remittance / GDP (fill) ratios 
# for aggregate regions to which the country is mapped. 
# e.g., AggFill('RemDat', 'mapping.xlsx', 'GDP')
# df is the dataframe containg data with missing data and a column lablled fill which is used to fill the missing data.
# Mapping file for aggregates
# fill is the column used to fill.
# You might use this to fill remittances where missing data is filled using remittances relative to GDP (fill) of the region
# You might use this to fill labor where missing data is filled using labor relative to POP (fill) of the region

def DatFill(df, mappingfile, fill):
    
    mappings = pd.read_excel(mappingfile)
    mappings = mappings.drop(['longnames'], axis=1, errors='ignore')

    datframes = [fill, df]
    df = pd.concat(datframes, axis=1)
    df.columns = ['fill', 'df']    

    df = df.dropna(subset=['fill'])
    df = df.merge(mappings, on='economy', how="left")
    df = df.dropna(subset=['Regions'])
    df = df.set_index('economy')
    
    df2agg = df.dropna(how='any')
    
    agg = df2agg.groupby('Regions').sum()

    columns_to_fix = agg.columns.drop('fill')
    agg[columns_to_fix] = agg[columns_to_fix].div(agg['fill'], axis='index')    
    agg = agg.drop(['fill'], axis=1)

    dffill = df.loc[:,['Regions','fill']]
    dffill = dffill.reset_index().merge(agg, on='Regions', how="left")
    dffill = dffill.set_index('economy')
    dffill = dffill.drop(['Regions'], axis=1)
    dffill[columns_to_fix] = dffill[columns_to_fix].multiply(dffill['fill'],axis='index')
    
    df[columns_to_fix] = df[columns_to_fix].fillna(dffill[columns_to_fix])
    df = df.drop(['Regions'], axis=1)
    df = df.drop(['fill'], axis=1)
        
    return df

# This function takes two dataframe from IMF data - paid and received and fills missing values using using aggregate ratios obtained using a mapping file 
# and then ensures total paid equals total received across all countries

def DatFillEq(Paid, Rec, mappingfile, fill):

    mappings = pd.read_excel(mappingfile)
    mappings = mappings.drop(['longnames'], axis=1, errors='ignore')

    datframes = [fill, Paid, Rec]
    df = pd.concat(datframes, axis=1)
    df.columns = ['fill', 'Paid', 'Rec']    
    
    df = df.dropna(subset=['fill'])
    df = df.merge(mappings, on='economy', how="left")
    df = df.dropna(subset=['Regions'])
    df = df.set_index('economy')
    
    df2agg = df.dropna(how='any')
    
    agg = df2agg.groupby('Regions').sum()

    columns_to_fix = agg.columns.drop('fill')
    agg[columns_to_fix] = agg[columns_to_fix].div(agg['fill'], axis='index')    
    agg = agg.drop(['fill'], axis=1)

    dffill = df.loc[:,['Regions','fill']]
    dffill = dffill.reset_index().merge(agg, on='Regions', how="left")
    dffill = dffill.set_index('economy')
    dffill = dffill.drop(['Regions'], axis=1)
    dffill[columns_to_fix] = dffill[columns_to_fix].multiply(dffill['fill'],axis='index')

    df[columns_to_fix] = df[columns_to_fix].fillna(dffill[columns_to_fix])
    df = df.drop(['Regions'], axis=1)

    scale = df.loc[:,'Paid'].sum()/df.loc[:,'Rec'].sum() 
    scale1 = ((df.loc[:,'Paid'].sum() + df.loc[:,'Rec'].sum())/2)/df.loc[:,'Paid'].sum() 
    scale2 = ((df.loc[:,'Paid'].sum() + df.loc[:,'Rec'].sum())/2)/df.loc[:,'Rec'].sum() 

    df['Paid'] = df['Paid'] * scale1
    df['Rec'] = df['Rec'] * scale2

    Paid1 = df.drop(['fill','Rec'], axis=1) 
    Rec1 = df.drop(['fill','Paid'], axis=1) 

    Paid1[Paid1 < 0] = 0    
    Rec1[Rec1 < 0] = 0    
    
    return Paid1, Rec1, scale

# This function takes a dataframe and aggregates it using a mapping file.  This is used when aggregatingto the GTAP database.

def DatAgg(df, version):
    
    mappings = pd.read_excel('GTAPMap.xlsx', sheet_name = f"{version}_map")
    mappings = mappings.drop(['longnames'], axis=1, errors='ignore')
    
    df = df.merge(mappings, on='economy', how="left", sort=False)
    
    agg = df.groupby('Regions').sum()
    agg = agg.drop(['economy'], axis=1)

    Order = pd.read_excel('GTAPMap.xlsx', sheet_name = f"{version}_set")

    agg = agg.reindex(Order['Regions'])

    agg = agg/1000000
    agg = agg.fillna(0)
    agg = agg.replace('', 0)
    
    return agg

def MyGTAPConstruct(year,version):
    # The requirements to run this program are listed in requirements.txt. Before running this file you should:
    # 1. create a virtual environment 
    # 2. install the required programs from the requirements.txt file: py -m pip install -r requirements.txt. 

    # This program also refers to an number of sub programs provided above
    # This files contains the following functions
    #     GetDatWB(WBcode, years) - extracts data from World Bank using code and year/s. This is used the get data like GDP, remittances etc
    #     GetDatIMFex(filename, indicator, BOPType, years) - extracts receipts and payments from IMF Balance of payments data downloaded into an excel (e.g., workers compensation).
    #         IMF does have an API but could not get it to work
    #     DatFill(df, mappingfile, fill) - fills a dataframe (df) using other data fill (e.g., fill remittances using GDP).
    #     DatFillEq(Paid, Rec, mappingfile, fill) - fills two data frames and ensures they are equal.  For instance remittances 
    #         paid andreceived by country are filled using a data series named fill and are also scaled to ensure payments equal receipts. 
    #         Note this function has 3 outputs - updated payments, receipts and the scale.  The closer scale is to 1 the less scaling done to make sure payments equal receipts.

    # Gets POP from World Bank API
    POP = GetDatWB('SP.POP.TOTL',[year])

    # Gets GDP from World Bank API
    GDP = GetDatWB('NY.GDP.MKTP.CD',[year])

    # Fill Taiwan's data for year (need to update if update year - can usually find in google) 
    TWNdata = {
        2004: (346900000000, 22700000),
        2007: (406900000000, 22958000),
        2011: (484000000000, 23268760),
        2014: (535300000000, 23491977),
        2017: (591700000000, 23674547),
        2019: (613510000000, 23773881),
        2023: (756590000000, 23424442),
    }
    if year in TWNdata:
        GDP.loc['TWN'], POP.loc['TWN'] = TWNdata[year]

    # Fill GDP so as to avoid missing tiny countries
    GDP = DatFill(GDP, 'Mappings.xlsx', POP)

    # Gets Worker's compensation payments for IMF excel file
    WCompPaid = GetDatIMFex('dataset_2026-02-17T23_01_53.772380157Z_DEFAULT_INTEGRATION_IMF.STA_BOP_21.0.0.xlsx', 'Compensation of employees', 'DB_T', [year])

    # Gets Worker's compensation payments for IMF excel file
    WCompRec = GetDatIMFex('dataset_2026-02-17T23_01_53.772380157Z_DEFAULT_INTEGRATION_IMF.STA_BOP_21.0.0.xlsx', 'Compensation of employees', 'CD_T', [year])

    # Fills workers compensation data and ensure receipts equal payments
    WCompPaid, WCompRec, scale = DatFillEq(WCompPaid, WCompRec, 'Mappings.xlsx', GDP)
    # Print how much scaling was required
    print("This is how much scaling was required to equalize receipts and payments globally (1 means no scaling):", scale)

    # Aggregate to GTAP using mapping file
    WCompPaid = DatAgg(WCompPaid,version)
    WCompRec = DatAgg(WCompRec,version)

    # Gets Primary income from World Bank API
    PIPaid = GetDatWB('BM.GSR.FCTY.CD',[year]) 

    # Gets Primary income from World Bank API
    PIRec = GetDatWB('BX.GSR.FCTY.CD',[year]) 

    # Fills primary income data and ensure receipts equal payments
    PIPaid, PIRec, scale = DatFillEq(PIPaid, PIRec, 'Mappings.xlsx',GDP)
    # Print how much scaling was required
    print("This is how much scaling was required to equalize receipts and payments globally (1 means no scaling):", scale)

    # Aggregate to GTAP using mapping file
    PIPaid = DatAgg(PIPaid,version)
    PIRec = DatAgg(PIRec,version)

    # Gets Remittances from World Bank API
    RemRec = GetDatWB('BX.TRF.PWKR.CD.DT',[year])

    # Gets Remittances from World Bank API
    RemPaid = GetDatWB('BM.TRF.PWKR.CD.DT',[year])

    # Fills remittances data and ensure receipts equal payments
    RemPaid, RemRec, scale = DatFillEq(RemPaid, RemRec, 'Mappings.xlsx',GDP)
    # Print how much scaling was required
    print("This is how much scaling was required to equalize receipts and payments globally (1 means no scaling):", scale)

    # Aggregate to GTAP using mapping file
    RemPaid = DatAgg(RemPaid,version)
    RemRec = DatAgg(RemRec,version)

    # Gets Aid from World Bank API
    AidRec = GetDatWB('DT.ODA.ODAT.CD',[year])

    # Gets Aid from World Bank API
    AidPaid = GetDatWB('DC.ODA.TOTL.CD',[year])

    # Fills aid data and ensure receipts equal payments
    AidPaid, AidRec, scale = DatFillEq(AidPaid, AidRec, 'Mappings.xlsx',GDP)
    # Print how much scaling was required
    print("This is how much scaling was required to equalize receipts and payments globally (1 means no scaling):", scale)

    # Aggregate to GTAP using mapping file
    AidPaid = DatAgg(AidPaid,version)
    AidRec = DatAgg(AidRec,version)

    # Note we want foreign income related to workers and capital - Primary income includes workers compensation and foreign investment - hence workers compensation must be subtracted.
    InvPaid = PIPaid - WCompPaid
    InvRec = PIRec - WCompRec

    # Write data to excel
    filename = f"MyGTAPoutput_{version}_{year}.xlsx"
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        RemPaid.to_excel(writer, sheet_name="RemPaid", index=True)
        RemRec.to_excel(writer, sheet_name="RemRec", index=True)
        InvPaid.to_excel(writer, sheet_name="InvPaid", index=True)
        InvRec.to_excel(writer, sheet_name="InvRec", index=True)
        AidPaid.to_excel(writer, sheet_name="AidPaid", index=True)
        AidRec.to_excel(writer, sheet_name="AidRec", index=True)

    return print(f"COMPLETED: see {filename} containing new information for MyGTAP {version} and year {year}")