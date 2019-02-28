# -*- coding: utf-8 -*-

import discord
import yaml
import asyncio
from datetime import datetime, date, time, timedelta
import pytz
import os

class DnmBotClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.RUN_CYCLE = 15 # seconds
        self.ALARM_OFFSET = 15 # minutes
        # self.__DISCORD_TOKEN = kwargs['tokens']['discord_bot']
        self.events = kwargs['events']
        self.days = kwargs['days']
        
        self.general_channels = []
        self.daily_channels = []
        self.event_channels = []
        self.voice_channels = []
        self.is_someone_in_vc = []
        
        self.events_today = []
        self.daily_announce_time = time(8, 0, 0, 0) # hour, minute, second, microsecond
        
        self.days_replace = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        self.bg_task = self.loop.create_task(self.start_bg_tasks())
        
        self.conan = ['なんやて', 'もろたで', 'せやかて', 'いけるで', 'なんやと', 'せやけど', 'せやろか', 'あかんて']
    
    async def _send_message(self, ch, msg):
        if not isinstance(ch, discord.channel.Channel):
            raise ValueError
        try:
            await self.send_message(ch, msg)
        except discord.Forbidden:
            print('You need to grant permission to send message to'
                  f' {ch.name} on {ch.server.name}')
            pass
        except discord.NotFound:
            print(f'Not Found {ch.name} on {ch.server.name}')
            pass
        except discord.HTTPException:
            print(f'HTTPException {ch.name} on {ch.server.name}')
            pass

    async def on_ready(self):
        print('logged in as')
        print(self.user.name)
        print(self.user.id)
        print('-------')
        
    async def daily_update(self):
        """
        Update today's event information from event table.
        """
        tz_jpn = pytz.timezone('Asia/Tokyo')
        dt_now = datetime.now(tz_jpn)
        weekday = dt_now.weekday()
        # self.events_today.clear()
        self.events_today = self.days[self.days_replace[weekday]]
        print('events_today updated')
        print(self.events_today)
    
    async def start_bg_tasks(self):
        await self.wait_until_ready()
        await self.daily_update()
        await self.bg_loop()
        
    async def update_server_and_channel_info(self):
        """
        Get channels[general, daily-announcements, event-alarm] from joined servers, or create channel if not exists.
        """
        self.general_channels.clear()
        self.daily_channels.clear()
        self.event_channels.clear()
        self.voice_channels.clear()
        for server in self.servers:
            check_general = [ch for ch in server.channels
                             if (ch.name == 'general' and ch.type == discord.ChannelType.text)]
            check_daily = [ch for ch in server.channels
                           if (ch.name == 'daily-announcements' and ch.type == discord.ChannelType.text)]
            check_event = [ch for ch in server.channels
                           if (ch.name == 'event-alarm' and ch.type == discord.ChannelType.text)]
            if len(check_general) != 0:
                self.general_channels.append(check_general[0])
            else:
                try:
                    ch_created = await self.create_channel(server, 'general', type=discord.ChannelType.text)
                except discord.Forbidden:
                    print(f'You need to grant permission to create channel on {server.name}')
                    pass
                except discord.NotFound:
                    print(f'Not Found {server.name}')
                    pass
                except discord.HTTPException:
                    print(f'HTTPException {server.name}')
                    pass
                else:
                    if isinstance(ch_created, discord.channel.Channel):
                        self.general_channels.append(ch_created)
            if len(check_daily) != 0:
                self.daily_channels.append(check_daily[0])
            else:
                try:
                    ch_created = await self.create_channel(server, 'daily-announcements', type=discord.ChannelType.text)
                except discord.Forbidden:
                    pass
                except discord.NotFound:
                    pass
                except discord.HTTPException:
                    pass
                else:
                    if isinstance(ch_created, discord.channel.Channel):
                        self.daily_channels.append(ch_created)
            if len(check_event) != 0:
                self.event_channels.append(check_event[0])
            else:
                try:
                    ch_created = await self.create_channel(server, 'event-alarm', type=discord.ChannelType.text)
                except discord.Forbidden:
                    pass
                except discord.NotFound:
                    pass
                except discord.HTTPException:
                    pass
                else:
                    if isinstance(ch_created, discord.channel.Channel):
                        self.event_channels.append(ch_created)
            check_voice = [ch for ch in server.channels if ch.type == discord.ChannelType.voice]
            self.voice_channels.extend(check_voice)
            
        print('Found these channels:')
        for ch in self.general_channels:
            print(f'text channel: {ch.name} on server: {ch.server.name}')
        for ch in self.daily_channels:
            print(f'text channel: {ch.name} on server: {ch.server.name}')
        for ch in self.event_channels:
            print(f'text channel: {ch.name} on server: {ch.server.name}')
        for ch in self.voice_channels:
            print(f'voice channel: {ch.name} on server: {ch.server.name}')
        print('Updated server and channel info.')
    
    async def bg_loop(self):
        while not self.is_closed:
            await self.update_server_and_channel_info()
            await self.check_vc_status()
            tz_jpn = pytz.timezone('Asia/Tokyo')
            dt_now = datetime.now(tz_jpn)
            print('###############')
            print(dt_now)
            print('###############')

            # event update
            dt_event_update = datetime.combine(dt_now, time(5, 0, 0, 0))
            dt_event_update = tz_jpn.localize(dt_event_update, is_dst=False)
            dif_event_update = dt_event_update - dt_now
            if dif_event_update < timedelta(seconds=self.RUN_CYCLE) and dif_event_update >= timedelta():
                await self.daily_update()
            
            # daily announce
            dt_daily_announce = datetime.combine(dt_now, self.daily_announce_time)
            dt_daily_announce = tz_jpn.localize(dt_daily_announce, is_dst=False)
            dif_daily_announce = dt_daily_announce - dt_now
            if dif_daily_announce < timedelta(seconds=self.RUN_CYCLE) and dif_daily_announce >= timedelta():
                await self.daily_update()
                await self.send_daily_announcement()
            
            # event alarm
            for event in self.events_today:
                dt_event = self.get_event_datetime(event_name=event)
                if dt_event is None:
                    continue
                dt_event = dt_event - timedelta(minutes=self.ALARM_OFFSET)
                dif_event = dt_event - dt_now
                if dif_event < timedelta(seconds=self.RUN_CYCLE) and dif_event >= timedelta():
                    await self.send_event_alarm(event)
            
            # sleep
            dt_now = datetime.now(tz_jpn)
            print(f'All operations in this loop ended at {dt_now}')
            await asyncio.sleep(self.RUN_CYCLE)
            dt_now = datetime.now(tz_jpn)
            print(f'The loop ended at {dt_now}')
            
    async def send_daily_announcement(self):
        """
        Send daily announcement message to the 'daily-announcements' channel
        """
        for ch in self.daily_channels:
            msg = '今日のイベント：\n'
            for event in self.events_today:
                dt_event = self.get_event_datetime(event_name=event)
                if dt_event is None:
                    msg = msg + self.events[event]['name'] + '\n'
                else:
                    msg = msg + dt_event.strftime('%H:%M~') + ' ' + self.events[event]['name'] +'\n'
                    
            await self._send_message(ch, msg)
            
    async def send_event_alarm(self, event_name):
        """
        Send event alarm message to the 'event-alarm' channel
        """
        for ch in self.event_channels:
            msg = self.events[event_name]['name'] + ' 開始' + str(self.ALARM_OFFSET) + '分前です\n'
            await self._send_message(ch, msg)
            
    def get_event_datetime(self, event_name):
        tz = pytz.timezone('Asia/Tokyo')
        try:
            start_time = self.events[event_name]['time']
        except KeyError:
            return None
        start_hour, start_minute = start_time.split('_')
        dt_event = datetime.combine(date.today(), time(int(start_hour), int(start_minute), 0, 0))
        dt_event = tz.localize(dt_event, is_dst=False)
        return dt_event
    
    async def check_vc_status(self):
        """
        Check status of voice channels and compare current/previous status
        """
        vc_status_now = [len(ch.voice_members) != 0 for ch in self.voice_channels]
        if len(vc_status_now) == len(self.is_someone_in_vc):
            for now, prev, ch in zip(vc_status_now, self.is_someone_in_vc, self.voice_channels):
                if now is True and  prev is False:
                    await self.notify_someone_in_vc(ch)

        self.is_someone_in_vc = vc_status_now
    
    async def notify_someone_in_vc(self, ch):
        """
        Send notification about voice channels
        """
        if not isinstance(ch, discord.channel.Channel):
            raise ValueError
        member_name = []
        for mem in ch.voice_members:
            member_name.append(mem.name)
        msg = str(member_name).strip('[]') + f" さんがボイスチャンネル '{ch.name}' に入りました"
        ch_general = None
        for gen in self.general_channels:
            if gen.server == ch.server:
                ch_general = gen
        if ch_general is None:
            print(f"There is no 'general' server in {ch.server}")
            return
        await self._send_message(ch_general, msg)
        
    async def on_message(self, message):
        if message.content.startswith('/foo'):
            reply = 'bar'
            await self._send_message(message.channel, reply)
            
        if message.content.startswith('/kick_dnm_bot'):
            reply = 'GG'
            await self._send_message(message.channel, reply)
            await self.leave_server(message.server)
            

        for word in self.conan:
            if message.content.startswith(word):
                reply = '工藤！'
                await self._send_message(message.channel, reply)

if __name__ == '__main__':
    with open('./config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    client = DnmBotClient(**config)
    TOKEN = os.environ['BOT_TOKEN'] # Use your own token.
    client.run(TOKEN)

