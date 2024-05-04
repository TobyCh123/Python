import pandas as pd
import matplotlib.pyplot as plt
import requests
import datetime
import re

from bs4 import BeautifulSoup
from pytrends.request import TrendReq
from random import randint
from time import sleep

date = datetime.datetime.now()
date = str(date.year) + str(date.month) + str(date.day)


# To scrape and sleep at random times to stop being blocked
def Sleeper(max_time):
    sleeptime = randint(3, max_time)
    print("="*80)
    print("Waiting " + str(sleeptime) + " Seconds")
    sleep(sleeptime)


# Finds the latest articles on popsci website
def GetURLs():
    url_collected = []
    # Homepage to find links
    url = 'https://www.popsci.com/category/science/'
    page = requests.get(url)
    print("Getting the latest news articles from: " + url)
    print("Connecting to homepage to find the articles")
    RequestStatusCheck(page)
    soup = BeautifulSoup(page.content, 'html.parser')
    # Loops through the items in the Lateset Articles section
    print("Getting the latest news articles...")
    for item in soup.select('section.LatestArticles'):
        i = 0
        while True:
            # Identifies the links
            try:
                text = item.select('a.PostItem-link')[i]
                text = str(text).split()
                the_link = text[2][6:-2]
                url_collected.append(the_link)
            except:
                # breaks the loop once it fails i.e. reaches the end
                break
            i += 1
    return url_collected


# Checks the connection
def RequestStatusCheck(page):
    if page.status_code != 200:
        print(page.status_code)
    else:
        print("Connected")
        print()


# Reads article contents adding paragraphs to a list
def ArticleReader(url):
    print(url)
    article = []
    page = requests.get(url)
    RequestStatusCheck(page)
    soup = BeautifulSoup(page.content, 'html.parser')
    for elem in soup.select('div.Article-bodyText'):
        i = 0
        while True:
            try:
                text = elem.select('p')[i].text
                article.append(text)
            except:
                break
            i += 1
    return(article)


# This Joins the list (paragraphs into one string and removes all punctuation
def StringCleaner(string):
    string = " ".join(string)
    string = re.sub(r'[^\w\s]', '', string)
    return string


# Calculates the frequency of the words in the string
def wordFrequency(string):
    string = " ".join(string)
    string = string.lower()
    string = string.split(" ")
    word_frequency = {}
    for i in string:
        if i in word_frequency:
            word_frequency[i] += 1
        else:
            word_frequency[i] = 1
    return(word_frequency)


# Removes common words from the frequency dictionary
def WordRemover(freq_dict):
    removal_list = ['and', 'the', 'cant', 'can','more','their' 'it', 'but', 'in', 'how' 'if', 'theyre','she',
                        'he','an','if','dont','may','do','theres','such', 'only','we','has','is','for','his',
                        'that','you','heres','to','of','a','be','are','not','as','or','had','no','i','would',
                        'no','my','off','like','at','have','than','there','with','its','this','says','your',
                        'it', 'when','by','their','these','what','who','how','they','so', 'on', 'from', '',
                        'was', 'were', 'her', 'some', 'been', 'much', 'most','them', 'out', 'could', 'into',
                        'also', 'up', 'one', 'which', 'about', 'other', 'new', 'study', 'work', 'time','our',
                        'will','all','while','over','did','even','two','first','said','according','years', 'just',
                        'same','where','us','then','any','see','related','might','still','help','very', 'information']
    # Adds words with only one apperance to removal list
    remove_low_words = 0
    # Not active, but can be used to remove low appearing words#
    if remove_low_words == 1:
        x = 0
        for word in freq_dict:
            try:
                if freq_dict[word] == 1:
                    removal_list.append(word)
            except:
                continue
            x += 0

    # Loops through the remove list, removing them from the dict
    for word in removal_list:
        try:
            del freq_dict[word]
        except:
            continue
    return freq_dict


# Sorts the Dictionary in decesending order
def DictSorter(mydict):
    sorteddict = dict(sorted(mydict.items(),
                             key=lambda x: x[1],
                             reverse=True))
    return sorteddict


# Runs the key_word through googles trend checker API
def GoogleApi(key_word):
    # Language and Timezone
    pytrends = TrendReq(hl='en-US', tz=0)
    # "builds payload" i.e. sends search to google
    pytrends.build_payload([key_word], cat=0, timeframe='today 12-m')
    data = pytrends.interest_over_time()
    Sleeper(5)
    suggestions = pytrends.related_queries()
    suggestions[key_word]['top']
    # Sorts
    data = data.sort_values(by=['date'])
    data = data.reset_index()
    return data, suggestions


##############
#    Main
#############


# Gets Latest URLs from link, turns it into a dataframe with date column
url_collected = GetURLs()

# Reads the file to check if it has read any of these articles already
try:
    File = pd.read_excel("Word Frequency.xlsx", sheet_name=['WordFreq',
                                                            'ArticlesRead'])
    current_word_freq = File['WordFreq']
    read_urls = File['ArticlesRead']

    read_list = read_urls.iloc[:, 0].tolist()
    url_to_read = [i for i in url_collected if i not in read_list]
except:
    url_to_read = url_collected

if len(url_to_read) == 0:
    print("No new articles")

# Runs through the functions to obtain and read the articles
all_articles = []
counter = 0
for top_url in url_to_read:
    Sleeper(18)
    article = ArticleReader(top_url)
    article = StringCleaner(article)
    all_articles.append(article)
    counter += 1
    print(counter, "out of", len(url_to_read), "articles read")

# Calculates the word frequencies and cleans the result
WordFreq = wordFrequency(all_articles)
cleanfreq = WordRemover(WordFreq)
sortedfreq = DictSorter(cleanfreq)
# Turns into a dataframe and adds date
df = pd.DataFrame(list(sortedfreq.items()), columns=['Word', 'Frequency'])
df['Date'] = date

# Creates data frame of the read urls to concatenate with previously read
url_to_read_df = pd.DataFrame(url_to_read)
url_to_read_df = url_to_read_df.rename(columns={0: 'URLs'})
url_to_read_df['Date Read'] = date

# Appends new df to old one before grouping to get the total word counts
try:
    NewReadURL = pd.concat([read_urls, url_to_read_df], ignore_index=True)
except:
    NewReadURL = url_to_read_df

try:
    NewWordFreq = pd.concat([current_word_freq, df], ignore_index=True)
    NewWordFreq = NewWordFreq.groupby(by=['Word'])['Frequency'].sum().sort_values(ascending=False)
    myindex = True
except:
    NewWordFreq = df
    myindex = False


# Saves the joint total dataframe to excel
with pd.ExcelWriter("Word Frequency.xlsx",
                    mode="w",
                    engine="openpyxl"
                    ) as file:
    NewWordFreq.to_excel(file, sheet_name='WordFreq', index=myindex)
    NewReadURL.to_excel(file, sheet_name='ArticlesRead', index=False)

########
# Google Search Trends API #
########

keyword_list = current_word_freq['Word'].tolist()
toplist = keyword_list[:5]
print("Top 5 words are...")
print(toplist)


for i in toplist:
    gc = 0
    while True:
        try:
            data, suggestions = GoogleApi(i)
            break
        except:
            print(""""google thinks we are a bot, obvs they are right,
                  but will try again in a few""")
            Sleeper(25+gc)
            gc += 2

    data['PoP'] = (data[i].pct_change())*100

    suggestions = suggestions[i]
    rising_df = pd.DataFrame(suggestions.get("rising"))
    top_df = pd.DataFrame(suggestions.get("top"))
    sus = pd.concat([rising_df, top_df], axis=1, ignore_index=True)
    sus = sus.rename(columns={0: 'Top Searches', 1: 'Top values',
                              2: 'Rising Searches', 3: 'Rising Values'})
    print(sus)

    # Creating the graph
    plt.style.use('ggplot')

    plt1 = plt.subplot2grid((11, 1), (0, 0), rowspan=5, colspan=1)
    plt2 = plt.subplot2grid((12, 1), (7, 0), rowspan=5, colspan=1)
    plt1.title.set_text('PoP IOT change')
    plt2.title.set_text('Interest Over Time')
    plt1.plot(data['date'], data['PoP'], color='blue', linestyle='solid',
              linewidth=3)
    plt2.plot(data['date'], data[i], color='green', linestyle='solid',
              linewidth=3)

    plt.style.use('ggplot')
    plt3 = plt.subplot2grid((11, 1), (0, 0), rowspan=5, colspan=1)
    plt4 = plt.subplot2grid((12, 1), (7, 0), rowspan=5, colspan=1)
    plt3.title.set_text('Top Searches')
    plt4.title.set_text('Rising Searches')
    plt3.barh(sus['Top Searches'], sus['Top values'], color='blue',
              linestyle='solid', linewidth=3)
    plt4.barh(sus['Rising Searches'], sus['Rising Values'], color='green',
              linestyle='solid', linewidth=3)
    plt.show()


