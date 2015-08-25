__author__ = 'aleivag'


from flask import Flask
from flask.ext.mako import MakoTemplates, render_template


app = Flask(__name__)
mako = MakoTemplates(app)


@app.route("/")
def main():
    return render_template('main_view.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
