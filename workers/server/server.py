from flask import Flask, request, jsonify, g
app = Flask(__name__)
workers = {}

@app.route("/hello/<hostname>")
def discover(hostname):
    global workers
    
    ip = request.remote_addr
    workers[hostname] = ip

    return "Hello {}".format(hostname)

@app.route("/workers")
def get_workers():
    return jsonify(workers)

@app.route("/worker/<hostname>")
def get_worker(hostname):
    return workers.get(hostname, "127.0.0.1")

if __name__ == "__main__":
    app.run()