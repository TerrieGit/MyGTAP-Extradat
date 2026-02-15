# Here are some functions used to extract, fill and aggregated World Bank data to prepare it for use with GTAP.
# To call this file in the python program use one of the following
#          import DataFunctions
#          import DataFunctions as XX (e.g., import DataFunctions as DF)

# You will also need to install some python programs:
#      pip install imfdatapy
#      pip install wbgapi
# and import them:
#      import imfdatapy imf
#      import wbgapi wb

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

    import wbgapi as wb
    import pandas as pd
    
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

    import wbgapi as wb
    import pandas as pd

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

    import pandas as pd

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
    df = df.dropna(how='all')

    dftype = df[df['BOPAcct'] == BOPType]
    
    dftype = dftype.drop(['SERIES_CODE','BOPAcct','D1','Currency','FREQ'], axis=1)

    dftype.info()
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
    import pandas as pd
    
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
    import pandas as pd

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

    return Paid1, Rec1, scale

# This function takes a dataframe and aggregates it using a mapping file.  This is used when aggregatingto the GTAP database.

def DatAgg(df, mappingfile):
    import pandas as pd
    
    mappings = pd.read_excel(mappingfile, sheet_name="Sheet1")
    mappings = mappings.drop(['longnames'], axis=1, errors='ignore')
    
    df = df.merge(mappings, on='economy', how="left", sort=False)
    
    agg = df.groupby('Regions').sum()
    agg = agg.drop(['economy'], axis=1)

    agg = agg.fillna(0)

    Order = pd.read_excel(mappingfile, sheet_name="Sheet2")

    agg = agg.reindex(Order['Regions'])
    
    return agg
