import unittest
from unittest.mock import patch
import server
from slack_sdk.errors import SlackApiError

class TestPostMessage(unittest.TestCase):

    @patch('server.client')
    def test_post_message_success(self, mock_client):
        mock_client.chat_postMessage.return_value = {'ok': True}
        message = "Hello!"
        result = server.post_message(message)
        self.assertEqual(result, "Message sent successfully")
        mock_client.chat_postMessage.assert_called_once_with(
            channel=server.channel, text=message)

    @patch('server.client')
    def test_post_message_failure(self, mock_client):
        mock_client.chat_postMessage.side_effect = SlackApiError(
            "error", {"ok": False})
        message = "Hello!"
        with self.assertRaises(ValueError) as context:
            server.post_message(message)
        self.assertTrue(
            "Error sending message: error" in str(context.exception))

class TestChannelList(unittest.TestCase):

    @patch('server.client')
    def test_channel_list(self, mock_client):
        expected_channels = [
            {"name": "channel_a", "id": "C123456"},
            {"name": "channel_b", "id": "C654321"},]
        mock_client.conversations_list.return_value = {
            "channels": expected_channels
        }

        channels = server.channel_list()
        self.assertEqual(channels, expected_channels)
        mock_client.conversations_list.assert_called_once_with(
            types="public_channel,private_channel")

class TestAddChannelToSlack(unittest.TestCase):

    @patch('server.client')
    @patch('server.channel_list')
    def test_add_channel_to_slack(self, mock_channel_list, mock_client):
        mock_channel_list.return_value = [
            {"name": "channel_a", "id": "C123456"},
            {"name": "channel_b", "id": "C654321"},]
        mock_client.conversations_create.return_value = {'ok': True}
        response = server.add_channel_to_slack("channel_c")
        self.assertEqual(response, "Channel channel_c added successfully")
        mock_client.conversations_create.assert_called_once_with(
            name="channel_c")

    @patch('server.channel_list')
    def test_add_channel_exists(self, mock_channel_list):
        mock_channel_list.return_value = [
            {"name": "channel_a", "id": "C123456"},
            {"name": "channel_b", "id": "C654321"},]
        with self.assertRaises(ValueError) as context:
            server.add_channel_to_slack("channel_a")
        self.assertEqual(
            str(context.exception), "Channel channel_a already exists.")

    @patch('server.client')
    @patch('server.channel_list')
    def test_error_response(self, mock_channel_list, mock_client):
        mock_channel_list.return_value = [
            {"name": "channel_a", "id": "C123456"},
            {"name": "channel_b", "id": "C654321"},
        ]
        mock_client.conversations_create.return_value = {
            'ok': False, 'error': 'channel_not_created'}
        with self.assertRaises(ValueError) as context:
            server.add_channel_to_slack("channel_c")
        self.assertEqual(
            str(context.exception),
            "Error adding channel: channel_not_created")

    @patch('server.client')
    @patch('server.channel_list')
    def test_slack_api_error(self, mock_channel_list, mock_client):
        mock_channel_list.return_value = [
            {"name": "channel_a", "id": "C123456"},
            {"name": "channel_b", "id": "C654321"},
        ]
        mock_client.conversations_create.side_effect = SlackApiError(
            "api_error", {"ok": False})
        with self.assertRaises(ValueError) as context:
            server.add_channel_to_slack("channel_c")
        self.assertIn("api_error", str(context.exception))
        self.assertIn(
            "The server responded with: {'ok': False}", str(context.exception))

class TestAddUserToChannel(unittest.TestCase):

    @patch('server.client')
    def test_add_user_to_channel(self, mock_client):
        mock_client.conversations_members.return_value = {
            'ok': True,
            'members': ['U123456', 'U654321']
        }
        mock_client.conversations_invite.return_value = {'ok': True}
        response = server.add_user_to_channel(
            "C123456", ["U789012", "U542658"])
        self.assertEqual(response, "Member U789012 added successfully")
        mock_client.conversations_invite.assert_called_once_with(
            channel="C123456", users="U789012")

    @patch('server.client')
    def test__user_already_exists(self, mock_client):
        mock_client.conversations_members.return_value = {
            'ok': True,
            'members': ['U123456', 'U654321']
        }
        with self.assertRaises(ValueError) as context:
            server.add_user_to_channel("C123456", ["U654321"])
        self.assertEqual(str(context.exception),
                         "The member U654321 is already part of the channel")

    @patch('server.client')
    def test_get_members_error(self, mock_client):
        mock_client.conversations_members.return_value = {
            'ok': False,
            'error': 'channel_not_found'}
        with self.assertRaises(ValueError) as context:
            server.add_user_to_channel("C123456", ["U654321"])
        self.assertEqual(
            str(context.exception),
            "Error getting channel members: channel_not_found")

    @patch('server.client')
    def test_add_user_to_channel_failure(self, mock_client):
        mock_client.conversations_members.return_value = {
            'ok': False,
            'error': 'channel_not_found'}
        with self.assertRaises(ValueError) as context:
            server.add_user_to_channel("C123456", ["U654321"])
        self.assertEqual(
            str(context.exception),
            "Error getting channel members: channel_not_found")

class TestRemoveUserFromChannel(unittest.TestCase):

    @patch('server.client')
    def test_remove_user_from_channel(self, mock_client):
        mock_client.conversations_members.return_value = {
            'ok': True,
            'members': ['U123456', 'U654321']
        }
        mock_client.conversations_kick.return_value = {'ok': True}
        response = server.remove_user_from_channel("C123456", "U654321")
        self.assertEqual(response, "Member U654321 was successfully removed")
        mock_client.conversations_kick.assert_called_once_with(
            channel="C123456", user="U654321")

    @patch('server.client')
    def test_user_not_exists_error(self, mock_client):
        mock_client.conversations_members.return_value = {
            'ok': True,
            'members': ['U123456', 'U654321']
        }
        mock_client.conversations_kick.return_value = {"ok": False}
        with self.assertRaises(ValueError) as context:
            server.remove_user_from_channel("C123456", "U789123")
        self.assertEqual(
            str(context.exception), "The user U789123 are not in the channel.")

    @patch('server.client')
    def test_get_members_error(self, mock_client):
        mock_client.conversations_members.return_value = {
            'ok': False,
            'error': 'channel_not_found'}
        with self.assertRaises(ValueError) as context:
            server.remove_user_from_channel("C123456", "U654321")
        self.assertEqual(str(context.exception), "channel_not_found")

    @patch('server.client')
    def test_remove_user_from_channel_failure(self, mock_client):
        mock_client.conversations_members.return_value = {
            'ok': False,
            'error': 'channel_not_found'}
        with self.assertRaises(ValueError) as context:
            server.remove_user_from_channel("C123456", "U654321")
        self.assertEqual(str(context.exception), "channel_not_found")

if __name__ == '__main__':
    unittest.main()
