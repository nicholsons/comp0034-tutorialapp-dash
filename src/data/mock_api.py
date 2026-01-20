""" Minimal code to return JSON data

 NB: This is NOT how to create a REST API. It is the simplest code possible to return the data
 in JSON format and lacks any of the expected validation and structure. This is fine for cw1 but
 do not use this as an example for coursework 2!

 """
import json
import sqlite3
from pathlib import Path
from typing import Callable

import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse


def get_event_data():
    """ Method to return the data from the paralympics .xlsx file.

    NB: This is a simplified return of all data without validation.

    Returns:
        json_data: json format paralympics data

    Raises:
        RuntimeError: if the data could not be read, converted to JSON
        FileNotFoundError: if no event file was found

        """
    data_file = Path(__file__).parent.joinpath("paralympics.xlsx")
    try:
        if not data_file.exists():
            raise FileNotFoundError(f"Data file not found: {data_file}")
        df = pd.read_excel(data_file)
        if df.empty:
            return []
        json_data = df.to_json(orient='records')
        return json_data
    except FileNotFoundError:
        raise
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:
        raise RuntimeError(f"Error reading XLSX {data_file}: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Error decoding JSON from XLSX conversion: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error loading event data: {e}") from e


class ParalympicsData:
    """ Class representing the paralympics data in JSON format.

    Each method returns all rows from a table as JSON.

    Attributes:
        database_file: path to the database file
        tables: list of table names from the database

    Methods:
        get_table_as_json(self, table_name): Gets the data from the specified table and returns it as JSON
        get_all_data(self): Gets data from joined tables and returns it as JSON

    """

    def __init__(self):
        self.database_file = Path(__file__).parent.joinpath("paralympics.db")
        if not self.database_file.exists():
            raise FileNotFoundError(f"Database file not found: {self.database_file}")
        self.tables = []
        try:
            conn = sqlite3.connect(self.database_file)
            with conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_master'"
                )
                self.tables = [row[0] for row in cur.fetchall()]
        except Exception as e:
            raise RuntimeError(f"Error querying database tables: {e}") from e

    def get_table_as_json(self, table_name):
        """ Method to return the specified table data from the paralympics .db file.

        Uses sqlite3 to access and query the database
        Only accepts a table name if it exists in the database

        Args:
            table_name: name of the database table

        Returns:
            json_data: json format data
        """
        try:
            conn = sqlite3.connect(self.database_file)
            with conn:
                conn.row_factory = sqlite3.Row  # Returns columns by names instead of tuples
                cur = conn.cursor()
                sql = f"SELECT * from {table_name}"
                cur.execute(sql)
                rows = cur.fetchall()
                if not rows:
                    return []
                data = [dict(row) for row in rows]
                return data
        except Exception as e:
            raise RuntimeError(f"Error querying table {table_name}: {e}") from e
        finally:
            if conn:
                conn.close()

    def get_all_data(self):
        """ Method to return all data from the paralympics .db file.

        Doesn't currently include URL, highlights or disabilities

        Returns:
            data: json format data

        Raises:
            e: Exception
        """
        sql = (
            "SELECT country.country_name, games.event_type, games.year, games.start_date, "
            "games.end_date, host.place_name, games.events, games.sports, games.countries, "
            "games.participants_m, games.participants_f, games.participants, "
            "host.latitude, host.longitude "
            "FROM games "
            "JOIN games_host ON games.id = games_host.games_id "
            "JOIN host ON games_host.host_id = host.id "
            "JOIN country ON host.country_id = country.id"
        )
        try:
            conn = sqlite3.connect(self.database_file)
            with conn:
                conn.row_factory = sqlite3.Row  # Returns columns by names instead of tuples
                cur = conn.cursor()
                cur.execute(sql)
                rows = cur.fetchall()
                if not rows:
                    return []
                data = [dict(row) for row in rows]
                return data
        except Exception as e:
            raise RuntimeError(f"Error querying tables: {e}") from e
        finally:
            if conn:
                conn.close()


# Minimal code to generate a REST API app with JSON format data
app = FastAPI(title="Mock Paralympics API")

origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:8050",  # dash default
    "http://localhost:5000",  # flask default
    "http://localhost:8501",  # streamlit default
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data = ParalympicsData()
_tables = data.tables


@app.get("/", summary="API documentation")
async def root(request: Request):
    """Redirect to the configured API docs page (Swagger UI, Redoc or OpenAPI)."""
    base = str(request.base_url).rstrip("/")
    if app.docs_url:
        return RedirectResponse(url=base + app.docs_url)
    if app.redoc_url:
        return RedirectResponse(url=base + app.redoc_url)
    if app.openapi_url:
        return RedirectResponse(url=base + app.openapi_url)
    raise HTTPException(status_code=404, detail="No API docs configured")


def _make_route(table_name: str) -> Callable:
    """ Method to return the route function """

    async def _route():
        try:
            return data.get_table_as_json(table_name)
        except AttributeError:
            raise HTTPException(status_code=500, detail="ParalympicsData.get_json not implemented")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    return _route


# create a GET route for each table at /{table}
for _t in _tables:
    app.get(f"/{_t}", name=_t)(_make_route(_t))


# Create a root to data for the charts
@app.get("/all")
async def get_all():
    try:
        return data.get_all_data()
    except AttributeError:
        raise HTTPException(status_code=500, detail="ParalympicsData.get_json not implemented")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    uvicorn.run("src.data.mock_api:app", host="127.0.0.1", port=8000, reload=True)
