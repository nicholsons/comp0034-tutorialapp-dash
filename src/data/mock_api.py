""" Minimal code to return JSON data

 NB: This is NOT how to create a REST API. It is the simplest code possible to return the data
 in JSON format and lacks any of the expected validation and structure. This is fine for cw1 but
 do not use this as an example for coursework 2!

 """
from typing import Callable

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from src.data.data import ParalympicsData

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


def _make_get_all_route(table_name: str) -> Callable:
    """ Create a GET /<table> route to get all data from a table """

    async def _route():
        try:
            return data.get_table_as_json(table_name)
        except AttributeError:
            raise HTTPException(status_code=500, detail="ParalympicsData.get_json not implemented")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    return _route


def _make_get_by_id_route(table_name: str) -> Callable:
    """ Create a GET /<table>/{item_id} route to get a row by its primary key """

    async def _route(item_id: int):
        try:
            row = data.get_row_by_id(table_name, item_id)
            if row is None:
                raise HTTPException(status_code=404, detail="Item not found")
            return row
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    return _route


def _make_search_route(table_name: str) -> Callable:
    """
    Create a GET '/<table>/search' route that accepts query parameters to filter rows.

    Usage:
    - Provide one or more query parameters where each key is a column name and the
      value is the exact value to match.
    - Multiple parameters are combined with logical AND.

    Examples:
    - /games/search?event_type=summer
    - /games/search?event_type=summer&year=2020

    Notes:
    - Only columns that exist in the table are considered; unknown query keys are ignored.
    - Matching is exact equality (\"column\" = ?). Wildcards/partial matches are not supported.
    - If no valid query parameters are supplied, the endpoint returns all rows for the table.
    """

    async def _route(request: Request):
        try:
            params = dict(request.query_params)
            return data.search_table(table_name, params)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    return _route


def _make_post_route(table_name: str) -> Callable:
    """
    Create a POST '/<table>' route to insert a new row.

    Usage:
    - Send HTTP POST to /{table} with a JSON object body (Content-Type: application/json).
    - Only keys that match existing column names are used; unknown keys are ignored.
    - On success the endpoint returns the inserted row as JSON. If the table has a primary key
      the returned row is fetched by that key; otherwise the row is returned using SQLite's rowid.

    Responses:
    - 200: inserted row as JSON.
    - 400: request body is not a JSON object.
    - 500: database or server errors (for example, no valid columns provided for insert).

    Example:
    curl -X POST 'http://localhost:8000/{table}' \\
         -H 'Content-Type: application/json' \\
         -d '{"column1":"value1","column2":123}'
    """

    async def _route(request: Request):
        try:
            payload = await request.json()
            if not isinstance(payload, dict):
                raise HTTPException(status_code=400, detail="Request body must be a JSON object")
            new_row = data.add_row(table_name, payload)
            return new_row
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    return _route


# create the routes for each table
for _t in _tables:
    app.get(f"/{_t}", name=f"{_t}_all")(_make_get_all_route(_t))
    app.get(f"/{_t}/search", name=f"{_t}_search")(_make_search_route(_t))
    app.get(f"/{_t}/{{item_id}}", name=f"{_t}_get")(_make_get_by_id_route(_t))
    app.post(f"/{_t}", name=f"{_t}_post")(_make_post_route(_t))


# Create a route to get data for the charts
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
