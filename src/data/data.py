import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


class ParalympicsData:
    """ Class representing the paralympics data in JSON format.

    Each method returns all rows from a table as JSON.

    Attributes:
        database_file: path to the database file
        tables: list of table names from the database

    Methods:
        get_table_as_json(self, table_name): Gets the data from the specified table and returns it as JSON
        get_all_data(self): Gets data from joined tables and returns it as JSON
        get_row_by_id(self, row_id): Gets the data from the specified row and returns it as JSON
        add_row(self, row_id): Adds a new row to the table
        search_table(self, table_name, filters): Gets rows based on search criteria in any column

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

    def _get_columns(self, table_name: str) -> List[str]:
        conn = sqlite3.connect(self.database_file)
        try:
            cur = conn.cursor()
            cur.execute(f"PRAGMA table_info('{table_name}')")
            cols = [row[1] for row in cur.fetchall()]  # the second column is 'name'
            return cols
        finally:
            conn.close()

    def _get_pk_column(self, table_name: str) -> Optional[str]:
        conn = sqlite3.connect(self.database_file)
        try:
            cur = conn.cursor()
            cur.execute(f"PRAGMA table_info('{table_name}')")
            for row in cur.fetchall():
                # row format: (cid, name, type, notnull, dflt_value, pk)
                if row[5]:  # pk > 0
                    return row[1]
            return None
        finally:
            conn.close()

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

        Doesn't currently include games.url, games.highlights, or disabilities

        Returns:
            data: json format data

        Raises:
            e: Exception
        """
        sql = (
            "SELECT country.country_name, games.event_type, games.year, games.start_date, "
            "games.end_date, host.place_name, games.events, games.sports, games.countries, "
            "games.participants_m, games.participants_f, games.participants, host.latitude, "
            "host.longitude "
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

    def get_row_by_id(self, table_name: str, item_id):
        if table_name not in self.tables:
            raise RuntimeError(f"Table {table_name} does not exist")
        pk = self._get_pk_column(table_name)
        conn = sqlite3.connect(self.database_file)
        try:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            if pk:
                sql = f"SELECT * FROM '{table_name}' WHERE \"{pk}\" = ?"
            else:
                sql = f"SELECT * FROM '{table_name}' WHERE rowid = ?"
            cur.execute(sql, (item_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def search_table(self, table_name: str, filters: Dict[str, str]):
        if table_name not in self.tables:
            raise RuntimeError(f"Table {table_name} does not exist")
        cols = set(self._get_columns(table_name))
        allowed_filters = {k: v for k, v in filters.items() if k in cols}
        if not allowed_filters:
            return self.get_table_as_json(table_name)
        where_clauses = []
        values = []
        for col, val in allowed_filters.items():
            where_clauses.append(f"\"{col}\" = ?")
            values.append(val)
        sql = f"SELECT * FROM '{table_name}' WHERE " + " AND ".join(where_clauses)
        conn = sqlite3.connect(self.database_file)
        try:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(sql, tuple(values))
            rows = cur.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def add_row(self, table_name: str, row: Dict):
        if table_name not in self.tables:
            raise RuntimeError(f"Table {table_name} does not exist")
        cols = self._get_columns(table_name)
        # Keep only known columns
        data = {k: v for k, v in row.items() if k in cols}
        if not data:
            raise RuntimeError("No valid columns provided for insert")
        columns = ", ".join(f"\"{c}\"" for c in data.keys())
        placeholders = ", ".join("?" for _ in data)
        sql = f"INSERT INTO '{table_name}' ({columns}) VALUES ({placeholders})"
        conn = sqlite3.connect(self.database_file)
        try:
            cur = conn.cursor()
            cur.execute(sql, tuple(data.values()))
            conn.commit()
            last_id = cur.lastrowid
            # return the inserted row (by primary key if available)
            pk = self._get_pk_column(table_name)
            if pk:
                return self.get_row_by_id(table_name, last_id)
            else:
                # no pk, return the last inserted row via rowid
                return self.get_row_by_id(table_name, last_id)
        finally:
            conn.close()


# Example of a function that gets data from an excel file and returns in JSON format
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


def add_quiz_data():
    """ Method to add question data to the paralympics database."""
    database_file = Path(__file__).parent.joinpath("paralympics.db")
    with sqlite3.connect(database_file) as conn:
        cur = conn.cursor()
        for sql_file in ("question.sql", "response.sql"):
            sql_path = Path(__file__).parent.joinpath(sql_file)
            cur.executescript(sql_path.read_text())
        conn.commit()

