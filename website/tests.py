"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.test.client import Client
import json
import unittest


class TestContactReply(unittest.TestCase):
    def test_contact_reply(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        # Create the social account

        c = Client()
        json_data = """{
          "collection": "timeline",
          "itemId": "39c0f39c-749d-4dfd-b547-7a2ed0d635c6",
          "operation": "INSERT",
          "userToken": "6",
          "userActions": [
            {
              "type": "SHARE"
            }
          ]
        }"""

        print "load dump", json.loads(json.dumps(json_data))
        j = json.loads(json_data)
        response = c.post('/mirror/subscription/reply/', json.dumps(j), "text/json",
                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # print response
        self.assertTrue(response.status_code == 200)

def run_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestContactReply)
    unittest.TextTestRunner(verbosity=2).run(suite)