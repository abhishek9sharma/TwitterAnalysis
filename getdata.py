import tweepy
import json
import Utlis as ut
import time
import math
import os
import random

class TweetExtractor:
    def __init__(self, minlikes = 2, mincharlen = 16 , tweetstofind = 250, configfilepath = 'config.json', datafolder = 'Data/', idsprocessedfile = "idsprocessedalready.txt", writeheader = False):
        try:
            self.minlikes = minlikes
            self.tweetstofind  = tweetstofind 
            self.mincharlen = mincharlen
            self.config = self.ReadConfig(configfilepath)
            self.datafolder = datafolder
            self.apiDict = self.InitiateAPIHAndlers()
            self.rangeoflikes = {'min': {'val': math.inf, 'id':''}, 'max': {'val': -math.inf, 'id':''}}

            self.idsprocessedfile = idsprocessedfile
            if os.path.exists(self.idsprocessedfile):
                idfileobj = open(self.idsprocessedfile,'r')
                self.tweetidsprocessed = [str(id.strip()) for id in idfileobj.readlines()]
                idfileobj.close()
            else:
                open(self.idsprocessedfile,'a').close()
                self.tweetidsprocessed =[]
            #self.maxid = max(self.tweetidsprocessed)
            self.headerwritten = writeheader
        
        except:
            print ("some error occured while initializing tweet extrction module")

    def InitiateAPI(self, auth):
        return tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=True)

    def InitiateAPIHAndlers(self):
        cnt =0 
        apiDict ={}       
        for configinfo in self.config:
            auth = tweepy.OAuthHandler(configinfo['CONSUMER_KEY'],configinfo['CONSUMER_SECRET'])
            auth.set_access_token(configinfo['ACCESS_TOKEN'],configinfo['ACCESS_SECRET'])
            api=self.InitiateAPI(auth)
            apiDict[cnt]=api
            cnt+=1
        return apiDict

    def ReadConfig(self, configpath):
        with open(configpath, 'r') as f:
            config = json.load(f)
        return config

    def IsValidTweet(self, tweetjson):
        favorite_filter = int(tweetjson['favorite_count'])>=self.minlikes
        char_filter = len(tweetjson['full_text'])>=self.mincharlen
        #isRT = 'retweeted_status' in tweetjson

        return favorite_filter & char_filter #& not(isRT)

    def UpdateRange(self,likes,id):
        if int(likes)<self.rangeoflikes['min']['val']:
            self.rangeoflikes['min']['val'] = likes
            self.rangeoflikes['min']['id'] =id
        elif int(likes)>self.rangeoflikes['max']['val']:
            self.rangeoflikes['max']['val'] = likes
            self.rangeoflikes['max']['id'] =id
        else:
            pass


    def WriteToJSONFile(self,data,filename, foldername):
        with open(self.datafolder + foldername +filename+'.json','a') as fo:
            json.dump(data,fo)
    
    def ExtractDataToWrite(self,tweetjson):
        tweetid = tweetjson['id_str']
        tweetcontent = tweetjson['full_text'].replace(',','') 
        likes = str(tweetjson['favorite_count'])
        langauge = tweetjson['lang'] 
        retweets = str(tweetjson['retweet_count'])
        charlen = str(len(tweetjson['full_text']))
        textline = ",".join([tweetid, tweetcontent, likes, langauge, charlen, retweets])
        return textline                        

    def WriteToTextFile(self,data,filename):
        with open(filename,'a') as fo:
            fo.write(data.replace('\n','').strip() +'\n')
    
    def CountAlreadyProcessed(self, searchkeyword):
        filesprocessedalready = os.listdir(self.datafolder+'/JSON/')
        alreadyprocessed = [int(f.split('_')[1].split('.')[0]) for f in filesprocessedalready if searchkeyword in f]
        if len(alreadyprocessed)>0:
            max_id_curr_search = min(alreadyprocessed)
        else:
            max_id_curr_search = NotImplementedError
        countalreadyprocessed = len(alreadyprocessed)
        return countalreadyprocessed, max_id_curr_search


    def ExtractTweets(self, searchkeyword):
        #self.tweetidsprocessed = []
        count_processed_before, max_id_curr_search = self.CountAlreadyProcessed(searchkeyword)

        #override already processed jsons delete later
        # filesprocessedalready = os.listdir(self.datafolder+'/JSON/')
        # self.tweetidsprocessed = [str(f.split('_')[1].split('.')[0]) for f in filesprocessedalready]

        tweetlimit = self.tweetstofind - count_processed_before
        if tweetlimit ==0 :
            print( " Have already found " + str(self.tweetstofind) + " for  hashtag " + searchkeyword)
            return 
        
        #tweetlimit = 5
        twtcntvalid = 0
        twtcounttotal =0
        last_proceesed_id =  None
        while(twtcntvalid<tweetlimit):
            try:
                #for idx, api in self.apiDict.items():
                apikeys = list(self.apiDict.keys())
                random.shuffle(apikeys)            
                for idx in apikeys:
                    api = self.apiDict[idx]
                    try:
                        #maxid is buggy check later if fixed can speed up data collection
                        for page in tweepy.Cursor(api.search, q = searchkeyword, count=100, tweet_mode='extended', max_id = None).pages():
                                try:
                                    #print(str(len(page)) + "  tweets found in page " )
                                    for tweetstatus in page:
                                        tweetjson = tweetstatus._json
                                        tweetid = tweetjson['id_str']
                                        if tweetid==str(max_id_curr_search):
                                            print("Cannot find tweets behhin the current max id i.e ", + tweetid)
                                            return twtcntvalid
                                        else:
                                            max_id_curr_search = int(tweetid)
                                        if tweetid not in self.tweetidsprocessed:
                                            self.tweetidsprocessed.append(tweetid)
                                            if self.IsValidTweet(tweetjson):
                                                self.UpdateRange(tweetjson['favorite_count'],tweetid)
                                                self.WriteToJSONFile(tweetjson, searchkeyword +'_'+ tweetid, '/JSON/')
                                                if not(self.headerwritten):
                                                    #has bugrewrites header when restarting job
                                                    self.WriteToTextFile('tweetid,content,likes,language,retweets,charlen,HT', self.datafolder + 'alltweets.txt')
                                                    self.headerwritten = True
                                                self.WriteToTextFile(self.ExtractDataToWrite(tweetjson) +","+ searchkeyword, self.datafolder + 'alltweets.txt')
                                                twtcntvalid+=1
                                                twtcounttotal+=1
                                                if twtcntvalid==tweetlimit:
                                                    print(" Finally Found ", twtcntvalid, "  tweets in ", twtcounttotal, "tweets that were checked for HT", searchkeyword)
                                                    return twtcntvalid
                                            else:
                                                self.WriteToJSONFile(tweetjson, searchkeyword +'_'+ tweetid, '/INVALID/')                                                
                                                self.tweetidsprocessed.append(tweetid)
                                                twtcounttotal+=1

                                        self.WriteToTextFile(tweetid, self.idsprocessedfile)                                   
                                        if twtcounttotal%500==0 and twtcounttotal>0:
                                            print( " proceesed ", twtcounttotal, " tweets for ", searchkeyword, " and have found ", twtcntvalid, " valid tweets")
    
                                    if twtcntvalid%60==0 and twtcntvalid>0:
                                        print( " Found ", twtcntvalid, " valid tweets for ", searchkeyword, "among total tweets ", twtcounttotal)

                                    if twtcounttotal%200==0 and twtcounttotal>0:
                                        print( " proceesed ", twtcounttotal, " tweets for ", searchkeyword, " and have found ", twtcntvalid, " valid tweets")
                                    time.sleep(10)
                                except Exception as e:
                                    print("Some error occured while processing tweet with id  " + tweetid + " :: " + str(e))
                    except tweepy.TweepError as e:
                        print("Error")
                        print( " Error occured, moving to next API Interface " + str(e.message))
                        pass
                                
            except:
                print(" error occured while extracting tweets using ", idx, api)
                return 0






# #Collect Data 
# #htlist = ['Service', 'price', 'cost', 'quality', 'ambiente', 'reservation']
# htlist = ['cost']
# data_collector = TweetExtractor(minlikes = 2, mincharlen = 16, tweetstofind = 300, configfilepath= 'config.json', datafolder= 'Data/', idsprocessedfile ='idsprocessedalready.txt', writeheader = False)
# data_collector.InitiateAPIHAndlers()
# for ht in htlist:
#     print( "Collecting Tweets for hashtag #" + ht)
#     print(str(data_collector.ExtractTweets('#'+ht)) + " tweets extracted for hashtag #" + ht)
#     print()

    
# #Print Range 
# minlikes = data_collector.rangeoflikes['min']
# maxlikes = data_collector.rangeoflikes['max']
# print (' Minimum Likes found are ', minlikes['val'], " for tweet id ", minlikes)
# print (' Maximum Likes found are ', maxlikes['val'], " for tweet id ", maxlikes)




    


