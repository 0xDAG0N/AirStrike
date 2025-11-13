import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from flask_restful import Api, Resource, reqparse
from flask import jsonify, request
from utils.network_utils import run_scan
class WifiScan(Resource):
    def get(self):
        """
        Scan Wi-Fi networks on a specific interface
        ---
        responses:
          200:
            description: A list of available Wi-Fi networks
            schema:
              type: array
              items:
                type: object
                properties:
                  BSSID:
                    type: string
                    example: "00:11:22:33:44:55"
                  ESSID:
                    type: string
                    example: "MyNetwork"
                  Channel:
                    type: string
                    example: "6"
        """
        interface = 'wlan0'
        result = run_scan(interface)
        return jsonify(result)
