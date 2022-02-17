import requests
from bs4 import BeautifulSoup
import sys
import sqlite3
import pickle as pkl
import argparse
from API_KEY import API_KEY
import time
URL_ADD = "https://api.domain.com.au/v1/addressLocators?searchLevel=Suburb&suburb={}&state=NSW&postcode={}"
URL_PERF = "https://api.domain.com.au/v2/suburbPerformanceStatistics/{}/{}/{}?propertyCategory={}&bedrooms={}&periodSize={}&startingPeriodRelativeToCurrent={}&totalPeriods={}"
URL_DEM = "https://api.domain.com.au/v2/demographics/{}/{}/{}?types=AgeGroupOfPopulation%2CCountryOfBirth%2CNatureOfOccupancy%2COccupation%2CGeographicalPopulation%2CGeographicalPopulation%2CEducationAttendance%2CHousingLoanRepayment%2CMaritalStatus%2CReligion%2CTransportToWork%2CFamilyComposition%2CHouseholdIncome%2CRent%2CLabourForceStatus&year={}"
state_map = {'Sydney':'NSW', 'Melbourne':'VIC'}

def get_suburbs(city):
    if(city=='Sydney'):
        URL = "https://www.intosydneydirectory.com.au/sydney-postcodes.php"
        HTML = requests.get(URL)
        if(not HTML.status_code==200):
            sys.exit(URL + " is not available\n", "RESPONSE " + HTML.status_code)
        soup = BeautifulSoup(HTML.text,'html.parser')
        table = soup.find('table') 
        rows = table.findAll('tr')
        data = [[cell.text for cell in row("td")] for row in rows]
        del data[0]
        return data
    elif(city=='Melbourne'):
        URL = "https://www.homely.com.au/find-suburb-by-region/melbourne-greater-victoria"
        HTML = requests.get(URL)
        if(not HTML.status_code==200):
            sys.exit(URL + " is not available\n", "RESPONSE " + HTML.status_code)
        soup = BeautifulSoup(HTML.text,'html.parser')
        allList  = soup.find("div", "col-group")
        links = allList.find_all("a")
        Msubs = []
        for link in links:
            Msubs.append(link.get_text())
        URL = "http://www.justweb.com.au/post-code/melbourne-postalcodes.html"
        HTML = requests.get(URL)
        if(not HTML.status_code==200):
            sys.exit(URL + " is not available\n", "RESPONSE " + HTML.status_code)
        soup = BeautifulSoup(HTML.text,'html.parser')
        allList = soup.find_all("select")
        subDict = {}
        for entry in allList[1].find_all("option"):
            txt = entry.get_text()
            code = txt[-4:]
            sub = txt[:-4].strip()
            subDict[sub]=code
        MelSubs = []
        for sub in Msubs:
            try:
                MelSubs.append((sub,subDict[sub]))
            except:
                print("No postcode data for {}".format(sub)) 
                continue
        return MelSubs
    else:
        sys.exit("No implementation for {}".format(city))

def create_table_suburbs(name):
    query = '''DROP TABLE IF EXISTS {}'''.format(name)
    sql.execute(query)
    query = '''CREATE TABLE  {} (
        suburb_name TEXT,
        postcode INTEGER NOT NULL
        ); '''.format(name)

    sql.execute(query)
    print("TABLE {} created ".format(name)) 


def insert_data_suburbs(name,data):
    query = '''INSERT INTO {} VALUES (?,?)'''.format(name)
    sql.executemany(query,data)
    print('DATA INSERTED IN TABLE {}'.format(name))

def drop_unknown_suburbs(name):
    query = '''DELETE FROM {} WHERE ID = -1;'''.format(name)
    sql.execute(query)
    conn.commit()

def create_table_performance(name):

    query = '''DROP TABLE IF EXISTS {};'''.format(name)
    sql.execute(query)
    query = '''CREATE TABLE {} (
        state TEXT,
        suburb TEXT,
        postcode INTEGER,
        type TEXT,
        bedrooms INTEGER,
        year INTEGER,
        month INTEGER,
        medianSoldPrice REAL,
        numberSold INTEGER, 
        highestSoldPrice REAL,
        lowestSoldPrice REAL,
        FifthPercentileSoldPrice REAL,
        TwentyFivePercentileSoldPrice REAL,
        SeventyFivePercentileSoldPrice REAL,
        NintyFivePercentileSoldPrice REAL,
        medianSaleListingPrice REAL,
        numberSaleListing INTEGER,
        highestSaleListingPrice REAL,
        lowestSaleListingPrice REAL,
        auctionNumberAuctioned INTEGER,
        auctionNumberSold INTEGER,
        auctionNumberWithdrawn INTEGER,
        daysOnMarket INTEGER,
        discountPercentage REAL,
        medianRentListingPrice REAL,
        numberRentListing REAL,
        highestRentListingPrice REAL,
        lowestRentListingPrice REAL
        );'''.format(name)

    sql.execute(query)

def create_table_demographic(name):
    query = '''DROP TABLE IF EXISTS {};'''.format(name)
    sql.execute(query)
    query='''CREATE TABLE {} (
        suburb TEXT,
        year INTEGER,
        category TEXT,
        subcategory TEXT,
        value REAL,
        composition TEXT);'''.format(name)
    sql.execute(query)

def insert_data_suburbs_performance(name,data):
    query = '''INSERT INTO {} VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''.format(name)
    sql.executemany(query,data)
    print('DATA INSERTED IN TABLE {}'.format(name))

def get_suburb_performance(state,suburb,postcode,category,bedrooms,periodSize,stPeriod,totalPeriods):
    URL = URL_PERF.format(state,suburb,postcode,category,bedrooms,periodSize,stPeriod,totalPeriods)
    try:
        response = requests.get(URL,headers = {"X-Api-Key": API_KEY})
    except:
        print("Cannot get response from API")
        return [], []
    if(not response.status_code == 200):
        print(response.status_code)
        return [], response.status_code
    try:
        data = response.json()
    except:
        print("JSON cannot be loaded")
        return [], response.status_code
    outdata = []
    for info in data['series']['seriesInfo']:
        base = [data['header']['state'],suburb, postcode, category, bedrooms, info['year'], info['month']]
        for vals in info['values'].values():
            base.append(vals)
        outdata.append(base)
    return outdata, response.status_code

def get_suburb_demographic(state,suburb,postcode,year):
    URL = URL_DEM.format(state,suburb,postcode, year)
    response = requests.get(URL,headers = {"X-Api-Key": API_KEY})
    if(not response.status_code == 200):
        print(response.status_code)
        return [], response.status_code

    data = response.json()
    outdata =[]
    for entry in data["demographics"]:
        typ = entry['type']
        for items in entry['items']:
            base = [suburb, year, typ, items['label'],items['value'],items['composition']]
            outdata.append(base)
    return outdata, response.status_code

def insert_suburb_demographic(state, year, query_points, table):
    idx=0
    for point in query_points:
        print("PROCESSING SUBURB {} ".format(point[0]))
        data, code = get_suburb_demographic(state, point[0], point[1], year)
        if(not code==200):
            if(code==429):
                print("Quota Exceeded")
                return idx
            idx=idx+1
            continue
        query = '''INSERT INTO {} VALUES (?,?,?,?,?,?) '''.format(table)
        sql.executemany(query,data)
        print("DATA INSERTED FOR {}".format(point[0]))
        conn.commit()
        idx=idx+1
    return idx

def insert_suburb_performance_table(city,query_points,table,periodSize,stPeriod,totalPeriods):
    state = state_map[city]
    idx=0
    for query in query_points:
            print("PROCESSING SUBURB {} for {} Bedroom {}".format(query[0],query[2],query[3]))
            data, code = get_suburb_performance(state,query[0],query[1],query[3],query[2],periodSize,stPeriod,totalPeriods)
            if(not code==200):
                if(code==429):
                    print("Quota Exceeded")
                    return idx
                idx=idx+1
                continue
            insert_data_suburbs_performance(table,data)
            idx=idx+1
            conn.commit()
    return idx

def generate_all_combinations(bedrooms, types, city):
    #Have to make a list and save to file for all combinations I want
    # Doing this because I am only allowed 500 API calls per day
    # An easy way of keeping track what has been done and what not
    query = '''SELECT suburb_name, postcode FROM suburbs_{}'''.format(city)
    sql.execute(query)
    query_points = []
    location = sql.fetchall()
    print(bedrooms, types)
    for loc in location:
        for beds in bedrooms:
            for ty in types:
                query_points.append([loc[0],loc[1],beds,ty])
    return query_points

def generate_suburbs(city):
    #Have to make a list and save to file for all combinations I want
    # Doing this because I am only allowed 500 API calls per day
    # An easy way of keeping track what has been done and what not
    query = '''SELECT suburb_name, postcode FROM suburbs_{}'''.format(city)
    sql.execute(query)
    query_points = []
    location = sql.fetchall()
    for loc in location:
                query_points.append([loc[0],loc[1]])
    return query_points


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Get housing data for Sydney')
    parser.add_argument('--database_name',type=str,default='test.db',help="Name of sql database")
    parser.add_argument('--city',type=str,default='Sydney',help="Name of city")
    parser.add_argument('--get_suburbs',action="store_true", default=False, help='will generate table of suburbs,\
            need to do this when running the script for the first time')
    parser.add_argument('--reset_table',action="store_true", default=False, help='Delete old data and start new')
    parser.add_argument('--fill_table_performance',action="store_true", default=False)
    parser.add_argument('--fill_demographic_table',action="store_true", default=False)
    parser.add_argument('--period',type=str, default='Years', help='Years, HalfYears or Quarters')
    parser.add_argument('--num_periods',type=int, default=10, help='Number of time periods for data')
    parser.add_argument('--bedrooms',type=str, nargs='+', default=['1'])
    parser.add_argument('--type',type=str, nargs='+' ,default=['House'],help="House of Unit")
    args = parser.parse_args()
    
    conn = sqlite3.connect(args.database_name)
    sql = conn.cursor()
    
    if(args.get_suburbs):
        data = get_suburbs(args.city)
        create_table_suburbs("suburbs_"+args.city)
        insert_data_suburbs("suburbs_"+args.city,data)
        conn.commit()

    if(args.fill_demographic_table):
        tab_name = 'suburb_demographic_'+args.city
        if(args.reset_table):
            query_points = generate_suburbs(args.city)
            pkl.dump(query_points,open('query_points_{}.pkl'.format(args.city),'wb'))
            create_table_demographic(tab_name)

        query_points = pkl.load(open('query_points_{}.pkl'.format(args.city),'rb'))
        #2016 latest census
        state = state_map[args.city]
        idx=insert_suburb_demographic(state,'2016', query_points, tab_name)
        query_points = query_points[idx:]
        pkl.dump(query_points,open('query_points_{}.pkl'.format(args.city),'wb'))
        print("PROCESSED {} samples, LEFT {} samples".format(idx,len(query_points)))

        query = '''SELECT COUNT(*) FROM (select distinct * FROM {})'''.format(tab_name)
        sql.execute(query)
        print("Table {} has {} entries".format(tab_name, sql.fetchall()))

    if(args.fill_table_performance):
         tab_name = 'suburb_performance_'+args.city+'_'+args.period
         if(args.reset_table):
            print("Deleting Old Data ... ")
            query_points = generate_all_combinations(args.bedrooms,args.type, args.city)
            pkl.dump(query_points,open('query_points_{}.pkl'.format(args.city),'wb'))
            create_table_performance(tab_name)
         try:
             query_points = pkl.load(open('query_points_{}.pkl'.format(args.city),'rb'))
         except:
             query_points = generate_all_combinations(args.bedrooms,args.type, args.city)

         idx=insert_suburb_performance_table(args.city,query_points,tab_name,args.period,1,args.num_periods)    
         query_points = query_points[idx:]
         pkl.dump(query_points,open('query_points_{}.pkl'.format(args.city),'wb'))
         print("PROCESSED {} samples, LEFT {} samples".format(idx,len(query_points)))

         query = '''SELECT COUNT(*) FROM (select distinct * FROM {})'''.format(tab_name)
         sql.execute(query)
         print("Table {} has {} entries".format(tab_name, sql.fetchall()))



    conn.commit()
    conn.close()
