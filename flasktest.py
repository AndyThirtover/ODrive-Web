from flask import Flask
from flask_socketio import SocketIO
from flask import jsonify
from flask import render_template
from flask import request
import threading
import logging
import time
import random
from odrive_jobs import *
from buttons import *
import atexit

button_event = threading.Event()
button_thread = threading.Thread(name="Button_Handler", target=read_button_task, args=(button_event,))


def create_app():
    flapp = Flask(__name__)

    def interrupt():
        print ("Shutting down Button Thread")
        global button_thread
        button_thread.set()

    def start_button():
        global button_thread
        button_thread.start()

    start_button()
    atexit.register(interrupt)
    return flapp

app = create_app()
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

def do_config(formargs):
    global config
    global buttons
    print ('formargs:{}'.format(formargs.items()))
    for key, value in formargs.items():
        if 'submit' in key:
            if value == 'SYSTEM':
                process_odrive_config(formargs)


def job_queue(job, parameter=None, parameter2=None):
    if job == 'cycle':
        test_run(parameter)
    elif job == 'tcycle':
        time_run(parameter)
    elif job == 'scycle':
        speed_run(parameter,parameter2)
    elif job == 'current':
        set_current(parameter)
    elif job == 'trajectory_to':
        trajectory_to(parameter,parameter2)
    elif job == 'cancel_trajectory':
        cancel_trajectory()
    elif job == 'move_to':
        move_to(parameter)
    

@app.route('/')
def render_index():
    all_threads = threading.enumerate()
    print (str(all_threads))
    return render_template('index.html', name='No Operation')

@app.route('/config')
def show_config():
    do_config(request.args)
    return render_template('config.html', name='No Operation')

@app.route('/json_data')
def json_data():
    global thread_data
    return jsonify(**thread_data)

@app.route('/json_config')
def json_config():
    global config
    return jsonify(**config)

@app.route('/button_config')
def button_config():
    global buttons
    return jsonify(**buttons)


@app.route('/queue/<job>')
@app.route('/queue/<job>/<parameter>')
@app.route('/queue/<job>/<parameter>/<parameter2>')
def index_do(job, parameter=None, parameter2=None):
    job_queue(job,parameter,parameter2)
    return render_template('index.html', name='Job Queued:' + job)

@app.route('/command')
@app.route('/command/<job>')
@app.route('/command/<job>/<parameter>')
@app.route('/command/<job>/<parameter>/<parameter2>')
def command_queue(job="NoJob", parameter=None, parameter2=None):
    job_queue(job,parameter,parameter2)
    return render_template('command.html', name='Job Queued:' + job)

@app.route('/docs')
def show_docs():
    return render_template('docs.html', name='Show Docs')

@app.route('/contact')
def show_contact():
    return render_template('contact.html', name='Show Contact Page')

@app.route('/action')
def show_action():
    return render_template('action.html', name='SocketIO Action Page')

@socketio.on('connect')
def handle_connect():
    print ("==================== Accepted Connection")
    socketio.emit('accept', {'name':'NeoPixel Driver'})

@socketio.on('message')
def handle_message(message):
    print('===================== Received message: ' + repr(message))
    socketio.emit('message',{'status':'good'})

@socketio.on('get_data')
def handle_get_data(message):
    global thread_data
    get_odrive_data()
    print('===================== Received message: ' + repr(message))
    socketio.emit('odrive_data',{'volts': thread_data['volts'], 'current_limit': thread_data['current_limit'], 'speed': thread_data['speed']})

@socketio.on('do_job')
def handle_do_job(message):
    print('===================== Received message: ' + repr(message))
    message = dict(message)
    for k,v in message.items():
        job = k
        params = v.split('/')
        parameter = params[0]
        if len(params) > 1:
            parameter2 = params[1]
        else:
            parameter2 = None
        job_queue(job, parameter, parameter2)
    handle_get_data('update_clients')   



socketio.run(app, host='0.0.0.0', debug=True)