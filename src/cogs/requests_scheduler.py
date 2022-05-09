import requests
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc
import json
import sys
import time
from discord.ext import commands
from discord import Embed
from src.utils.json_load import read_json
import discord
from discord.ext.tasks import loop
import datetime

class RequestsScheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduler.start()

    config_json_file_name = "scheduler_cogs"
    requests_json_file_name = "requests_logs"
    scheduler = BackgroundScheduler()
    one_day_in_milliseconds = 86400000
    test = 0
    count = 0

    #sn - as Scheduler
    @commands.group(aliases=['sn'], invoke_without_command=True, description="Scheduler nofity commands")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def notify(self, ctx):
        await ctx.invoke(self.bot.get_command("help"), entity="notify")

    @notify.command(name="params_info", description="Print all set parameters")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def params_info(self, ctx):
        guilds_config_params = self.get_json_content(self.config_json_file_name)
        params_exits = False
        guild_name = str(ctx.guild)
        for params in guilds_config_params:
            params_guild_name = params['quild_name']
            if params_guild_name == guild_name:
                params_exits = True
                description_text = "All set params"
                description_text += "\n* requests_api_url : " + params['requests_api_url']
                description_text += "\n* requests_subject_shortcut : " + params['requests_subject_shortcut']
                description_text += "\n* requests_time_minutes : " + params['requests_time_minutes']
                description_text += "\n* request_is_running : " + params['request_is_running']
                description_text += "\n* notify_info_channels : "
                if len(params['notify_info_channels']) > 0:
                    for info_channel in params['notify_info_channels']:
                        description_text += "\n .... " + info_channel
                else:
                    description_text += "empty"
                description_text += "\n* notify_system_error_channels : "
                if len(params['notify_system_error_channels']) > 0:
                    for error_channel in params['notify_system_error_channels']:
                        description_text += "\n .... " + error_channel
                else:
                    description_text += "empty"
                embed = Embed(title="Parameters info for guild " + guild_name, color=0x00FFFF, description=description_text)
                await ctx.send(embed=embed)
        if not params_exits:
            description_text = "There are NOT set notify params for this guild"
            embed = Embed(title="Parameter info - ERROR", color=0xFF0000, description=description_text)
            await ctx.send(embed=embed)

    @notify.command(name="set_api_url", description="Set new Api URL")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def set_api_url(self, ctx, *args):
        #Validate set Api URL
        valid, error_text = self.validate_api_url(args)
        if valid:
            self.update_add_config_params(args[0], ctx, 'requests_api_url')
            embed = Embed(title="Set Api URL", color=0x7CFC00, description="Api URL changed successfuly")
            await ctx.send(embed=embed)
        else:
            embed = Embed(title="Set Api URL - ERROR", color=0xFF0000, description=error_text)
            await ctx.send(embed=embed)

    @notify.command(name="set_requests_time_minutes", description="Set interval how often API will be called in minutes (>= 1)")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def set_requests_time_minutes(self, ctx, *args):
        # Validate set request time in minutes
        valid, error_text = self.validate_request_time_minutes(args)
        if valid:
            self.update_add_config_params(args[0], ctx, 'requests_time_minutes')
            embed = Embed(title="Set requests interval", color=0x7CFC00, description="Interval value changed successfuly")
            await ctx.send(embed=embed)
        else:
            embed = Embed(title="Set requests interval - ERROR", color=0xFF0000, description=error_text)
            await ctx.send(embed=embed)

    @notify.command(name="set_requests_subject_shortcut", description="Set shortcut of wanted subject")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def set_requests_subject_shortcut(self, ctx, *args):
        # Validate set subject shortcut
        valid, error_text = self.validate_request_subject_shortcut(args)
        if valid:
            self.update_add_config_params(args[0], ctx, 'requests_subject_shortcut')
            embed = Embed(title="Set subject shortcut", color=0x7CFC00, description="Subject shortcut changed successfuly")
            await ctx.send(embed=embed)
        else:
            embed = Embed(title="Set subject shortcut - ERROR", color=0xFF0000, description=error_text)
            await ctx.send(embed=embed)

    @notify.command(name="set_start_stop_requesting", description="Start requesting using param : true , stop requesting using param : false")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def set_start_stop_requesting(self, ctx, *args):
        valid, error_text, start = self.validate_request_is_running(args)
        if valid:
            valid, error_text = self.start_stop_requesting(ctx, args[0])
            if valid:
                if start:
                    embed = Embed(title="Set subject shortcut", color=0x7CFC00, description="Requesting started successfuly")
                else:
                    embed = Embed(title="Set subject shortcut", color=0x7CFC00, description="Requesting stoped successfuly")
                await ctx.send(embed=embed)
            else:
                embed = Embed(title="Start/stop requesting - ERROR", color=0xFF0000, description=error_text)
                await ctx.send(embed=embed)
        else:
            embed = Embed(title="Start/stop requesting - ERROR", color=0xFF0000, description=error_text)
            await ctx.send(embed=embed)

    @notify.command(name="add_notify_info_channels", description="Add channels where new nofications will be printed")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def add_notify_info_channels(self, ctx, *args):
        if len(args) < 1:
            embed = Embed(title="Add notify channels - ERROR", color=0xFF0000, description="You need add at least one channel")
            await ctx.send(embed=embed)
        else:
            for channel in args:
                valid, error_text = self.validate_channel(ctx, channel)
                if valid:
                    valid, error_text = self.update_add_config_params(channel, ctx, "notify_info_channels")
                    if valid:
                        embed = Embed(title="Add notify info channel", color=0x7CFC00,
                                      description="This channel added succesfuly : " + channel)
                        await ctx.send(embed=embed)
                    else:
                        error_text += channel
                        embed = Embed(title="Add notify channels - ERROR", color=0xFF0000, description=error_text)
                        await ctx.send(embed=embed)
                else:
                    error_text +=  channel
                    embed = Embed(title="Add notify channels - ERROR", color=0xFF0000, description=error_text)
                    await ctx.send(embed=embed)

    @notify.command(name="add_notify_system_error_channels", description="Add channels where new system errors will be printed")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def add_notify_system_error_channels(self, ctx, *args):
        if len(args) < 1:
            embed = Embed(title="Add system error channels - ERROR", color=0xFF0000, description="You need add at least one channel")
            await ctx.send(embed=embed)
        else:
            for channel in args:
                valid, error_text = self.validate_channel(ctx, channel)
                if valid:
                    valid, error_text = self.update_add_config_params(channel, ctx, "notify_system_error_channels")
                    if valid:
                        embed = Embed(title="Add notify system error channel", color=0x7CFC00,
                                      description="This channel added succesfuly : " + channel)
                        await ctx.send(embed=embed)
                    else:
                        error_text += channel
                        embed = Embed(title="Add system error channels - ERROR", color=0xFF0000, description=error_text)
                        await ctx.send(embed=embed)
                else:
                    error_text +=  channel
                    embed = Embed(title="Add system error channels - ERROR", color=0xFF0000, description=error_text)
                    await ctx.send(embed=embed)

    @notify.command(name="remove_notify_info_channels", description="Remove channels where new nofications will be printed from arr")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def remove_notify_info_channels(self, ctx, *args):
        if len(args) < 1:
            embed = Embed(title="Remove notify info channels - ERROR", color=0xFF0000, description="You need add at least one channel")
            await ctx.send(embed=embed)
        else:
            for channel in args:
                valid, error_text = self.remove_channel(ctx, channel, "notify_info_channels")
                if valid:
                    embed = Embed(title="Remove notify info channel", color=0x7CFC00,
                                  description="This channel was removed succesfuly : " + channel)
                    await ctx.send(embed=embed)
                else:
                    error_text += channel
                    embed = Embed(title="Remove notify info channel - ERROR", color=0xFF0000, description=error_text)
                    await ctx.send(embed=embed)

    @notify.command(name="remove_notify_system_error_channels", description="Remove channels where new nofications will be printed from arr")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def remove_notify_system_error_channels(self, ctx, *args):
        if len(args) < 1:
            embed = Embed(title="Remove notify system error channels - ERROR", color=0xFF0000, description="You need add at least one channel")
            await ctx.send(embed=embed)
        else:
            for channel in args:
                valid, error_text = self.remove_channel(ctx, channel, "notify_system_error_channels")
                if valid:
                    embed = Embed(title="Remove notify system error channel", color=0x7CFC00,
                                  description="This channel was removed succesfuly : " + channel)
                    await ctx.send(embed=embed)
                else:
                    error_text += channel
                    embed = Embed(title="Remove notify system error channel - ERROR", color=0xFF0000, description=error_text)
                    await ctx.send(embed=embed)

    def remove_channel(self, ctx, remove_channel, channel_type):
        valid = True
        error_text = ""
        guilds_config_params = self.get_json_content(self.config_json_file_name)
        params_exits = False
        guild_name = str(ctx.guild)
        for params in guilds_config_params:
            params_guild_name = params['quild_name']
            # Params for this guild exits, just update
            if params_guild_name == guild_name:
                if len(params[channel_type]) > 0:
                    for channel in params[channel_type]:
                        if channel == remove_channel:
                            params[channel_type].remove(remove_channel)
                            self.update_json(guilds_config_params, self.config_json_file_name)
                            return valid, error_text
        valid = False
        error_text = "This channel doesnt belong to notify_info_channels : "
        return valid, error_text

    def validate_channel(self, ctx, add_channel):
        valid = False
        error_text = ""
        guilds = self.bot.guilds
        for guild in guilds:
            if guild == ctx.guild:
                for channel in guild.channels:
                    if str(channel) == add_channel:
                        valid = True
                        return valid, error_text
        error_text = "This channel doesnt exist in this quild : "
        return valid, error_text

    def start_stop_requesting(self, ctx, action):
        valid = True
        error_message = ""
        guilds_config_params = self.get_json_content(self.config_json_file_name)
        params_exits = False
        guild_name = str(ctx.guild)
        for params in guilds_config_params:
            params_guild_name = params['quild_name']
            # Params for this guild exits
            if params_guild_name == guild_name:
                # Check if all params are set (no empty value)
                if self.check_if_empty(params):
                    error_message = "To run this operation all params must be set."
                    valid = False
                    return valid, error_message
                else:
                    #We are here- means all params arent empty
                    #Now check if operation is same
                    if params['request_is_running'] == action:
                        #Same action throw error
                        valid = False
                        if action == "true":
                            error_message = "Requesting is already running !"
                        else:
                            error_message = "Requesting is already stoped !"
                        return valid, error_message
                    else:
                        # We found params, all params are set, and action is new
                        # Change action
                        params['request_is_running'] = action
                        # Update config json
                        self.update_json(guilds_config_params, self.config_json_file_name)
                        return valid, error_message
        #No params for this guild
        error_message = "To run this operation all params must be set."
        valid = False
        return valid, error_message


    def check_if_empty(self, params_to_check):
        empty = False
        if params_to_check['quild_name'] == 'empty':
            empty = True
        elif params_to_check['requests_api_url'] == 'empty':
            empty = True
        elif params_to_check['requests_subject_shortcut'] == 'empty':
            empty = True
        elif params_to_check['requests_time_minutes'] == 'empty':
            empty = True
        elif params_to_check['request_is_running'] == 'empty':
            empty = True
        elif len(params_to_check['notify_info_channels']) < 1:
            empty = True
        elif len(params_to_check['notify_system_error_channels']) < 1:
            empty = True
        return empty

    def validate_request_is_running(self, args):
        valid = False
        error_text = ""
        start = False
        if len(args) < 1:
            error_text = "Start/stop requesting params cannot be empty"
            return valid, error_text, start
        else:
            if args[0] == "true":
                valid = True
                start = True
            elif args[0] == "false":
                valid = True
                start = False
            else:
                error_text = "Start/stop requesting params had wrong format."
        return valid, error_text, start

    def validate_api_url(self, args):
        valid = False
        error_text = ""
        if len(args) < 1:
            error_text = "Api URL cannot be empty"
            return valid, error_text
        else:
            if args[0].startswith('https://'):
                valid = True
                pass
            elif args[0].startswith('http://'):
                valid = True
                pass
            else:
                error_text = "Api URL had wrong format. Api must start with https:// or http://"
        return valid, error_text

    def validate_request_time_minutes(self, args):
        valid = False
        error_text = ""
        if len(args) < 1:
            error_text = "Interval cannot be empty"
            return valid, error_text
        if not args[0].isdecimal():
            error_text = "Interval value can contain only numbers"
            return valid, error_text
        if int(args[0]) < 1:
            error_text = "Interval value MUST be bigger or equal 1"
            return valid, error_text
        valid = True
        return valid, error_text

    def validate_request_subject_shortcut(self, args):
        valid = False
        error_text = ""
        if len(args) < 1:
            error_text = "subject shortcut cannot be empty"
            return valid, error_text
        valid = True
        return valid, error_text

    def create_new_param_form(self, guild_name):
        new_params = {
            "quild_name": guild_name,
            "requests_api_url": "empty",
            "requests_subject_shortcut": "empty",
            "requests_time_minutes": "empty",
            "request_is_running": "false",
            "notify_info_channels": [],
            "notify_system_error_channels": [],
            "minutes_from_last_request_call": "0"
        }
        return new_params

    def update_add_config_params(self, new_value, ctx, param_name):
        valid = True
        error_text = ""
        guilds_config_params = self.get_json_content(self.config_json_file_name)
        params_exits = False
        guild_name = str(ctx.guild)
        for params in guilds_config_params:
            params_guild_name = params['quild_name']
            # Params for this guild exits, just update
            if params_guild_name == guild_name:
                params_exits = True
                if param_name == "notify_info_channels":
                    if len(params[param_name]) > 0:
                        for channel in params[param_name]:
                            if channel == new_value:
                                valid = False
                                error_text = "This channel is already in notify_info_channels : "
                                return valid, error_text
                    #This channel is valid and not allready in arr
                    params[param_name].append(new_value)
                    self.update_json(guilds_config_params, self.config_json_file_name)
                    return valid, error_text
                elif param_name == "notify_system_error_channels":
                    if len(params[param_name]) > 0:
                        for channel in params[param_name]:
                            if channel == new_value:
                                valid = False
                                error_text = "This channel is already in notify_system_error_channels : "
                                return valid, error_text
                    #This channel is valid and not allready in arr
                    params[param_name].append(new_value)
                    self.update_json(guilds_config_params, self.config_json_file_name)
                    return valid, error_text
                else:
                    # Update config json
                    params[param_name] = new_value
                    self.update_json(guilds_config_params, self.config_json_file_name)
        # Params for this guild doesny exists
        if not params_exits:
            # Create new param record
            if param_name == 'notify_info_channels':
                new_params = self.create_new_param_form(guild_name)
                new_params[param_name].append(new_value)
            elif param_name == 'notify_system_error_channels':
                new_params = self.create_new_param_form(guild_name)
                new_params[param_name].append(new_value)
            else:
                new_params = self.create_new_param_form(guild_name)
                new_params[param_name] = new_value
            guilds_config_params.append(new_params)
            # Update config json
            self.update_json(guilds_config_params, self.config_json_file_name)
            return valid, error_text

    # Return set configurations from json
    def get_json_content(self, json_file_name):
        try:
            # Reading from json file
            return read_json(json_file_name)
        except ValueError:
            # File is empty or data are corrupted, clear file
            self.clear_json_file(json_file_name)
            # Return empty array
            return []
        except:
            # Fatal problem occured
            print("ERROR!", sys.exc_info()[0], "occurred.")
            return -1

    def update_json(self, content, json_file_name):
        with open("configs/" + json_file_name +".json", "w") as outfile:
            outfile.write(self.return_serialize_json(content))

    # Create and return a formatted string of the Python JSON object
    def return_serialize_json(self, obj):
        text = json.dumps(obj, sort_keys=True, indent=4)
        return text

    # Clear JSON file (write empty array)
    def clear_json_file(self, json_file_name):
        with open("configs/" + json_file_name + ".json", "w") as outfile:
            outfile.write(self.return_serialize_json([]))

    def return_status_code_message(status_code):
        if status_code == 200:
            return "Request okay, result has been returned."
        elif status_code == 301:
            return "The server is redirecting you to a different endpoint."
        elif status_code == 400:
            return "The server thinks you made a bad request."
        elif status_code == 401:
            return "The server thinks youre not authenticated."
        elif status_code == 403:
            return "The resource youre trying to access is forbidden: you dont have the right permissions to see it."
        elif status_code == 404:
            return "The resource you tried to access wasnt found on the server."
        elif status_code == 500:
            return "The server is not ready to handle the request."

    # Return True if two requests logs are same - or return False
    def compare_req_logs(self, log_a, log_b):
        if(log_a["subjectShortcut"] != log_b["subjectShortcut"]):
            return False
        if(log_a["updatedPage"] != log_b["updatedPage"]):
            return False
        if(log_a["updatedPageLink"] != log_b["updatedPageLink"]):
            return False
        if(log_a["updateDateTime"] != log_b["updateDateTime"]):
            return False
        return True

    # Return saved logs from file requests_logs.json
    def return_requests_logs(self):
        try:
            # Reading from json file
            return read_json("requests_logs")
        except ValueError:
            # File is empty or data are corrupted, clear file
            self.clear_json_file(self.requests_json_file_name)
            # Return empty array
            return []
        except:
            # Fatal problem occured
            print("ERROR!", sys.exc_info()[0], "occurred.")
            return -1

    # Chceck if array of requests logs already include this "request_log"
    def check_if_include(self, requests_logs, request_log):
        if len(requests_logs) == 0:
            return False
        else:
            for req_log in requests_logs:
                if self.compare_req_logs(req_log, request_log):
                    return True

        return False

    # Obviously return current milliseconds :D
    def return_current_milliseconds(self):
        return round(time.time() * 1000)

    # Return request log only if updateDateTime is NOT older than 24 hours
    def return_valid_requests_logs(self, requests_logs):
        valid_req_logs = []
        if len(requests_logs) > 0:
            for req_log in requests_logs:
                datetime_diff = self.return_current_milliseconds() - int(req_log["updateDateTime"])
                if datetime_diff < self.one_day_in_milliseconds:
                    valid_req_logs.append(req_log)
        return valid_req_logs

    # Send notification for student
    # New response mean -> there is something
    async def send_notification(self, response, guild_params):
        notify_channels = guild_params['notify_info_channels']
        guilds = self.bot.guilds
        for guild in guilds:
            if str(guild) == guild_params['quild_name']:
                channels = guild.channels
                for channel in channels:
                    for notify_channel in notify_channels:
                        if str(channel) == notify_channel:
                            description_text = "\n *Website name : " + response['updatedPage']
                            description_text += "\n *Website url : " + response['updatedPageLink']
                            description_text += "\n *Subject shortcut : " + response['subjectShortcut']
                            miliseconds  = int(response['updateDateTime'])
                            description_text += "\n *Update date time : " + str(datetime.datetime.fromtimestamp(miliseconds/1000.0)).split('.')[0]
                            embed = Embed(title="New contentent on subject " + response['subjectShortcut'] + " website", color=0x00FFFF, description=description_text)
                            await channel.send(embed=embed)

    # Send notification / warning for admins
    # Something go wrong during process
    def send_warning(self, message, guild_params):
        notify_channels = guild_params['notify_info_channels']
        guilds = self.bot.guilds
        for guild in guilds:
            if str(guild) == guild_params['quild_name']:
                channels = guild.channels
                for channel in channels:
                    for notify_channel in notify_channels:
                        if str(channel) == notify_channel:
                            embed = Embed(title="Error occured during process", color=0x7CFC00, description=message)
                            await channel.send(embed=embed)

    async def get_guilds_request(self):
        guilds_config_params = self.get_json_content(self.config_json_file_name)
        if len(guilds_config_params) > 0:
            for guild_params in guilds_config_params:
                if guild_params['request_is_running'] == 'true':
                    last_time = int(guild_params['minutes_from_last_request_call']) + 1
                    #Check if is time to get request
                    request_time = int(guild_params['requests_time_minutes'])
                    if last_time >= request_time:
                        await self.get_request(guild_params)
                        guild_params['minutes_from_last_request_call'] = "0"
                    else:
                        guild_params['minutes_from_last_request_call'] = str(last_time)
        #Update times of last requests
        self.update_json(guilds_config_params, self.config_json_file_name)

    async def get_request(self, config):
        # Here set url of api
        response = requests.get(config['requests_api_url'])

        # Get response status code
        status_code = response.status_code

        # Get JSON
        response_json = response.json()

        if status_code == 200:
            if response_json == 0:
                # There is no requests logs to handle
                return
            else:
                # Get requests logs
                requests_logs = self.return_requests_logs()

                # Validate returned logs
                valid_requests_logs = self.return_valid_requests_logs(requests_logs)

                # Create copy of valid logs (we will append here new logs)
                logs_for_save = valid_requests_logs

                # Loop response json
                for response in response_json:
                    is_new = True

                    # Handle only requests about our choosen subject
                    if response["subjectShortcut"] == config['requests_subject_shortcut']:
                        datetime_diff = self.return_current_milliseconds() - int(response["updateDateTime"])
                        # Handle only requests NOT older than 24 hours (add because of savefty reasons)
                        if datetime_diff < self.one_day_in_milliseconds:
                            # Loop all exist logs (no older than 1 day)
                            for req_log in valid_requests_logs:
                                if self.compare_req_logs(response, req_log):
                                    # Log for this response allready exist
                                    is_new = False
                            # If there is no log for this response, it must be new
                            if is_new:
                                # Notify this response
                                await self.send_notification(response, config)
                                # Add new log for this response
                                logs_for_save.append(response)
                # Save new array of requests logs
                self.update_json(logs_for_save, self.requests_json_file_name)
        else:
            # Get message explained status code
            message = self.return_status_code_message(status_code)
            # Send warning for admins
            await self.send_warning(message, config)

    #Scheduler reload time will be fix set on 60 sec
    @loop(seconds=60)
    async def scheduler(self):
        if self.test != 0:
            await self.get_guilds_request()
        self.test += 1


def setup(bot):
    bot.add_cog(RequestsScheduler(bot))
