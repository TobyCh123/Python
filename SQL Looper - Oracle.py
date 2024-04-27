import pandas as pd
import cx_Oracle
import datetime
import time
# An internal company module to enable easier connection changes
from Oracle_Connections import get_Oracle_dns
import re
import getpass

start = time.time()

""" Connecting to Oracle """

username = "defaultlogin"
password = "defaultlogin"
connection = 'defaultconnection'

while True:
    print("=" * 40, '\n')
    print(f"Username: {username}")
    print(f"Connection: {connection}\n")

    print("Enter 1 if you want to enter personal login details")
    print("Enter 2 if you want to change connection")
    print("Enter anything else to move on")
    inputs = input(":")

    if inputs == '1':
        username = input("Enter your username: ")
        password = getpass("Enter your password: ")
        print("Details updated\n")

    elif inputs == '2':
        connection = input("Enter your connection e.g. (alias): ")
        print(f"new connection: {connection}")

    else:
        try:
            dns_tsn = get_Oracle_dns.get_Oracle_dns(connection)
            conn = cx_Oracle.connect(username, password, dns_tsn)
            curs = conn.cursor()
            print('=' * 20, '\nConnected!')
            break
        except:
            print("Connection failed, please try again")


##############################################

print(time.time() - start)

# ask timeframe and create a list of periods to loop through
first_period = int(input('Enter the first period:'))
last_period = int(input('Enter the final period:'))
period = first_period
period_list = []

while period < last_period + 1:
    period_list.append(period)
    year = int(period/100)
    per = period - (100*year)
    if per == 13:
        period += 88
    else:
        period += 1


print("\nEnter your sql below (any 'YYYYPP' format will be replaced to loop")
print("If you want to use sql already in the script enter 1")
sql_input = input(": ")

df = pd.DataFrame()
for current_period in period_list:

    # 'Essential' time variables
    current_year = str(int(current_period / 100))
    current_week = str(4 * (current_period - (100*int(current_year))))
    current_period = str(current_period)
    year = int(current_year)
    week = int(current_week)
    period = int((current_period)[4:6])
    yrper = year * 100 + period
    lastyr = year - 1
    lastyrper = (year - 1) * 100 + period

    print("This is period ", current_period)
    print("This is year ", current_year)

    # Extra time options for input into SQL query depending on needs
    firstyr = 2015
    firstper = 1
    yrdiff = year - firstyr
    perdiff = period - firstper
    totalperdiff = (yrdiff * 13) + perdiff
    totaldaydiff = totalperdiff * 28
    firstyrperlastday = datetime.date(2015, 2, 1)
    firstyrperlastday24_1 = datetime.datetime(2015, 2, 1, 23, 59, 59, 0)
    firstyrperlastday24_2 = datetime.datetime(2015, 2, 1, 0, 0, 0, 0)
    lastdaycurrper = firstyrperlastday + datetime.timedelta(
        days=(totaldaydiff))
    lastyearlastdaycurrper = lastdaycurrper - datetime.timedelta(
        days=336)
    lastdaycurrper24 = firstyrperlastday24_1 + datetime.timedelta(
        days=(totaldaydiff))
    firstdaycurrper = firstyrperlastday + datetime.timedelta(
        days=(totaldaydiff-27))
    firstdaynextper = firstyrperlastday24_2 + datetime.timedelta(
        days=(totaldaydiff+1))
    lastdayprevper = firstyrperlastday24_1 + datetime.timedelta(
        days=(totaldaydiff-28))

    '''
    SQL to loop through a table like tablename_YYYYPP
    Substitue default sql with your own and replace YYYYPP with {str(yrper)}
    Same method can be used for year and period {str(year)} or {str(period)}
    '''

    default_sql = f'''
        select * from tablename_{str(yrper)}
    '''

    # Runs the SQL
    pattern = r'\d{4}(?:0[1-9]|1[0-3])'
    if sql_input == 1:
        curs.execute(default_sql)
    else:
        matches = re.findall(pattern, sql_input)
        if matches:
            sqlInput = re.sub(pattern, str(yrper), sql_input)
            print('\n' + sql_input)
            print("-"*60 + '\n')
            curs.execute(sql_input)
        else:
            print("Can't find any periods YYYYPP")
            print("I will run it, but does this need to be looped?")
            check = input("Enter to acknowledge...")
            curs.execute(sql_input)

    # Adds current period column and appends to data to dataframe for output
    columns = [column[0] for column in curs.description]
    temp_df = pd.DataFrame(curs.fetchall())
    temp_df.columns = columns
    temp_df.insert(loc=0, column='PERIOD_YEAR.py', value=yrper)
    df = df.append(temp_df)

curs.close()
print(df)
df.to_csv("SQL Period Looped.csv", index=False)

print("Script completed :)")
