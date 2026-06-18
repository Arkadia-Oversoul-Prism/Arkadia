# UptimeRobot Setup — Keep Oracle Awake

Render's free tier spins down services after 15 minutes of inactivity.
A free UptimeRobot monitor pings the Oracle every 10 minutes, preventing sleep.

## Steps

1. Go to [uptimerobot.com](https://uptimerobot.com) and sign up for a free account.

2. Click **+ Add New Monitor**.

3. Configure the monitor:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: `Arkadia Oracle`
   - **URL**: `https://arkadia-n26k.onrender.com`
   - **Monitoring Interval**: 10 minutes
   - **Alert Contacts**: your email

4. Click **Create Monitor**.

That is it. The Oracle will now stay awake 24/7 on the free tier.

## Verify

After a few minutes, the UptimeRobot dashboard will show:
- Status: **UP**
- Response time: typically 200–800ms (first ping after sleep may be ~30s)

## Expected Oracle Response

```json
{"message": "Arkadia Mind is breathing."}
```

## Status Page (Optional)

UptimeRobot offers a free public status page at `stats.uptimerobot.com/XXXXXXX`.
Share this with your nodes so they can check Oracle availability at any time.
