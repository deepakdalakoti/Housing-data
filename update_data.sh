#Script to update data. This is to update suburb performance statistics data
#We will first look and see if we have started processing before by looking if there is a query_points file available
#If yes start from there and process, otherwise drop table and start from beginning
#read -p "Enter City: " city
#read -p "Database name: " db
#read -p "Bedrooms: " bed
#read -p "Dwelling type (House/Unit): " dwelling
#read -p "Period (Years/Half years/Quarters): " period
#read -p "Number of periods: " nperiod

city=Sydney
db=housing.db
bed='2 3'
dwelling='House Unit'
period=years
nperiod=40

#Check if file exists
if [ -e "query_points_"$city.pkl ]; then
	echo "query file exists, will update table"
	python3 house_prices.py --database_name=$db --city=$city --fill_table_performance --period=$period --num_periods=$nperiod --bedroom $bed --type $dwelling

else
	echo "query file does not exists, will start over"
	python3 house_prices.py --reset_table --database_name=$db --city=$city --fill_table_performance --period=$period --num_periods=$nperiod --bedroom $bed --type $dwelling
fi
