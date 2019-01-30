# -*- coding: utf-8 -*-

import discord
import yaml
import asyncio
from datetime import datetime, date, time, timedelta


class DnmBotClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.RUN_CYCLE = 5 # todo ->60
        self.__DISCORD_TOKEN = kwargs['tokens']['discord_bot']
        self.events = kwargs['events']
        
        self.general_channels = []
        self.daily_channels = []
        self.event_channels = []
        
        self.bg_task = self.loop.create_task(self.start_bg_tasks())
    
    async def on_ready(self):
        print('logged in as')
        print(self.user.name)
        print(self.user.id)
        print('-------')
        
    async def daily_update(self):
        """
        Update today's event information from event table.
        """
        pass
    
    async def start_bg_tasks(self):
        await self.wait_until_ready()
        await self.update_server_and_channel_info()
        await self.notificator()
        
    async def update_server_and_channel_info(self):
        # self.servers_list = [server for server in self.servers]
        # todo is it better to run this func every RUN_CYCLE?
        # get channels from each server, or create channel if not exists.
        for server in self.servers:
            check_general = [ch for ch in server.channels if ch.name == 'general']
            check_daily = [ch for ch in server.channels if ch.name == 'daily-announcements']
            check_event = [ch for ch in server.channels if ch.name == 'event-alarm']
            try:
                self.general_channels.append(check_general[0])
            except IndexError:
                try:
                    ch_created = await self.create_channel(server, 'general', type=discord.ChannelType.text)
                except discord.Forbidden:
                    pass
                else:
                    if isinstance(ch_created, discord.channel.Channel):
                        self.general_channels.append(ch_created)
            try:
                self.daily_channels.append(check_daily[0])
            except IndexError:
                try:
                    ch_created = await self.create_channel(server, 'daily-announcements', type=discord.ChannelType.text)
                except discord.Forbidden:
                    pass
                else:
                    if isinstance(ch_created, discord.channel.Channel):
                        self.daily_channels.append(ch_created)
            try:
                self.event_channels.append(check_event[0])
            except IndexError:
                try:
                    ch_created = await self.create_channel(server, 'event-alarm', type=discord.ChannelType.text)
                except discord.Forbidden:
                    pass
                else:
                    if isinstance(ch_created, discord.channel.Channel):
                        self.event_channels.append(ch_created)
        print('Found these channels:')
        for ch in self.general_channels:
            print(f'channel: {ch.name} on server: {ch.server.name}')
        for ch in self.daily_channels:
            print(f'channel: {ch.name} on server: {ch.server.name}')
        for ch in self.event_channels:
            print(f'channel: {ch.name} on server: {ch.server.name}')
        print('Updated server and channel info.')
    
    async def notificator(self):
        channel = self.general_channels[0]
        while not self.is_closed:
            dt_now = datetime.now()
            dt_daily = datetime.combine(date.today(), time(8, 30, 0, 0))
            dif_daily = dt_daily - dt_now
            if dif_daily < timedelta(seconds=self.RUN_CYCLE) and dif_daily > timedelta():
                # await self.daily_update()
                await self.send_message(channel, 'message from dnm_bot.')
                
                
        
            await asyncio.sleep(self.RUN_CYCLE)
    
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
    client.run(config['tokens']['discord_bot'])

