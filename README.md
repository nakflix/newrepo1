# Multi File Sharing Bot

A Telegram bot to share multiple files via a single link, with flexible Force-Subscribe support.

## ✨ New Feature: Smart Force-Subscribe Check

The bot now **checks each channel individually** and shows inline join buttons **only for the channels the user has NOT yet joined**.

- If a user has already joined channels 1 & 2 but not 3 & 4 → they only see buttons for channels 3 and 4.
- If a user has joined all channels → files are delivered immediately.
- The ♻️ **Try Again** button re-checks membership and refreshes the keyboard in place.

## Features

- Fully customizable.
- Can be deployed on Heroku & VPS.
- Customizable welcome message & Force-Subscribe.
- More than one file per link (batch mode).
- Flexible FSUB: 1–4 channels, smart per-channel button display.

## Setup

- Add bot to **Database Channel** with all admin permissions.
- Add bot to each **Force-Sub Channel** as ADMIN (with "Invite Users via Link" permission).

## Environment Variables

| Variable | Description |
|---|---|
| `TG_BOT_TOKEN` | Your bot token from @BotFather |
| `APP_ID` | API ID from my.telegram.org |
| `API_HASH` | API Hash from my.telegram.org |
| `CHANNEL_ID` | Database channel ID |
| `OWNER_ID` | Your Telegram user ID |
| `FORCE_SUB_CHANNEL_1..4` | Force-sub channel IDs (use 0 to disable) |
| `FORCE_SUB_CHANNEL_1_NAME..4_NAME` | Optional display names for the join buttons |
| `START_MESSAGE` | Custom start message |
| `FORCE_SUB_MESSAGE` | Custom force-sub message |
| `CUSTOM_CAPTION` | Caption appended to shared files |
| `PROTECT_CONTENT` | Set `True` to prevent forwarding |

## Deploy on Heroku

[![Deploy](https://img.shields.io/badge/Deploy%20On%20Heroku-black?style=for-the-badge&logo=heroku)](https://dashboard.heroku.com/new?template=https://github.com/nakflix/muti-file-sharing)
