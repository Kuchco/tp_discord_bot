import requests
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc
import json
import sys
import datetime
import time
import discord
from discord.ext import commands

from src.utils.json_load import read_json

config = read_json("cogs")

class RequestsScheduler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.start_scheduler()

    scheduler = BackgroundScheduler()
    one_day_in_milliseconds = 86400000

    # Create and return a formatted string of the Python JSON object
    def return_serialize_json(self, obj):
        text = json.dumps(obj, sort_keys=True, indent=4)
        return text

    def return_status_code_message(status_code):
        if status_code == 200 :
            return "Request okay, result has been returned."
        elif status_code == 301 :
            return "The server is redirecting you to a different endpoint."
        elif status_code == 400 :
            return "The server thinks you made a bad request."
        elif status_code == 401 :
            return "The server thinks youre not authenticated."
        elif status_code == 403 :
            return "The resource youre trying to access is forbidden: you dont have the right permissions to see it."
        elif status_code == 404 :
            return "The resource you tried to access wasnt found on the server."
        elif status_code == 500 :
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

    # Clear JSON file (write empty array)
    def clear_json_file(self):
        with open("cogs/requests_logs.json", "w") as outfile:
            outfile.write(self.return_serialize_json([]))

    # Return saved logs from file requests_logs.json
    def return_requests_logs(self):
        try:
            # Reading from json file
            return read_json("requests_logs")
        except ValueError:
            # File is empty or data are corrupted, clear file
            self.clear_json_file()
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
        else :
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

    def save_new_request_logs(self, requestsLogs):
        with open("cogs/requests_logs.json", "w") as outfile:
            outfile.write(self.return_serialize_json(requestsLogs))

    # Send notification for student
    # New response mean -> there is something
    def send_notification(self, response_to_notify):
        subject_shortcut = response_to_notify["subjectShortcut"]
        updated_page = response_to_notify["updatedPage"]
        updated_pageLink = response_to_notify["updatedPageLink"]
        milliseconds = response_to_notify["updateDateTime"]

        # Format milliseconds to date time
        update_datetime = datetime.datetime.fromtimestamp(int(milliseconds)/1000.0)

        guilds = self.bot.guilds
        if guilds:

            # Notify only to supported guilds
            # If include only 1 values called "ALL" -> means all guilds are supported
            all_guilds = False
            supported_guilds = config['requests_supported_guilds']
            if len(supported_guilds) == 1 and supported_guilds[0] == "ALL":
                all_guilds = True

            for guild in guilds:
                # If all_guilds = False, Notify only supported one
                if all_guilds or guild.name in supported_guilds:

                    # Notify only to supported channels
                    # If include only 1 values called "ALL" -> means all channels are supported
                    all_channels = False
                    supported_channels = config['requests_notify_channels']
                    if len(supported_channels) == 1 and supported_channels[0] == "ALL":
                        all_channels = True

                    for channel in guild.channels:
                        # If all_channels = False, Notify only supported one
                        if all_channels or channel.name in supported_channels:
                            # Prepare notification
                            embed = discord.Embed(
                                title="One kokos to rule them all",
                                description="There in not KOKOS like kokos",
                                colour=discord.Colour.red()
                            )
                            channel.send(embed=embed)


    # Send notification / warning for admins
    # Something go wrong during process
    def send_warning(self):
        guilds = self.bot.guilds
        if guilds:

            # Warn only to supported guilds
            # If include only 1 values called "ALL" -> means all guilds are supported
            all_guilds = False
            supported_guilds = config['requests_supported_guilds']
            if len(supported_guilds) == 1 and supported_guilds[0] == "ALL":
                all_guilds = True

            for guild in guilds:
                # If all_guilds = False, Warn only supported one
                if all_guilds or guild.name in supported_guilds:

                    # Notify only to supported channels
                    # If include only 1 values called "ALL" -> means all channels are supported
                    all_channels = False
                    supported_channels = config['requests_warning_channels']
                    if len(supported_channels) == 1 and supported_channels[0] == "ALL":
                        all_channels = True

                    for channel in guild.channels:
                        # Warn only to supported channels
                        if all_channels or channel.name in supported_channels:
                            # Prepare warning
                            embed = discord.Embed(
                                title="One kokos to rule them all",
                                description="There in not KOKOS like kokos",
                                colour=discord.Colour.red()
                            )
                            channel.send(embed=embed)

    def get_request(self):
        # Here set url of api
        response = requests.get(config['requests_api_url'])

        # Get response status code
        status_code = response.status_code

        # Get JSON
        response_json = response.json()

        print(response_json)

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
                                self.send_notification(response)

                                # Add new log for this response
                                logs_for_save.append(response)

                # Save new array of requests logs
                self.save_new_request_logs(logs_for_save)

        else:
            # Get message explained status code
            message = self.return_status_code_message(status_code)

            # Send warning for admins
            self.send_warning(message)

    def start_scheduler(self):
        self.scheduler.configure(timezone=utc)
        # Reload time is set in cogs.json (convert to int and to milliseconds)
        reload_time = int(config['requests_time_seconds']) * 1000
        self.scheduler.add_job(self.get_request, 'interval', seconds=reload_time)
        self.scheduler.start()

    def end_scheduler(self):
        self.scheduler.shutdown()

def setup(bot):
    bot.add_cog(RequestsScheduler(bot))