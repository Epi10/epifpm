__author__ = 'aleivag'

import os, sys

sys.path.append(os.path.join(sys.path[0], '..'))

from epifpm.zfm20 import Fingerprint

from flask import Flask
from flask.ext.mako import MakoTemplates, render_template


app = Flask(__name__)
mako = MakoTemplates(app)

LOW_LEVEL_API = ['handshake', 'empty', 'get_image', 'up_image', 'image_2_tz']

@app.route("/")
def main():
    return render_template('main_view.html', fingerprint=Fingerprint, LOW_LEVEL_API=LOW_LEVEL_API)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
