from flask import Flask, render_template
from routes_tests import bp as tests_bp

app = Flask(__name__)
app.register_blueprint(tests_bp)

@app.get("/")
def consignes():
    return render_template("consignes.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
