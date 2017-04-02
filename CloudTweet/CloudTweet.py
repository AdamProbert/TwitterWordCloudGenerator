import time
import tweepy
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy.streaming import StreamListener
import logging
import operator
import string
import urllib
from os import path
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import urllib.request
import random


from wordcloud import WordCloud

#Useful link: https://www.dataquest.io/blog/streaming-data-python/


class CloudTweet:

    api = None
    auth = None
    search_terms = ['Gibraltar']
    tweets = []
    tweet_word_count = {}

    def __init__(self):

        consumer_key = 'TOCHDhZpbQFsmg4d2odjVSxJm'
        consumer_secret = 'WP6b1j3Uw3WwjN1hrGk8bQQm7bzgJ7kpEHQH6wHf76x0WafYAV'
        access_token = '848315682358005760-OmSl5diTQCpOljQFrkA71favcsBnkzo'
        access_secret = 'SIhr67MQl71yg2l3WS4IMHaxr8v2tSqJVlzxq6T535VGw'

        self.setup_logger()

        self.auth = OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_secret)

        self.logger.info("Authorisation with Twitter complete")

        self.api = tweepy.API(self.auth)

    def main(self):

        self.logger.info("Beginning main method")
        twitter_stream = Stream(self.auth, listener=MyListener(10*60, 1000))
        twitter_stream.filter(track=self.search_terms) #Search for the voice using a new thread
        self.logger.info("Stream returned")
        self.process_tweets()
        # self.print_word_count()
        self.write_tweet_to_file()
        self.generate_word_cloud()


    def process_tweets(self):
        self.logger.info("Processing tweets")
        for tweet in self.tweets:
            # Split tweet into words
            for word in (tweet.text.split(" ")):
                # Remove punctuation if not url
                if 'http' not in word:
                    word = word.translate(str.maketrans('','',string.punctuation)).lower().replace("\n", "").replace("\r", "")


                if word in self.tweet_word_count:
                    self.tweet_word_count[word] +=1
                elif word not in self.tweet_word_count:
                    self.tweet_word_count[word] = 1
                else:
                    self.logger.warning("Something weird happened with process_tweets")

        self.logger.info("Done processong tweets")


    def write_tweet_to_file(self, filename='/Users/Adam/Dropbox/Programming/PythonProjects/TwitterWordCloudGenerator/Resources/tweets.txt'):

        self.logger.info("Writing tweets to file")
        with open(filename, 'a') as f:
            for tweet in self.tweets:
                f.write(tweet.text)

        self.logger.info("Done writing tweets to file")





    def print_word_count(self):
        sorted_word_count = sorted(self.tweet_word_count.items(), key=operator.itemgetter(1))
        print("Word       :       Count")
        for word, count in self.tweet_word_count.items():
            print(word +"\t:\t" + str(count))


    def generate_word_cloud(self, imageurl='http://concretecanvas.com/wp-content/uploads/2013/07/UK_map1.png'):

        self.logger.info("Generating word cloud")

        urllib.request.urlretrieve(imageurl, "../Resources/Images/uk.jpg")

        mask = np.array(Image.open(path.join(path.dirname(__file__), "../Resources/Images/uk.jpg")))

        text = open("../Resources/tweets.txt").read()

        wc = WordCloud(max_words=1000, mask=mask, margin=10,
                       random_state=1).generate(text)
        # store default colored image
        default_colors = wc.to_array()
        plt.imshow(wc.recolor(random_state=3),
                   interpolation="bilinear")
        wc.to_file(self.search_terms[0] + ".png")
        plt.axis("off")
        plt.figure()
        plt.imshow(default_colors, interpolation="bilinear")
        plt.axis("off")
        plt.show()

        self.logger.info("Finished generating word cloud")



    def setup_logger(self):

        logger = logging.getLogger('CloudTweet')
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        self.logger = logger


class MyListener(StreamListener):


    def __init__(self, max_time=10*60, max_tweets=10000):
        start_time = time.time()
        self.limit = start_time+max_time
        self.max_tweets = max_tweets
        self.logger = logging.getLogger('CloudTweet')
        self.logger.info("My listener initialised")
        super(MyListener, self).__init__()

    def on_status(self, status):
        if time.time() > self.limit:
            return False
        elif len(CloudTweet.tweets)>self.max_tweets:
            return False
        else:
            CloudTweet.tweets.append(status)
            self.logger.info("Received new tweet!")


    def on_error(self, status):
        if status == 420:
            # returning False in on_data disconnects the stream
            self.logger.warning("Twitter api error: %s" %status)
            return False


if __name__ == '__main__':
    ct = CloudTweet()
    ct.main()