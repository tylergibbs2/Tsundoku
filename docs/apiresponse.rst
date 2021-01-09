API Responses
=============

All API responses (except occasionally 500 responses) can be reasonably expected to return as :code:`application/json`. The JSON format for responses can be seen below.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1/shows/14 HTTP/1.1
      Host: localhost
      Accept: application/json

   **Example successful response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "status": 200,
        "result": {
            "id": 14,
            "title": "Steins;Gate",
            "desired_format": "{n} - {s00e00}",
            "desired_folder": "/target/{n}/Season {s00}",
            "season": 0,
            "episode_offset": 0
        }
      }

   **Example failed response**:

   .. sourcecode:: http

      HTTP/1.1 404 Not Found
      Content-Type: application/json

      {
        "status": 404,
        "error": "Show with passed ID not found."
      }