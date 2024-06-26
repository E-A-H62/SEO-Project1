import pandas as pd
import os
import json
import sqlalchemy as db
from openai import OpenAI
from sqlite3 import DatabaseError


# Retrieve the API key from the environment variable
my_api_key = os.getenv('OPENAI_KEY')


class Project:

    @staticmethod
    def store_db(data,
                 db_url='sqlite:///data_base_name.db',
                 table_name='table_name'):
        df = pd.DataFrame.from_dict(data)
        engine = db.create_engine(db_url)

        try:
            df.to_sql(table_name, con=engine, if_exists='replace', index=False)
        except DatabaseError:
            # Handle database errors such as malformed database
            # For simplicity, let's recreate the database if it's corrupted
            os.remove('data_base_name.db')
            engine = db.create_engine(db_url)
            df.to_sql(table_name, con=engine, if_exists='replace', index=False)

        with engine.connect() as connection:
            query_result = connection.execute(
                db.text("SELECT * FROM table_name;")
            ).fetchall()
            return pd.DataFrame(query_result)

    def generate_chat(api_key, age, cuisine, location):
        # Create an OpenAI client using the provided API key
        client = OpenAI(api_key=api_key)

        # Specify the model to use and the messages to send
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You know about popular restaurants."
                },
                {"role": "user", "content": (
                    f"I am {age} years old and "
                    f"am interested in {cuisine} cuisine"
                    f"I live in {location} zip code"
                    "Generate a JSON formatted table with 10 items. "
                    "The data contains the name of the restaurant "
                    "and the adress of the restraunt"
                    "and the website url of the restraunt"
                    "and its rating (0-5 stars)."
                    "Rank the restaurants in descending order "
                    "with the highest ratings at the top."
                    "The format should follow something like: "
                    "{'restaurants': "
                    "[{'Name': 'name', 'Adress': adress, "
                    "'Website': website, 'Rating(0-5)': rating}]}"
                )}
            ]
        )

        # Extract and return the content from the API response
        chat_response = completion.choices[0].message.content
        return chat_response

    def get_recs(api_key, age, cuisine, location):
        # Generate chat response
        chat_response = Project.generate_chat(api_key, age, cuisine, location)

        # Parse JSON response
        data = json.loads(chat_response)

        # Store data in the database and print the resulting dataframe
        first_key = list(data.keys())[0]
        restaurant_data = data[first_key]

        df = Project.store_db(restaurant_data)
        # Print DataFrame without index
        blankIndex = [''] * len(df)
        df.index = blankIndex

        return df


# print(Project.get_recs(my_api_key, 19, "Italian"))
