import azure.functions as func
import logging
import requests
import os
import json

app = func.FunctionApp()

@app.service_bus_queue_trigger(arg_name="azservicebus", queue_name="queue-feb23",
                               connection="servicebusfeb23_SERVICEBUS")
def servicebus_queue_trigger_function(azservicebus: func.ServiceBusMessage):
    # Parse the message body to get the location
    location = azservicebus.get_body().decode('utf-8')
    logging.info('Python ServiceBus Queue trigger processed a message: %s', location)

    # Make the API call to get weather data for the location
    api_key = os.environ["WEATHER_API_KEY"]
    url = f"http://api.weatherstack.com/current?access_key={api_key}&query={location}"
    response = requests.get(url)

    # Log the response or handle it as needed
    if response.status_code == 200:
        # Assuming the API returns JSON data
        data = response.json()
        # You can log the data or perform further processing here
        logging.info(f"Weather Data for {location}: {json.dumps(data, indent=2)}")
        return func.HttpResponse(body=json.dumps(data), status_code=200)
    else:
        error_message = f"Failed to retrieve weather data for {location}"
        logging.error(error_message)
        return func.HttpResponse(body=error_message, status_code=response.status_code)
