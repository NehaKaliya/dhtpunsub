from __future__ import print_function
import paho.mqtt.publish as publish
from tkinter import *
import Adafruit_DHT
import time
from urllib.request import urlopen
import json
import threading

class Publish:
    def __init__(self):
        self.control = None
        self.publisher_threat = None
        
        self.sensor = Adafruit_DHT.DHT11
        # Set GPIO sensor is connected to
        self.gpio = 4

        # The ThingSpeak Channel  details
        self.channelID = "1410012"
        self.writeAPIKey = "GPWINVR7PERGOKSU"
        self.broker_address = "mqtt.thingspeak.com"
        self.user = "mwa0000009686187"
        self.mqttAPIKey = "TVIUC0UTDT9YOJ4I"
        self.tTransport = "websockets"
        self.tPort = 80

        self.TOPIC = "channels/" + self.channelID + "/publish/" + self.writeAPIKey
        
    def push(self):
        while self.control:
            try:
                # code to get temperature and humidity values
                humidity, temperature = Adafruit_DHT.read_retry(
                    self.sensor, self.gpio)

                if humidity is not None and temperature is not None:
                    print(
                        'Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))
                else:
                    print('Failed to get reading. Try again!')
                    continue

                # build the payload string.
                payload = "field1=" + str(temperature)+"&field2="+str(humidity)

                # publish to the topic.
                publish.single(self.TOPIC, payload, hostname=self.broker_address, transport=self.tTransport, port=self.tPort, auth={
                               'username': self.user, 'password': self.mqttAPIKey})

                time.sleep(2)

            except Exception as e:
                print('Exception: push ', str(e))

    def start(self):
        # function to start the push data thread
        self.control = True
        self.publisher_threat = threading.Thread(target=self.push)
        self.publisher_threat.start()

    def stop(self):
        # funtion to stop push data thread
        self.control = False
        self.publisher_threat.join()


class Subscribe:
    
    def __init__(self):
        self.URL = 'https://api.thingspeak.com/channels/1410012/feeds.json?results=1'

    def fetchdata(self):
        # function to fetch date from Chennel API
        with urlopen(self.URL) as url:
            data = json.loads(url.read().decode())

            return (
                data['feeds'][-1]['created_at'].split('T')[0],
                data['feeds'][-1]['created_at'].split('T')[1][:-1],
            )
            

class GUI:
   
    def __init__(self):
        
        # object of Publish class and flag to track thread status 
        self.publisher = Publish()
        self.pub_flag = True

        # object of Subscribe class and thread status flag.
        self.subscriber = Subscribe()
        self.sub_flag = True
        self.subscriber_thread = None
        self.control = None

        # gui
        self.root = Tk()
        self.root.title('ThingSpeak PUBLISH SUBSCRIBE')

        # frame for start publishing
        self.pub_frame = LabelFrame(
            self.root, text='Publish', padx=61, pady=61)
        self.pub_frame.grid(row=0, column=0, padx=10, pady=10)

        # frame for subscribing
        self.sub_frame = LabelFrame(
            self.root, text='Subscribe', padx=30, pady=30)
        self.sub_frame.grid(row=0, column=1, padx=10, pady=10)

        # Status View publishing
        self.status_text = StringVar()
        self.status_text.set('Current Status')

        self.status_view = Label(self.pub_frame, textvariable=self.status_text)
        self.status_view.grid(row=0, column=0)

        # Status View subscrbe
        self.temperature_view = Label(self.sub_frame, text='Temperature')
        self.humidity_view = Label(self.sub_frame, text='Humidity')
        self.temperature_view.grid(row=0, column=0)
        self.humidity_view.grid(row=1, column=0)

        # Status view for subsscribing
        self.subscription_status_text = StringVar()
        self.subscription_status_text.set('Unsubscribed')
        self.subscription_status = Label(
            self.sub_frame, textvariable=self.subscription_status_text, anchor=W)
        self.subscription_status.grid(row=2, column=0)

        # Data view
        self.temperature = Entry(self.sub_frame)
        self.humidity = Entry(self.sub_frame)
        self.temperature.grid(row=0, column=1)
        self.humidity.grid(row=1, column=1)
        self.temperature.insert(0, 'xx.x')
        self.humidity.insert(0, 'xx.x')

        # adding button in publishing frame.
        self.start = Button(self.pub_frame, text='Start',
                            command=self.start_pub)
        self.stop = Button(self.pub_frame, text='Stop', command=self.stop_pub)
        self.start.grid(row=2, column=0)
        self.stop.grid(row=3, column=0)

        # adding button in subscribe frame.
        self.sub = Button(self.sub_frame, text='Subscribe',
                          command=self.start_sub)
        self.cancel = Button(self.sub_frame, text='Unsubscribe',
                             command=self.stop_sub)
        self.sub.grid(row=3, column=0)
        self.cancel.grid(row=3, column=1)

        self.root.mainloop()

    def loader(self):
        # function runs in a different thread and update the data of text view
        while self.control:

            # get current data.
            current_state = self.subscriber.fetch_update()
            print(current_state)

            # update all text view
            
            self.temperature.delete(0, END)
            self.temperature.insert(0, current_state[0])

            self.humidity.delete(0, END)
            self.humidity.insert(0, current_state[1])

            time.sleep(2)

    def start_sub(self):
        # on subscribe click event
        # starts leader thead
        if self.sub_flag:
            self.sub_flag = False
            print('Start sub')

            # start thread
            self.control = True
            self.subscriber_thread = threading.Thread(target=self.loader)
            self.subscriber_thread.start()

            # start progress bar and chnage subscription status
            self.sub_prog.start(10)
            self.subscription_status_text.set('subscribed')

    def stop_sub(self):
        # on unsubscribe click event
        # stops the leader thead
        if not self.sub_flag:
            self.sub_flag = True
            print('Stop sub')

            # stop infinite loop
            self.control = False

            # stop progress bar and chnage subscription status
            self.sub_prog.stop()
            self.subscription_status_text.set('unsubscribed')

    def start_pub(self):
        # on click event of publish
        # starts publisher thread

        if self.pub_flag:
            self.pub_flag = False
            print('Start pub')

            self.publisher.start()
            self.pub_prog.start(20)
            self.status_text.set('Started')

    def stop_pub(self):
        # on click event of publish
        # starts publisher thread

        if not self.pub_flag:
            self.pub_flag = True
            print('Stop pub')

            self.publisher.stop()
            self.pub_prog.stop()
            self.status_text.set('Stopped')


# start GUI
GUI()
