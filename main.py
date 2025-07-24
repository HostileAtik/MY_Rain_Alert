import os
import requests
from twilio.rest import Client
from datetime import datetime
import pytz

# --- CONFIG ---
# Fetching Tomorrow.io API key and Twilio credentials from environment variables
TOMORROW_API_KEY = os.getenv('TOMORROW_API_KEY')  # Replace with your Tomorrow.io API Key in GitHub Secrets
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')  # Replace with your Twilio Account SID in GitHub Secrets
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')  # Replace with your Twilio Auth Token in GitHub Secrets

# Twilio WhatsApp numbers (these are standard Twilio numbers)
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+14155238886'  # Twilio WhatsApp number (do not change this)
RECIPIENT_WHATSAPP = 'whatsapp:+8801978163944'  # Replace with the recipient's WhatsApp number

# --- WEATHER CONFIG ---
LATITUDE = 23.726658238586133  # Latitude for the given location (Dhaka University)
LONGITUDE = 90.39265872628926  # Longitude for the given location (Dhaka University)
TOMORROW_API_URL = f"https://api.tomorrow.io/v4/timelines?location={LATITUDE},{LONGITUDE}&fields=precipitationIntensity&apikey={TOMORROW_API_KEY}&units=metric&timesteps=1h"

# Get the current time and convert to BDT (Bangladesh Standard Time)
def get_bdt_time():
    tz = pytz.timezone('Asia/Dhaka')  # BDT timezone
    current_time = datetime.now(tz)  # Current time in BDT
    return current_time

# Function to check for rain between 9 AM to 9 PM BDT
def check_rain():
    response = requests.get(TOMORROW_API_URL)
    data = response.json()

    # Print the response for debugging
    print(data)

    # Check if 'data' key exists and contains weather info
    if 'data' in data:
        rain_times = []
        current_time = get_bdt_time()

        # Get today's date (in BDT)
        today_date = current_time.date()

        # Loop through the forecasted hours (weather forecast)
        for timeline in data['data']['timelines']:
            for interval in timeline['intervals']:
                # Convert the time from the API to BDT (already in local time for Tomorrow.io)
                hour_time = datetime.strptime(interval['startTime'], '%Y-%m-%dT%H:%M:%SZ').astimezone(pytz.timezone('Asia/Dhaka'))
                hour_precip = interval['values'].get('precipitationIntensity', 0)  # Correct field name

                # Check if the hour is between 9 AM to 9 PM BDT and the forecast is for today
                if 9 <= hour_time.hour < 21 and hour_precip > 0 and hour_time.date() == today_date:
                    rain_times.append({
                        'time': hour_time.strftime('%Y-%m-%d %I:%M %p'),  # Using AM/PM format
                        'precip': hour_precip,
                        'hour': hour_time  # Keep the datetime object for sorting by time
                    })

        # Sort by precipitation intensity in descending order and get the top 3
        rain_times_sorted_by_precip = sorted(rain_times, key=lambda x: x['precip'], reverse=True)

        # Get the top 3 rain times with the highest precipitation
        top_3_rain_times = rain_times_sorted_by_precip[:3]

        # Sort the top 3 rain times by hour (chronologically)
        top_3_sorted_by_time = sorted(top_3_rain_times, key=lambda x: x['hour'])

        if top_3_sorted_by_time:
            return [f"{entry['time']} with intensity {entry['precip']} mm/h" for entry in top_3_sorted_by_time]
        else:
            return None
    else:
        print("Error: 'data' key is missing in the response.")
    return None

# Function to send a WhatsApp message via Twilio
def send_whatsapp_alert(message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=message,
        from_=TWILIO_WHATSAPP_NUMBER,  # Twilio WhatsApp number
        to=RECIPIENT_WHATSAPP  # Recipient's WhatsApp number
    )
    print(f"Message sent to {RECIPIENT_WHATSAPP}: {message.sid}")

# Main function to run the rain check and send message
def main():
    rain_times = check_rain()
    current_time = get_bdt_time().strftime("%Y-%m-%d %I:%M %p")  # Get current time in AM/PM format

    if rain_times:
        message = f"🌧️ Rain alert! Rain is expected at the following times between 9 AM to 9 PM BDT:\n"
        message += "\n".join(rain_times)  # List the times when rain is expected
    else:
        message = f"🌞 No rain expected between 9 AM to 9 PM BDT. Enjoy your day!"

    send_whatsapp_alert(message)

# Run the script
if __name__ == "__main__":
    main()
