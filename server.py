from dotenv import load_dotenv
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv()

slack_token = os.getenv("MY_SLACK_TOKEN")
channel = os.getenv("MY-CHANNEL")
client = WebClient(token=slack_token)

def post_message(message):
    try:
        client.chat_postMessage(channel=channel, text=message)
        return "Message sent successfully"
    except SlackApiError as e:
        raise ValueError(f"Error sending message: {e}") from e

def channel_list():
    try:
        result = client.conversations_list(
            types="public_channel,private_channel")
        channels = result["channels"]
        return channels
    except Exception as e:
        raise ValueError(e) from e

def channel_exists(channel_name):
    channels = channel_list()
    return any(ch["name"] == channel_name for ch in channels)

def add_channel_to_slack(channel_name):
    if channel_exists(channel_name):
        raise ValueError(f"Channel {channel_name} already exists.")
    try:
        response = client.conversations_create(name=channel_name)
        if response['ok']:
            return f"Channel {channel_name} added successfully"
        raise ValueError(
            f"Error adding channel: {response['error']}")
    except SlackApiError as e:
        raise ValueError(e) from e

def add_user_to_channel(channel_id, user_ids):
    try:
        members_response = client.conversations_members(channel=channel_id, )
        if members_response['ok']:
            current_members = members_response['members']
            for user in user_ids:
                if user not in current_members:
                    invite_response = client.conversations_invite(
                        channel=channel_id, users=user)
                    if invite_response['ok']:
                        return f"Member {user} added successfully"
                    raise ValueError(
                        f"Error adding user {user}: "
                        f"{invite_response['error']}")
                raise ValueError(
                    f"The member {user} is already part of the channel")
        else:
            raise ValueError(
                f"Error getting channel members: {members_response['error']}")
    except SlackApiError as e:
        raise ValueError(e) from e

def remove_user_from_channel(channel_id, user_id):
    try:
        members_response = client.conversations_members(channel=channel)
        if not members_response.get('ok'):
            raise ValueError(members_response.get('error', 'Unknown error'))
        current_members = members_response['members']
        if user_id in current_members:
            response = client.conversations_kick(
                channel=channel_id, user=user_id)
            if not response.get('ok'):
                raise ValueError(
                    f"Error removing user {user_id}: "
                    f"{response.get('error', 'Unknown error')}")
            return f"Member {user_id} was successfully removed"
        raise ValueError(f"The user {user_id} are not in the channel.")
    except SlackApiError as e:
        raise ValueError(str(e)) from e
