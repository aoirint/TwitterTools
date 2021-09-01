import json
import requests
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ImageTweet:
    tweet_id: str
    text: str
    photo_urls: List[str]

@dataclass
class SelfReplyTreeImageTweets:
    root_tweet_id: str
    screen_name: str
    tweets: List[ImageTweet]

def get_self_reply_tree_image_tweets(
    root_tweet_id: str,
    token: str,
) -> SelfReplyTreeImageTweets:
    session = requests.Session()

    headers = {
      'Authorization': f'Bearer {token}'
    }

    # https://developer.twitter.com/en/docs/twitter-api/tweets/lookup/api-reference/get-tweets-id
    params = {
        'ids': root_tweet_id,
        'tweet.fields': 'conversation_id',
        'expansions': 'author_id',
        'user.fields': 'username',
    }
    res_root_tweets = session.get(f'https://api.twitter.com/2/tweets', headers=headers, params=params)

    root_tweets = res_root_tweets.json()
    root_tweets_data = root_tweets['data']
    root_tweets_includes = root_tweets['includes']

    root_tweet = root_tweets_data[0]
    conversation_id = root_tweet['conversation_id']

    author = root_tweets_includes['users'][0]
    author_screen_name = author['username']

    # TODO: work in progress

    params = {
        'q': f'from:{author_screen_name}',
        'since_id': root_tweet_id,
        'count': 100,
        'result_type': 'mixed',
        'include_entities': 1,
    }

    # https://developer.twitter.com/en/docs/twitter-api/v1/tweets/search/api-reference/get-search-tweets
    res_self_mentions = session.get('https://api.twitter.com/2/search/tweets.json', headers=headers, params=params)
    self_mentions = json.loads(res_self_mentions.text)

    thread_ids = set()
    thread_ids.add(str(root_tweet_id))

    self_replies = []
    self_replies.append(tweet)
    for mention in reversed(self_mentions['statuses']):
        mention_tweet_id = str(mention['id'])
        in_reply_to_status_id = str(mention['in_reply_to_status_id'])

        if in_reply_to_status_id is not None and in_reply_to_status_id in thread_ids:
            thread_ids.add(mention_tweet_id)
            self_replies.append(mention)

    # print(':Self Reply List')
    # for self_reply in self_replies:
    #     print(self_reply['id'], self_reply['text'], '=>', self_reply['in_reply_to_status_id'])

    def get_photo_urls(entities: Dict[str, Any]) -> List[str]:
        media = entities.get('media')
        if media is None:
            return []

        photos = filter(lambda medium: medium['type'] == 'photo', media)
        photo_urls = map(lambda photo: photo['media_url_https'], photos)
        return list(photo_urls)

    image_tweets = []
    for self_reply in self_replies:
        tweet_id = self_reply.get('id')
        text = self_reply.get('text')

        entities = self_reply.get('entities')
        extended_entities = self_reply.get('extended_entities')

        photo_urls = []
        photo_urls += get_photo_urls(entities=entities)
        photo_urls += get_photo_urls(entities=extended_entities)

        photo_urls = sorted(set(photo_urls), key=photo_urls.index)

        image_tweets.append(ImageTweet(
            tweet_id=tweet_id,
            text=text,
            photo_urls=photo_urls,
        ))

    return SelfReplyTreeImageTweets(
        root_tweet_id=root_tweet_id,
        screen_name=author_screen_name,
        tweets=image_tweets,
    )
