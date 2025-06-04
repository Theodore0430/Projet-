#!/usr/bin/env python
from inf349 import app

if __name__ == "__main__":
    # FLASK_DEBUG=True FLASK_APP=inf349 flask run fonctionnerait aussi,
    # mais run.py permet un démarrage direct :
    app.run(debug=True)
