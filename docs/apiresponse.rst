API Responses
=============

All API responses (except occasionally 500 responses) can be reasonably expected to return as :code:`application/json`.
The JSON format for responses can be seen below.

API authorization should be carried out via the use of request headers and an API key. Each user
has their own unique API key that can be refreshed at any time on the website's `Config` page.

   **Example request**:

   .. sourcecode:: http

      GET /api/v1/shows/14 HTTP/1.1
      Host: localhost
      Accept: application/json
      Authorization: 7baef621-321d-4330-ada2-8d9766c0fe4f

   **Example successful response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json

      {
        "status": 200,
        "result": {
            "id_": 14,
            "title": "Steins;Gate",
            "desired_format": "{n} - {s00e00}",
            "desired_folder": "/target/{n}/Season {s00}",
            "season": 0,
            "episode_offset": 0,
            "entries: [ ... ],
            "metadata: { ... },
            "webhooks": [ ... ]
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