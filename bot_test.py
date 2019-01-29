import discord
import yaml
import asyncio
from datetime import datetime, date, time, timedelta

class DnmBotClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.DISCORD_TOKEN = kwargs['tokens']['discord_bot']
        self.GENERAL_ID = kwargs['channel_ids']['general']
        self.bg_task = self.loop.create_task(self.notificator())

        
    async def on_ready(self):
        print('logged in as')
        print(self.user.name)
        print(self.user.id)
        print('-------')
        
    async def notificator(self):
        await self.wait_until_ready()
        counter = 0
        channel = self.get_channel(str(self.GENERAL_ID))
        while not self.is_closed:
            counter += 1
            await self.send_message(channel, 'message from dnm_bot.')
            await asyncio.sleep(10)
            
    async def on_message(self, message):
        if message.content.startswith('/foo'):
            reply = 'bar'
            await self.send_message(message.channel, reply)



#
# @client.event
# async def on_ready():
#     print('dnm_bot  logged in as')
#     print(client.user.name)
#     print(client.user.id)
#     print('-------')
#
#
# @client.event
# async def on_message(message):
#     if message.content.startswith('/foo'):
#         reply = 'bar'
#         await client.send_message(message.channel, reply)
        
    
    
if __name__ == '__main__':
    with open('./config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    client = DnmBotClient(**config)
    client.run(client.DISCORD_TOKEN)
    
    