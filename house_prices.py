import requests
from bs4 import BeautifulSoup
import sys
import sqlite3
import pickle as pkl
from API_KEY import API_KEY
URL_ADD = "https://api.domain.com.au/v1/addressLocators?searchLevel=Suburb&suburb={}&state=NSW&postcode={}"
URL_PERF = "https://api.domain.com.au/v2/suburbPerformanceStatistics/NSW/{}/{}?propertyCategory={}&bedrooms={}&periodSize={}&startingPeriodRelativeToCurrent={}&totalPeriods={}"
#API_KEY = "key_ef97cf191bb88481638276f78f5a46fd"
conn = sqlite3.connect("housing.db")
sql = conn.cursor()

def get_syd_suburbs():
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

def create_table_suburbs(name):
    query = '''DROP TABLE IF EXISTS {}'''.format(name)
    sql.execute(query)
    query = '''CREATE TABLE  {} (
        suburb_name TEXT,
        state TEXT,
        postcode INTEGER NOT NULL,
        ID INTEGER NOT NULL
        ); '''.format(name)

    sql.execute(query)
    print("TABLE {} created ".format(name)) 


def insert_data_suburbs(name,data):
    query = '''INSERT INTO {} VALUES (?,?,?,?)'''.format(name)
    sql.executemany(query,data)
    print('DATA INSERTED IN TABLE {}'.format(name))

def get_suburb_code_domain(data):

    for row in data:
        URL = URL_ADD.format(row[0],row[2]) #name and postcode
        response = requests.get(URL, headers = {"X-Api-Key": API_KEY})
        outp = response.json()
        try:
            row.append(outp[0]['ids'][0]['id'])
            print("PROCESSED {}".format(row[0]))
        except:
            print(" NO RESULT FOR SUBURB {}\n".format(row[0]))
            print(outp)
            row.append(-1)

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

def insert_data_suburbs_performance(name,data):
    query = '''INSERT INTO {} VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''.format(name)
    sql.executemany(query,data)
    print('DATA INSERTED IN TABLE {}'.format(name))

def get_suburb_performance(suburb,postcode,category,bedrooms,periodSize,stPeriod,totalPeriods):
    URL = URL_PERF.format(suburb,postcode,category,bedrooms,periodSize,stPeriod,totalPeriods)
    response = requests.get(URL,headers = {"X-Api-Key": API_KEY})
    if(not response.status_code == 200):
        print(response.status_code)
        return [], response.status_code
    #print(response.json())
    data = response.json()
    outdata = []
    for info in data['series']['seriesInfo']:
        base = [data['header']['state'],suburb, postcode, category, bedrooms, info['year'], info['month']]
        for vals in info['values'].values():
            base.append(vals)
        outdata.append(base)
    return outdata, response.status_code

def insert_suburb_performance_table(query_points,table,periodSize,stPeriod,totalPeriods):
    idx=0
    for query in query_points:
            print("PROCESSING SUBURB {} for {} Bedroom {}".format(query[0],query[2],query[3]))
            data, code = get_suburb_performance(query[0],query[1],query[3],query[2],periodSize,stPeriod,totalPeriods)
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

def generate_all_combinations(bedrooms, types):
    #Have to make a list and save to file for all combinations I want
    # Doing this because I am only allowed 500 API calls per day
    # An easy way of keeping track what has been done and what not
    query = '''SELECT suburb_name, postcode FROM suburbs'''
    sql.execute(query)
    query_points = []
    location = sql.fetchall()
    for loc in location:
        for beds in bedrooms:
            for ty in types:
                query_points.append([loc[0],loc[1],beds,ty])
    return query_points


if __name__ == "__main__":

    get_subs = 0
    if(get_subs):

        data = get_syd_suburbs()
        get_suburb_code_domain(data)
        create_table_suburbs("suburbs")
        insert_data_suburbs("suburbs",data)
        print(data[0])
        conn.commit()
    
    #query_points = generate_all_combinations(['1','2','3'],['House','Unit'])
    #pkl.dump(query_points,open('query_points.pkl','wb'))
    query_points = pkl.load(open('query_points.pkl','rb'))
    print(len(query_points))
    #drop_unknown_suburbs("suburbs")

    #create_table_performance('suburb_performance_quaterly')
    idx=insert_suburb_performance_table(query_points,'suburb_performance_quaterly','Quarters',1,40)    
    query_points = query_points[idx:]
    pkl.dump(query_points,open('query_points.pkl','wb'))
    print("PROCESSED {} samples, LEFT {} samples".format(idx,len(query_points)))

    #create_table_performance('suburb_performance_quarterly')
    #insert_suburb_performance_table('suburb_performance_yearly','Quarters',1,40)    
    #query = '''SELECT suburb_name, postcode FROM suburbs WHERE suburb_name NOT IN (SELECT suburb FROM suburb_performance_yearly)'''
    query = '''SELECT COUNT(*) FROM (select distinct * FROM suburb_performance_quaterly)'''
    sql.execute(query)
    print(sql.fetchall())



    conn.commit()
    conn.close()
