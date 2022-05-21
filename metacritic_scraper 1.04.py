import requests 
from bs4 import BeautifulSoup
import pandas as pd
import time 
from dateutil.parser import parse #to proccess dates
import re # to parse partial tags
import numpy as np

userAgent={'User-agent':'Mozilla/5.0'}
base_url='https://www.metacritic.com'
for ind in range(0, 195):
    game_names=[]  #name
    scores=[]  #game score - what we will try and predict
    developers=[]  #developer name
    publishers=[]  #publisher name
    genres=[]  #genres the game is associated with
    ratings=[]  #game age rating
    user_score=[]  #game user score as aggragated by user reviews on site
    num_crit_reviews=[]  #number of critics reviews for game
    release_month=[]  #the month the game was released in
    release_year=[]  #the year the game was released in
    platforms=[]  #platform the game was reviewed for
    descriptions=[]  #game description for text proccessing
    dev_career_score=[]  #developer aggragated score
    pub_career_score=[]  #publisher aggragated score
    num_pos_critic=[]  #number of positive reviews
    num_mix_critic=[]  #number of mixed reviews
    num_neg_critic=[]  #number of negative reviews
    
    print('***************')
    # parses list page
    url_page=base_url+'/browse/games/score/metascore/all/all/filtered?page='+str(ind)
    print(url_page)
    response=requests.get(url_page,headers=userAgent)
    time.sleep(0.1) #we had problems with parsing the page so we added the pause so the page had time to load
    soup_page = BeautifulSoup(response.content, 'html.parser')
    # creates a list of all games in the page
    url_game_list=soup_page.find_all('a',attrs={'class':'title'})
    #**************#
    
    # parses each page
    for game in url_game_list:
        game_url=base_url+game['href']
        print(game_url)
        #this 'if' statement is for each page that created a specific problem that couldnt be solved
        if(game_url == "https://www.metacritic.com/game/pc/wild-west-online"):
            continue
        response = requests.get(game_url,headers=userAgent)
        time.sleep(0.5) #we had problems with parsing the page so we added the pause so the page had time to load
        soup_game = BeautifulSoup(response.content, 'html.parser')
        #**************#
    
        #game name
        game_names.append(soup_game.find("a",{"class":"hover_none"}).get_text().strip())
        #**************#

        #game score
        scores.append(int(soup_game.find("span",{"itemprop":"ratingValue"}).get_text().strip()))
        #**************#

        #list of genres
        genres_list=[]#the list of stripped down genres
        #finding the right tag
        genre_li=soup_game.find_all("li",attrs={"class":"summary_detail product_genre"})
        if(genre_li!=None):
            #receiving a list of all the genres
            gen_list=genre_li[0].find_all("span",attrs={"class":"data"})
            for genre in gen_list:
                genres_list.append(genre.get_text().strip()) #stripping names and adding them to list
            genres.append(list(dict.fromkeys(genres_list))) #removes duplicates inside genre list
        else:
            genres.append(np.nan)
        #**************#

        #rating
        #checking if rating exists, not all game get ratings - usually hyper violent games
        if(soup_game.find("li",attrs={"class":"summary_detail product_rating"})!=None):
            rating=soup_game.find("li",attrs={"class":"summary_detail product_rating"})
            ratings.append(rating.find("span",attrs={"class":"data"}).get_text().strip())
        else:
            ratings.append(np.nan)
        #**************#

        #user score
        user_score_element = soup_game.find("div",{"class":re.compile(r'^metascore_w user large game')})
        # some games didnt have an aggragated user score
        if(user_score_element == None or user_score_element.get_text().strip() == 'tbd'):
            user_score.append(np.nan)
        else:
            user_score.append(float(soup_game.find("div",{"class":re.compile(r'^metascore_w user large game')}).get_text().strip()))
        
        #**************#

        #number of reviews
        #reviews divided by positive,mixed and negative
        game_scores_div=soup_game("div",attrs={"class":"module reviews_module critic_reviews_module"})[0]
        score_list=game_scores_div.find_all("span",attrs={"class":"count"})
        sum_crit=0
        num_pos_critic.append(int(score_list[0].get_text().strip()))
        num_mix_critic.append(int(score_list[1].get_text().strip()))
        num_neg_critic.append(int(score_list[2].get_text().strip()))
        for spans in score_list:
            sum_crit=int(spans.get_text().strip())+sum_crit
        num_crit_reviews.append(sum_crit)
        #**************#

        #release date divide by day, month, year
        releas=soup_game("li",attrs={"class":"summary_detail release_data"})[0]
        date=releas.find("span",attrs={"class":"data"}).get_text().strip()
        dt=parse(date) #a function able to return a date from a string
        dt=dt.strftime('%Y-%m-%d') #a function able to return a date by format
        dt=dt.split(sep='-') #seperating the date
        release_month.append(int(dt[1]))
        release_year.append(int(dt[0]))
        #**************#

        #platforms
        platforms.append(soup_game.find("span",{"class":"platform"}).get_text().strip())
        #**************#

         #game description
         #checking if a description exists
        if(soup_game.find("li",{"class":"summary_detail product_summary"}) != None):
            desc=soup_game("li",attrs={"class":"summary_detail product_summary"})[0]
            #in some pages the summary is too long so they separate it to collapsed and expanded
            if(desc.find("span",attrs={"class":"blurb blurb_expanded"})==None):
                descr=desc.find("span",attrs={"class":"data"}).get_text().strip()
            else:
                descr=desc.find("span",attrs={"class":"blurb blurb_expanded"}).get_text().strip()
            descriptions.append(descr)
        else:
            descriptions.append(np.nan)
        #**************#

        #publisher
        #publisher career score
        pub_li=soup_game.find("li",attrs={"class":"summary_detail publisher"}) #finding the right tag
        publisher_temp = np.nan
        pub_career_temp = np.nan
        #checking if a publisher exists on page
        if(pub_li != None):          
            #finding first publisher
            publisher_temp=pub_li.find("a").get_text().strip()
            publishers.append(publisher_temp)
            
            # finding the publisher url
            pub_url=pub_li.find("a")['href']
            pub_domain=base_url+pub_url
            response=requests.get(pub_domain,headers=userAgent)
            soup_pub = BeautifulSoup(response.content, 'html.parser')
            # finding the publisher score with a specific elemnt
            pub_career_temp=soup_pub.select("tr.review_average > td > span")
            # some publisher didnt have a score, so we had to check
            if(len(pub_career_temp) == 0):
                pub_career_temp = np.nan
                pub_career_score.append(pub_career_temp)
            else:
                pub_career_temp = pub_career_temp[0].get_text().strip()
                pub_career_score.append(int(pub_career_temp))
            #**************#
        else:
           publishers.append(publisher_temp)
           pub_career_score.append(pub_career_temp)

        #developer
        #developer career score
        dev_li=soup_game.find("li",attrs={"class":"summary_detail developer"}) #finding the right tag
        #some games didnt have a developer written
        if(dev_li != None):
            developer_temp=dev_li.find("a").get_text().strip()        
            developers.append(developer_temp)
        else:
            developer_temp = publisher_temp
            developers.append(developer_temp)
        # appending the publisher score
        #checking if the publisher and developer aren't the same to save time
        if(developer_temp!=publisher_temp):
            dev_url=dev_li.find("a")['href']
            dev_domain=base_url+dev_url
            response=requests.get(dev_domain,headers=userAgent)
            soup_dev = BeautifulSoup(response.content, 'html.parser')
            dev_career_temp=soup_dev.select("tr.review_average > td > span")
            if(len(dev_career_temp) == 0):
                dev_career_temp = np.nan
                dev_career_score.append(dev_career_temp)
            else:
                dev_career_temp = dev_career_temp[0].get_text().strip()
                dev_career_score.append(int(dev_career_temp))
        else:
            dev_career_score.append(int(pub_career_temp))
        #**************#
        #end of loop
        
    df=pd.DataFrame({'game_name': game_names, 'score': scores,'user_score': user_score,'platform': platforms,
                         'developer': developers,"developer_score":dev_career_score, 'publisher': publishers,
                         "publisher_score":pub_career_score,'rating': ratings,'release_month': release_month,
                         'release_year': release_year,'num_crit_review': num_crit_reviews, 'num_pos_critic': num_pos_critic,
                         'num_mix_critic': num_mix_critic,'num_neg_critic': num_neg_critic, 'genres':genres,
                         'descriptions': descriptions})
    if(ind>0): # on first time create the file
        df.to_csv("game_score_database.csv",mode='a',index=False,header=False)
    else: #on succesive runs append to existing file
        df.to_csv("game_score_database.csv",index=False)
    time.sleep(30)
    
print("the end")