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
        self.embed_color = discord.Color(0x7fff00)
        self.channel_id = 671168589084229642
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
                if submission.id != latest_submission_id:
                    await self.post_submission(submission)

            # Sleep to run on the timer
            await asyncio.sleep(self.timer)
        
    # Take the newest submission and create an embed of the 
    # submissions content and post it to the #reddit channel, 
    # Send submission id to store_latest_submission() 
    # if submission is not new (is None), return.
    async def post_submission(self, submission):
        if submission == None:
            return

        # Get channel and update reddit.json
        channel = self.bot.get_channel(self.channel_id)
        self.store_latest_submission(submission.id)
        await channel.send('A new post has been submitted on /r/CassiopeiaMains!')
        
        # Create an embed for the submission type
        image_filetypes = ['.jpg', '.gif', '.png', '.bmp', '.tif']
        if submission.selftext == '':
            # Image Submission
            if submission.url[-4:] in image_filetypes:
                embed = self.create_embed(submission, tag='image')
            # Link Submission
            else:
                embed = self.create_embed(submission, tag='link')
        # Text Submission
        else:
            embed = self.create_embed(submission)
        
        # Finally send the embed to the channel
        await channel.send(embed=embed)

    # Take the submission id of the last posted message
    # and put it in reddit.json under 'submission_id'
    def store_latest_submission(self, submission_id):
        with open('reddit.json', 'w') as file:
            file.write(json.dumps({ 'submission_id': submission_id }))

    # Creates an embed of the reddit submission
    # Alters the embed based on the submission type
    # Stored in the tag parameter
    def create_embed(self, submission, tag='text'):
        if tag == 'image':
            embed = discord.Embed(color=self.embed_color, 
                                        title=submission.title[:256],
                                        url=f'https://www.reddit.com{submission.permalink}',
                                        timestamp=datetime.datetime.now())
            embed.set_image(url=submission.url)
            embed.set_thumbnail(url=submission.author.icon_img)
            embed.set_author(name=f'/u/{submission.author.name}')
            return embed
        elif tag == 'link':
            embed = discord.Embed(color=self.embed_color, 
                                  title=submission.title[:256],
                                  url=f'https://www.reddit.com{submission.permalink}',
                                  timestamp=datetime.datetime.now())
            embed.set_thumbnail(url=submission.author.icon_img)
            embed.set_author(name=f'/u/{submission.author.name}')
            return embed
        else:
            selftext = submission.selftext.replace('&#x200B;', '')
            embed = discord.Embed(color=self.embed_color, 
                                       title=submission.title[:256], 
                                       description=selftext[:2048],
                                       url=f'https://www.reddit.com{submission.permalink}',
                                       timestamp=datetime.datetime.now())
            embed.set_thumbnail(url=submission.author.icon_img)
            embed.set_author(name=f'/u/{submission.author.name}')
            return embed
