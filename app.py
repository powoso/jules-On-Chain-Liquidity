from flask import Flask, jsonify, request, Response, render_template
import json
import threading
import time
import os
import monitor  # Ensure this imports your modified monitor.py

app = Flask(__name__)

# In-memory logs queue to feed the SSE stream
logs_queue = []
monitor_thread = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    try:
        with open('wallets.json', 'r') as f:
            config = json.load(f)
        return jsonify(config)
    except FileNotFoundError:
        return jsonify({"error": "wallets.json not found"}), 404

@app.route('/api/config', methods=['POST'])
def update_config():
    data = request.json
    try:
        # Load existing config to retain non-user-editable fields (like ABI)
        with open('wallets.json', 'r') as f:
            config = json.load(f)

        # Update user-editable fields
        if 'whales' in data:
            config['whales'] = data['whales']
        if 'threshold' in data:
            config['threshold'] = int(data['threshold'])
        if 'rpc_url' in data:
            config['rpc_url'] = data['rpc_url']

        with open('wallets.json', 'w') as f:
            json.dump(config, f, indent=2)

        return jsonify({"message": "Configuration updated successfully", "config": config})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/monitor/start', methods=['POST'])
def start_monitor():
    global monitor_thread
    if monitor.monitor_running:
        return jsonify({"message": "Monitor is already running"})

    if monitor_thread and monitor_thread.is_alive():
        return jsonify({"message": "Monitor is currently stopping. Please wait a few seconds and try again."}), 400

    # Clear old logs before starting
    logs_queue.clear()
    monitor.monitor_running = True
    monitor_thread = threading.Thread(target=monitor.run_monitor, args=(logs_queue,), daemon=True)
    monitor_thread.start()
    return jsonify({"message": "Monitor started"})

@app.route('/api/monitor/stop', methods=['POST'])
def stop_monitor():
    if not monitor.monitor_running:
        return jsonify({"message": "Monitor is not running"})

    # Signal the monitor loop to stop
    monitor.monitor_running = False
    return jsonify({"message": "Stop signal sent to monitor"})

@app.route('/api/monitor/status', methods=['GET'])
def monitor_status():
    return jsonify({"running": monitor.monitor_running})

@app.route('/api/logs')
def stream_logs():
    def generate():
        last_index = 0
        while True:
            # If there are new logs in the queue
            if last_index < len(logs_queue):
                new_logs = logs_queue[last_index:]
                for log in new_logs:
                    # SSE format: data: <message>\n\n
                    # To handle multiline strings, we format them as JSON
                    json_log = json.dumps({"message": log})
                    yield f"data: {json_log}\n\n"
                last_index = len(logs_queue)
            time.sleep(0.5)

    return Response(generate(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
