import azure.functions as func
import logging
import requests
import os
import json
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text  # Importing text
from sqlalchemy.orm import sessionmaker

app = func.FunctionApp()

# Assemble the connection string
server = "server-l-uat.database.windows.net"
database = "database_uat"
username = "adm-uat"
password = os.environ.get("DB_PASSWORD")  # It's better to get sensitive data from environment variables
connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server"

# Define your SQLAlchemy connection
engine = create_engine(connection_string)
Session = sessionmaker(bind=engine)

@app.service_bus_queue_trigger(arg_name="azservicebus", queue_name="queue-feb23", connection="servicebusfeb23_SERVICEBUS")
def servicebus_queue_trigger_function(azservicebus: func.ServiceBusMessage) -> None:
    location = azservicebus.get_body().decode('utf-8').strip()
    logging.info(f'Python ServiceBus Queue trigger processed a message: {location}')

    api_key = os.environ["WEATHER_API_KEY"]
    url = f"http://api.weatherstack.com/current?access_key={api_key}&query={location}"
    response = requests.get(url)

    if response.status_code == 200:
        api_response = response.json()
        if api_response.get('location', {}).get('name', '').lower() == location.lower():
            logging.info(f"Exact weather data match for {location}: {json.dumps(api_response, indent=2)}")
        else:
            logging.info(f"No exact match found for {location}. Possibly found: {api_response.get('location', {}).get('name')}")

        try:
            with Session() as session:
                mst_time = datetime.now(timezone.utc) - timedelta(hours=7)
                query = text("INSERT INTO dbo.weather2 (record_date, datafile_name, data_json) VALUES (:record_date, :datafile_name, :data_json)")
                session.execute(query, {'record_date': mst_time, 'datafile_name': 'weather', 'data_json': json.dumps(api_response)})
                session.commit()
            logging.info("Data successfully written to dbo.weather2_changeslanre")
        except Exception as e:
            logging.error(f"Error writing to the database: {e}")
    else:
        logging.error(f"Failed to retrieve weather data for {location} or location not found.")

    return None
