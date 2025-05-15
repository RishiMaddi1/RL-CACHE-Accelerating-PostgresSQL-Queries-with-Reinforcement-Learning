from flask import Flask, Response, render_template, request
import threading
import time
import queue
import redis_rl_cache_simulation as sim

app = Flask(__name__)

# Queues for streaming logs and plot data to frontend
log_queue_cache = queue.Queue()
log_queue_nocache = queue.Queue()
plot_queue = queue.Queue()

# Shared state for simulation   
sim_running = False

# In app.py, add a new queue for the summary
summary_queue = queue.Queue()

# Helper to run the RL cache simulation
def run_cache_sim():
    global cache_summary
    cache_summary = sim.run_simulation(with_cache=True, log_queue=log_queue_cache, plot_queue=plot_queue)
    log_queue_cache.put({'type': 'done', 'results': cache_summary})
    maybe_send_summary()

# Helper to run the no-cache simulation
def run_nocache_sim():
    global nocache_summary
    nocache_summary = sim.run_simulation(with_cache=False, log_queue=log_queue_nocache, plot_queue=plot_queue)
    log_queue_nocache.put({'type': 'done', 'results': nocache_summary})
    maybe_send_summary()

def maybe_send_summary():
    global summary_str_global, sim_running
    if 'cache_summary' in globals() and 'nocache_summary' in globals():
        summary_str = sim.format_simulation_summary(cache_summary, nocache_summary)
        summary_str_global = summary_str  # Store for later GET
        summary_queue.put(summary_str)
        sim_running = False  # Reset the flag when both simulations are done

@app.route('/start', methods=['POST'])
def start_simulation():
    global sim_running
    if sim_running:
        return 'Simulation already running', 400
    sim_running = True
    # Start both simulations in parallel
    threading.Thread(target=run_cache_sim, daemon=True).start()
    threading.Thread(target=run_nocache_sim, daemon=True).start()
    return 'Started', 200

@app.route('/stream/cache')
def stream_cache():
    def event_stream():
        while True:
            msg = log_queue_cache.get()
            if isinstance(msg, dict) and msg.get('type') == 'done':
                break
            if isinstance(msg, str) and msg == '__done__':
                break
            yield f'data: {msg}\n\n'
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/stream/nocache')
def stream_nocache():
    def event_stream():
        while True:
            msg = log_queue_nocache.get()
            if isinstance(msg, dict) and msg.get('type') == 'done':
                break
            if isinstance(msg, str) and msg == '__done__':
                break
            yield f'data: {msg}\n\n'
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/stream/plot')
def stream_plot():
    def event_stream():
        while True:
            msg = plot_queue.get()
            yield f'data: {msg}\n\n'
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/stream/summary')
def stream_summary():
    def event_stream():
        while True:
            msg = summary_queue.get()
            yield f'data: {msg}\n\n'
            break
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/summary')
def get_summary():
    global summary_str_global
    return summary_str_global, 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/')
def index():
    return render_template('index.html')

summary_str_global = ""

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 
