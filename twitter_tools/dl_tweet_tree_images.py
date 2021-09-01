#!/usr/bin/env python3

import tempfile
from pathlib import Path
import shutil
import requests

from .get_self_reply_tree_image_tweets import get_self_reply_tree_image_tweets

def dl_tweet_tree_images(
    tweet_id: str,
    output_dir: Path,
    token: str,
):
    tree = get_self_reply_tree_image_tweets(root_tweet_id=tweet_id, token=token)

    num_photos = sum(map(lambda tweet: len(tweet.photo_urls), tree.tweets))
    download_index = 1

    for tweet in tree.tweets:
        print(f'@{tree.screen_name}: {tweet.text}')
        for photo_index, photo_url in enumerate(tweet.photo_urls):
            tweet_dir = output_dir / f'{tree.screen_name}_{tweet_id}'
            tweet_dir.mkdir(parents=True, exist_ok=True)

            filename = Path(photo_url).name
            new_filename = f'{tweet_id}_{download_index:03}_{filename}'
            output_path = tweet_dir / new_filename

            print(f'{"(skip) " if output_path.exists() else ""}[{download_index}/{num_photos}] {photo_url} => {output_path}')

            if output_path.exists():
                download_index += 1
                continue

            with tempfile.NamedTemporaryFile() as fp:
                photo_res = requests.get(photo_url, stream=True)
                shutil.copyfileobj(photo_res.raw, fp)
                shutil.copy(fp.name, output_path)

                download_index += 1
