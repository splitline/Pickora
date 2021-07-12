from urllib.request import urlopen

from json import load as json_load
from operator import itemgetter
from functools import partial
from itertools import starmap

print("+---------------------+")
print("|  Subreddit Browser  |")
print("+---------------------+")

options = {
    0: "/r/all",
    1: "/r/Python",
    2: "/r/memes",
}

print('id  Subreddit')
tuple(map(print, starmap(
    partial(str.format, "{}:  {}" ),
    options.items())))
choice = input("[+] Choose a subreddit: ")
subreddit = options.get(choice, "/r/Python")

print("Loading...")

json = json_load(urlopen('https://www.reddit.com%s.json' % subreddit))


articles = json['data']['children']
get_data = itemgetter('data')
get_detail = itemgetter('ups', 'title', 'num_comments', 'permalink')
detailed_articles = map(get_detail, map(get_data, articles))

listitem_render = partial(str.format,
                          "-" * 32 + "\n" +
                          "^{0} [{1}] | 💬 {2}\n🔗 https://www.reddit.com{3}\n" +
                          "-" * 32 + "\n")

tuple(map(print, starmap(listitem_render, detailed_articles)))

RETURN = "Subreddit browser demo :D"
