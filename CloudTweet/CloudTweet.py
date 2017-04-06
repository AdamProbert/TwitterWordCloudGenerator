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
from imgurpython import ImgurClient

import json

from wordcloud import WordCloud

#Useful link: https://www.dataquest.io/blog/streaming-data-python/


class CloudTweet:

    api = None
    auth = None
    tweets = []
    tweet_word_count = {}

    def __init__(self):

        self.setup_logger()

        self.auth = OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_token, access_secret)

        self.logger.info("Authorisation with Twitter complete")

        self.api = tweepy.API(self.auth)

    def main(self):

        self.logger.info("Beginning main method")
        self.logger.info("Collecting trending topics")
        trends = self.find_trends()

        for trend in trends[:5]:
            trend = trend['name']
            filename = '/Users/Adam/Dropbox/Programming/PythonProjects/TwitterWordCloudGenerator/Resources/Clouds/' + trend + '_cloud.png'
            comment = "A TweetCloud for " + trend + "!"

            self.logger.info("Streaming tweets for for: " + trend)

            # Collect tweets
            self.stream_tweets(topic=trend, num=100)

            self.logger.info("Streaming complete")

            # Write to file
            self.write_tweet_to_file()

            # Need some stuff for collecting the background image, bing api looks good.
            self.generate_word_cloud(filename)

            # Upload to imgur
            # self.upload_word_cloud()

            # Post the tweet
            self.api.update_with_media(filename, comment)

            self.logger.info("Tweet posted for " + trend)

        self.logger.info("All trends done")


        # self.logger.info("Stream returned")
        # self.process_tweets()
        # # self.print_word_count()
        # self.write_tweet_to_file()
        # self.generate_word_cloud()
        # trend_list = self.find_trends()

    def stream_tweets(self, topic='#python', num=1000):

        twitter_stream = Stream(self.auth, listener=MyListener(10*60, num))
        twitter_stream.filter(track=topic) #Search for the voice using a new thread



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
        with open(filename, 'w') as f:
            for tweet in self.tweets:
                f.write(tweet.text)

        time.sleep(2)

        self.logger.info("Done writing tweets to file")


    def print_word_count(self):
        sorted_word_count = sorted(self.tweet_word_count.items(), key=operator.itemgetter(1))
        print("Word       :       Count")
        for word, count in self.tweet_word_count.items():
            print(word +"\t:\t" + str(count))


    def generate_word_cloud(self, filename, imageurl='http://concretecanvas.com/wp-content/uploads/2013/07/UK_map1.png'):

        self.logger.info("Generating word cloud")

        urllib.request.urlretrieve(imageurl, "../Resources/Images/uk.jpg")

        mask = np.array(Image.open(path.join(path.dirname(__file__), "../Resources/Images/uk.jpg")))

        text = open("../Resources/tweets.txt").read()

        wc = WordCloud(max_words=400, mask=mask, margin=10,
                       random_state=1).generate(text)
        # store default colored image
        default_colors = wc.to_array()
        plt.imshow(wc.recolor(random_state=3),
                   interpolation="bilinear")
        wc.to_file(filename)
        plt.axis("off")
        plt.figure()
        plt.imshow(default_colors, interpolation="bilinear")

    def upload_word_cloud(self, path):

        self.logger.info("Uploading cloud to imgur...")
        client_id = '71f48d008a5cdf2'
        client_secret = 'cc526f8fb0275877cbcf7cdc3854206c4a02e908'

        client = ImgurClient(client_id, client_secret)

        # Example request
        image = client.upload_from_path(path, config=None, anon=True)

        self.logger.info("Done!")
        self.logger.info("Imgur link: " + image['link'])

        return image['link']

    # Returns ordered list of trending topics from UK.
    def find_trends(self):
        trends_list = []
        places = self.api.trends_place(23424975)

        for uk in places:
            for trend in uk["trends"]:
                trends_list.append(trend)
                # self.logger.info("Trending topic: " + trend)

        return trends_list



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
        CloudTweet.tweets = []
        start_time = time.time()
        self.limit = start_time+max_time
        self.max_tweets = max_tweets
        self.logger = logging.getLogger('CloudTweet')
        self.logger.info("My listener initialised")
        super(MyListener, self).__init__()

    def on_status(self, status):

        if time.time() > self.limit:
            return False
        elif len(CloudTweet.tweets) > self.max_tweets:
            return False
        else:
            CloudTweet.tweets.append(status)
            print("Collecting tweets. Tweet: " + str(len(CloudTweet.tweets)))


    def on_error(self, status):
        if status == 420:
            # returning False in on_data disconnects the stream
            self.logger.warning("Twitter api error: %s" %status)
            return False


if __name__ == '__main__':
    ct = CloudTweet()
    ct.main()
