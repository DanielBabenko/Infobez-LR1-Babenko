#!flask/bin/python
from flask import make_response
from jwt_authentification import *
from config import *
from auth import *
from tasks import *

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)