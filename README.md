# SMS Sending System

This project is an SMS sending system that works on Android devices. It only includes SMS sending functionality.

## Features

- Send SMS from Android devices
- Send SMS via HTTP API
- Send bulk SMS
- SMS history and logging
- Works on Termux

## Installation

1. Open Termux
2. Run `pkg update && pkg install python`
3. Install Termux:API package - `pkg install termux-api`
4. Download this system
5. Run `python sms_server.py` command

## Usage

The system works via HTTP API:
- `POST /api/send_sms` - Send single SMS
- `POST /api/send_bulk_sms` - Send bulk SMS
- `GET /api/status` - Get system status
- `GET /api/logs` - Get SMS logs

## Requirements

- Termux
- Termux:API package
- Python 3