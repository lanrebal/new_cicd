import azure.functions as func
import logging
import requests
import os
import json

app = func.FunctionApp()

@app.service_bus_queue_trigger(arg_name="azservicebus", queue_name="queue-feb23",
                               connection="servicebusfeb23_SERVICEBUS")
def servicebus_queue_trigger_function(azservicebus: func.ServiceBusMessage) -> None:
    # Parse the message body to get the location
    location = azservicebus.get_body().decode('utf-8').strip()
    logging.info('Python ServiceBus Queue trigger processed a message: %s', location)

    # Make the API call to get weather data for the location
    api_key = os.environ["WEATHER_API_KEY"]
    url = f"http://api.weatherstack.com/current?access_key={api_key}&query={location}"
    response = requests.get(url)

    # Initialize api_response
    api_response = None

    # Log the response or handle it as needed
    if response.status_code == 200:
        api_response = response.json()
        
        # Check if the location matches exactly, ignoring case
        if api_response.get('location', {}).get('name', '').lower() == location.lower():
            logging.info(f"Exact weather data match for {location}: {json.dumps(api_response, indent=2)}")
        else:
            logging.info(f"No exact match found for {location}. Possibly found: {api_response.get('location', {}).get('name')}")
            # If you need to perform additional actions for non-matching locations, do it here
    else:
        error_message = f"Failed to retrieve weather data for {location} or location not found."
        logging.error(error_message)

    # Optionally, log the entire api_response for debugging or information purposes
    logging.info(f"Weather API Response: {json.dumps(api_response, indent=2)}")

    # Function returns None to indicate successful processing of the message
    return None
