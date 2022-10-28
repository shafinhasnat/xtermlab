from select import select
from flask import Flask, render_template
from flask_socketio import SocketIO
import os, pty, select, subprocess
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)
app.config["fd"] = None
app.config["child_pid"] = None

def term_worker():
    max_read_bytes = 1024*20
    while True:
        socketio.sleep(0.01)
        if app.config["fd"]:
            timeout_sec = 0
            (data_ready, _, _) = select.select([app.config["fd"]], [], [], timeout_sec)
            if data_ready:
                output = os.read(app.config["fd"], max_read_bytes).decode()
                socketio.emit("term_output", output, namespace='/term')

@app.route("/")
def home():
    return render_template("index.html")
    
@socketio.on("connect", namespace="/term")
def connect():
    print("new connection")
    socketio.emit("connect", "banglar socket connected", namespace="/term")
    if app.config["child_pid"]:
        return
    (child_pid, fd) = pty.fork()
    print(child_pid, fd)
    if child_pid == 0:
        subprocess.run("bash")
    else:
        app.config["fd"] = fd
        app.config["child_pid"] = child_pid
        socketio.start_background_task(target=term_worker)


@socketio.on("term_input", namespace="/term")
def term_input(data):
    if app.config["fd"]:
        os.write(app.config["fd"], data["input"].encode())

if __name__ == "__main__":
    socketio.run(app, debug=True,host='0.0.0.0', port=5000)
