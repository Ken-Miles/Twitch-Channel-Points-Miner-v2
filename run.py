# -*- coding: utf-8 -*-

import logging
from colorama import Fore
from TwitchChannelPointsMiner import TwitchChannelPointsMiner
from TwitchChannelPointsMiner.logger import LoggerSettings, ColorPalette
from TwitchChannelPointsMiner.classes.Chat import ChatPresence
from TwitchChannelPointsMiner.classes.Discord import Discord
from TwitchChannelPointsMiner.classes.Telegram import Telegram
from TwitchChannelPointsMiner.classes.Settings import Priority, Events, FollowersOrder
from TwitchChannelPointsMiner.classes.entities.Bet import Strategy, BetSettings, Condition, OutcomeKeys, FilterCondition, DelayMode
from TwitchChannelPointsMiner.classes.entities.Streamer import Streamer, StreamerSettings
import environ

streamer_settings = StreamerSettings(
        make_predictions=True,                  # If you want to Bet / Make prediction
        follow_raid=True,                       # Follow raid to obtain more points
        claim_drops=True,                       # We can't filter rewards base on stream. Set to False for skip viewing counter increase and you will never obtain a drop reward from this script. Issue #21
        watch_streak=True,                      # If a streamer go online change the priority of streamers array and catch the watch screak. Issue #11
        chat=ChatPresence.ALWAYS,               # Join irc chat to increase watch-time [ALWAYS, NEVER, ONLINE, OFFLINE]
        bet=BetSettings(
            strategy=Strategy.SMART_MONEY,            # Choose you strategy!
            percentage=15,                       # Place the x% of your channel points
            percentage_gap=20,                  # Gap difference between outcomesA and outcomesB (for SMART strategy)
            max_points=25000,                   # If the x percentage of your channel points is gt bet_max_points set this value
            stealth_mode=True,                  # If the calculated amount of channel points is GT the highest bet, place the highest value minus 1-2 points Issue #33
            delay_mode=DelayMode.FROM_END,      # When placing a bet, we will wait until `delay` seconds before the end of the timer
            delay=6,
            minimum_points=4000,               # Place the bet only if we have at least 20k points. Issue #113
            filter_condition=FilterCondition(
                by=OutcomeKeys.ODDS_PERCENTAGE,     # Where apply the filter. Allowed [PERCENTAGE_USERS, ODDS_PERCENTAGE, ODDS, TOP_POINTS, TOTAL_USERS, TOTAL_POINTS]
                where=Condition.GTE,            # 'by' must be [GT, LT, GTE, LTE] than value
                value=70
            )
        )
)

env = environ.Env(
    current_user=str,
    port=(int, 4550),
    discord_webhook=str,
)

user = env('current_user')
if not user:
    raise ValueError("Must specify a current_user in env vars")

port = env('port')
discord_webhook = env('discord_webhook')

twitch_miner = TwitchChannelPointsMiner(
    username=str(user),

    claim_drops_startup=True,                  # If you want to auto claim all drops from Twitch inventory on the startup
    priority=[                                  # Custom priority in this case for example:
        Priority.STREAK,                        # - We want first of all to catch all watch streak from all streamers
        Priority.DROPS,                         # - When we don't have anymore watch streak to catch, wait until all drops are collected over the streamers
        Priority.ORDER                          # - When we have all of the drops claimed and no watch-streak available, use the order priority (POINTS_ASCENDING, POINTS_DESCEDING)
    ],
    logger_settings=LoggerSettings(
        save=True,                              # If you want to save logs in a file (suggested)
        console_level=logging.INFO,             # Level of logs - use logging.DEBUG for more info
        file_level=logging.DEBUG,               # Level of logs - If you think the log file it's too big, use logging.INFO
        emoji=True,                             # On Windows, we have a problem printing emoji. Set to false if you have a problem
        less=False,                             # If you think that the logs are too verbose, set this to True
        colored=True,                           # If you want to print colored text
        color_palette=ColorPalette(             # You can also create a custom palette color (for the common message).
            STREAMER_online="GREEN",            # Don't worry about lower/upper case. The script will parse all the values.
            streamer_offline="red",             # Read more in README.md
            BET_wiN=Fore.MAGENTA                # Color allowed are: [BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET].
        ),
        #telegram=Telegram(                                                          # You can omit or leave None if you don't want to receive updates on Telegram
        #    chat_id=123456789,                                                      # Chat ID to send messages @GiveChatId
        #    token="123456789:shfuihreuifheuifhiu34578347",                          # Telegram API token @BotFather
        #    events=[Events.STREAMER_ONLINE, Events.STREAMER_OFFLINE, "BET_LOSE"],   # Only these events will be sent to the chat
        #    disable_notification=True,                                              # Revoke the notification (sound/vibration)
        #),
        discord=Discord(
            webhook_api=str(discord_webhook),  # Discord Webhook URL
            events=[Events.STREAMER_ONLINE, Events.STREAMER_OFFLINE, Events.BET_WIN, Events.BET_REFUND, Events.BET_START, Events.BET_FAILED, Events.BET_LOSE, Events.CHAT_MENTION],       # Only these events will be sent to the chat
        )
    ),
    streamer_settings=streamer_settings,
    enable_analytics=True
)

# You can customize the settings for each streamer. If not settings were provided, the script would use the streamer_settings from TwitchChannelPointsMiner.
# If no streamer_settings are provided in TwitchChannelPointsMiner the script will use default settings.
# The streamers array can be a String -> username or Streamer instance.

# The settings priority are: settings in mine function, settings in TwitchChannelPointsMiner instance, default settings.
# For example, if in the mine function you don't provide any value for 'make_prediction' but you have set it on TwitchChannelPointsMiner instance, the script will take the value from here.
# If you haven't set any value even in the instance the default one will be used

twitch_miner.analytics(host="127.0.0.1", port=int(port), refresh=5, days_ago=7)   # Analytics web-server

streamers = []

with open('channels.txt') as f:
    for line in f:
        # Remove anything after a '#' and strip whitespace
        cleaned_line = line.split('#')[0].strip()
        if cleaned_line:  # Ensure line isn't empty
            streamers.append(cleaned_line.lower().strip())


bans = {
    'caseoh_': ['ken_miles9067', 'formeraidensassistant'],
}

for channel, banned_users in bans.items():
    if channel.lower() not in streamers:
        continue

    if twitch_miner.username.lower() in banned_users:
        streamers.remove(channel)

if twitch_miner.username.lower() in streamers:
    streamers.remove(twitch_miner.username.lower())

streamer_list = [Streamer(x, settings=streamer_settings) for x in streamers]

# streamer_list = []

# for x in streamers:
#     streamer_list.append(
#         Streamer(x, settings=streamer_settings)
#     )

twitch_miner.mine(
    streamer_list,
)