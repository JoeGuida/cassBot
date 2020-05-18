from discord.ext import commands
from decouple import config
import praw
import discord
import json
import asyncio
import datetime
import re

# The reddit class implements a scraper for the Reddit API that:
# - Pulls new submissions from r/CassiopeiaMains every X seconds
# - Posts new submissions to the CassiopeiaMains discord server as a discord embed

class Reddit(commands.Cog):

    # Create bot instance and reddit instance
    # Start the get_newest_submission() task
    # channel_id = channel to post reddit submissions
    # subreddit = name of subreddit to pull submissions from
    # timer = interval to check for new posts
    def __init__(self, bot):
        self.bot = bot
        self.reddit = praw.Reddit(client_id=config('REDDIT_CLIENT_ID'),
                                  client_secret=config('REDDIT_CLIENT_SECRET'),
                                  user_agent=config('REDDIT_USER_AGENT'))
        self.bot.loop.create_task(self.get_newest_submission())
        self.channel_id = 698318509939359814
        self.subreddit = 'CassiopeiaMains'
        self.timer = 30

    # Pull the last submission that was posted to discord
    # and the newest reddit post, and send the submission
    # to post_submission() if it is new
    async def get_newest_submission(self):
        await self.bot.wait_until_ready()

        while True:
            # Get the id of the last submission posted to discord
            with open('reddit.json', 'r') as file:
                latest_submission_id = json.loads(file.read())['submission_id']

            # If the submission is new, send it
            subreddit = self.reddit.subreddit(self.subreddit)
            for submission in subreddit.new(limit=1):
                if submission.id != latest_submission_id and submission != None:
                    self.store_latest_submission_id(submission.id)
                    await self.post_submission(submission)

            # Sleep to run on the timer
            await asyncio.sleep(self.timer)
        
    # Take the newest submission and create an embed of the 
    # submissions content and post it to the #reddit channel, 
    async def post_submission(self, submission):
        # Get channel to send the message
        channel = self.bot.get_channel(self.channel_id)
        
        # Determine the submission type and pass to create_embed()
        image_filetypes = ['.jpg', '.gif', '.png', '.bmp', '.tif']
        if submission.url[-4:] in image_filetypes:
            tag = 'image'
        elif submission.selftext == '':
            tag = 'link'
        else:
            tag = 'text'
        # Create an embed for the submission type
        embed = self.create_embed(submission, tag=tag)
        
        # Finally send the message with the embed to the channel
        await channel.send('A new post has been submitted on /r/CassiopeiaMains!')
        await channel.send(embed=embed)

    # Take the submission id of the last posted message
    # and write json in the format: { 'submission_id': submission_id }
    def store_latest_submission_id(self, submission_id):
        with open('reddit.json', 'w') as file:
            file.write(json.dumps({ 'submission_id': submission_id }))

    # Creates an embed of the reddit submission
    # Alters the embed based on the tag parameter
    def create_embed(self, submission, tag='text'):
        # All embed types share the same color, title, timestamp, 
        # author, and thumbnail, data will hold all the embed options
        data = {
            'color': 0x7fff00,
            'title': submission.title,
            'author': { 'name': f'/u/{submission.author.name}' },
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'thumbnail': { 'url': submission.author.icon_img }
        }
        
        if tag == 'image':
            data['image'] = { 'url': submission.url }
        if tag in ['image', 'link']:
            data['url'] = f'https://www.reddit.com{submission.permalink}'
        else:
            # This '&#x200B;' character is showing up sometimes, remove it
            # Discord embed descriptionhas a 2048 character max
            # Limit the submissions selftext to fit the description limit.
            selftext = submission.selftext.replace('&#x200B;', '')
            data['description'] = selftext[:2048],
                        
        return discord.Embed.from_dict(data)
