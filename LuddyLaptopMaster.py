# LuddyLaptopMaster.py - LASG/PBAI
# Created by Adam Francey, March 16 2018
# This code resides on the master laptop at Amatria in Luddy Hall
# Reads and writes UDP data to each connected Raspberry Pi
# Reads and writes OSC messages to the 4DSOUND laptop
# Coordinates global behaviour

# THINGS TO CHANGE WHEN TESTING:
# IP addresses, path_to_logs_folder

#TEST_teensy_int = 336632
#TEST_teensy_bytes = bytes([(TEST_teensy_int >> 16) & 255,(TEST_teensy_int >> 8) & 255, (TEST_teensy_int) & 255])
#TEST_pi = '192.168.2.91'
TEST_teensy_int = 245744
TEST_teensy_bytes = bytes([(TEST_teensy_int >> 16) & 255,(TEST_teensy_int >> 8) & 255, (TEST_teensy_int) & 255])
TEST_pi = '192.168.1.94'

# standard python libraries
import socket # for UDP
import threading
import time
import queue
import random

#Server
from pythonosc import dispatcher
from pythonosc import osc_server

#Client
from pythonosc import osc_message_builder
from pythonosc import udp_client

# LASG python libraries
import DeviceLocator # Auto generated from device_locator_generator.py and a .csv file of actuator properties
import FutureActions # Execute functions at a certain time in the future
import GroupActions # Coordinated actions for groups of actuators (aka sphereunit, SSS, breathing pore, etc).
                    # Uses OSC interface
                    
import Excitor # Stores incoming excitor information
import Tools # Useful functions
import Learning

device_locator = DeviceLocator.DeviceLocator()
future_manager = FutureActions.FutureActions()
excitor = Excitor.Excitor()

path_to_logs_folder = 'C:\\Users\\Studio\\Desktop\\logs\\' #ROM

# if logs folder doesn't exist, create it
import os
if not os.path.isdir(path_to_logs_folder):
    os.makedirs(path_to_logs_folder)

# CHANGE THESE IP ADDRESSES
IP_4D_LAPTOP = device_locator.IP_4D_LAPTOP
IP_MASTER = device_locator.IP_MASTER
pi_ip_addresses = device_locator.pi_ip_addresses

# for testing at home
#pi_ip_addresses = ['192.168.1.94']

group_actions = GroupActions.GroupActions(IP_MASTER)

# class for holding global variables
class SYSTEM():

    def __init__(self):
        self.on = True

        # modifiable params
        # Background Behaviour Timing Parameters
        self.background_behaviour_min_time = 45000
        self.background_behaviour_max_time = 90000

        #Lone Actuator Selection
        self.prob_RANDOM_ACTUATOR = 20
        self.ramp_up_time_RANDOM_ACTUATOR = 2000
        self.hold_time_RANDOM_ACTUATOR =1000
        self.ramp_down_time_RANDOM_ACTUATOR = 3000
        self.cooldown_time_RANDOM_ACTUATOR = 20000
        self.max_brightness_RANDOM_ACTUATOR = 240

        #Light Column Timing Parameters
        self.local_trigger_act_time = 5000
        self.local_trigger_variance = 1# on Teensy: 1/100.0 = 0.01 default, range: 0-100
        self.local_trigger_chain_width = 5 # on teensy: 10.0*5/100.0 = 0.5 default, range = 0-100
        self.local_trigger_act_time_AUTO = 3000

        #BP reflex behaviour
        self.ramp_up_time_BP_moth=1500
        self.ramp_up_time_BP_RS=1500
        self.ramp_down_time_BP_moth=2500
        self.ramp_down_time_BP_RS=2500
        self.hold_time_BP_moth=1000
        self.hold_time_BP_RS=1000

        #IR cool down time between triggers
        self.IR_min_time_between_triggers=1000
        self.next_random_sweep_time = int(time.time()) + 60


class Learning_System():
    def __init__(self):

        ### LEARNING PARAMETERS
        
        self.num_params = 17
        self.param_mins = [0,0,0,0,0,0,0,0,0,15000,60000,0,0,0,1000,5,200]
        self.param_maxs = [5000,5000,5000,5000,5000,5000,255,5000,5000,60000,100000,10000,100,5000,5000,200,400]
        self.number_of_bytes_to_encode = [2,2,2,2,2,2,1,2,2,3,3,2,1,0,0,0,0]
        self.num_teensy_params = 13
        self.param_defaults = [1500,1500,1000,1000,2500,2500,200,1500,300,45000,90000,5000,40,1800,700,120,240]
        self.reset_data_bytes = self.get_reset_data_bytes_for_teensy()
        print(self.reset_data_bytes)
        self.param_current_values = [0]*self.num_params
        for i in range(self.num_params):
            self.param_current_values[i] = self.param_defaults[i]

        # Teensy-side parameters (defaults)
        #1a)#min:0, max:5000
        self.ramp_up_time_BP_moth = 1500 #1
        self.ramp_up_time_BP_RS = 1500 #2

          #1b)#min:0, max:5000
        self.hold_time_BP_moth = 1000 #3
        self.hold_time_BP_RS = 1000 #4

          #1c)#min:0, max:5000
        self.ramp_down_time_BP_moth = 2500 #5
        self.ramp_down_time_BP_RS = 2500 #6

          #1d)#min:0, max:255
        self.max_brightness_BP_IR_TRIGGER = 200 #7

          #2)#min:0, max:5000
        self.RS_time_offset_BP_IR_TRIGGER = 1500 #8

          #3)#min:0, max:5000
        self.delay_between_SMA_BP_IR_TRIGGER = 300 #9

          #5a)#min:15000, max:60000
        self.background_behaviour_min_time = 45000 #10

          #5b)#min:60000, max:100000
        self.background_behaviour_max_time = 90000 #11

          #6a)#min:0, max:10000
        self.cooldown_time_RANDOM_ACTUATOR = 5000 #12

          #6b)#min:0, max:100
        self.prob_RANDOM_ACTUATOR = 40 #13

        
        # Master-side parameters
        #4) #min:0, max:5000
        self.delay_time_BP_NEIGHBOUR = 1800 #14

        #7) min: 100, max: 5000
        self.time_to_choose_random_SMA = 700 #15
        

        #8a) #min:5, max:200
        self.min_time_BP_SWEEP = 120 #16
        
        #8b) min:200, max:400
        self.max_time_BP_SWEEP = 240 #17
        

        ### SENSOR VALUES
        self.current_sensor_values = {'IR1-1': 0, 'IR1-2': 0, 'IR2-1': 0, 'IR2-2': 0, 'IR3-1': 0, 'IR3-2': 0, 'IR4-1': 0, 'IR4-2': 0,
                                      'IR5-1': 0, 'IR5-2': 0, 'IR6-1': 0, 'IR6-2': 0, 'IR7-1': 0, 'IR7-2': 0, 'IR8-1': 0, 'IR8-2': 0,
                                      'IR9-1': 0, 'IR9-2': 0, 'IR10-1': 0, 'IR10-2': 0, 'IR11-1': 0, 'IR11-2': 0, 'IR12-1': 0, 'IR12-2': 0}

        ### Control Variables
        self.time_of_last_observation = 0
        self.sampling_interval = 0.1
        

    def get_observation(self):
        # outputs current sensor values, transformed to fit within range [0,1]
        if time.time() - self.time_of_last_observation >= self.sampling_interval:
            self.time_of_last_observation = time.time() 
            sensor_value_list = []
            num_bp = 12
            for i in range(1, num_bp+1):
                key = 'IR' + str(i) + '-1'
                sensor_value_list.append(self.current_sensor_values[key]/1023.)
                key = 'IR' + str(i) + '-2'
                sensor_value_list.append(self.current_sensor_values[key]/1023.)
            sensor_logging.record_sensor_value_list(sensor_value_list)
            return(True, sensor_value_list)
        else:
            return(False, [])
            

    def take_action(self, action_list):

        #print("starting to take action")

        data_list = []

        # get actions and transform to proper values
        for i in range(len(action_list)):

            #get actions and transform to proper values
            normed_val = action_list[i] # this value is between -1 and 1
            actual_val = int((self.param_maxs[i] - self.param_mins[i])*(normed_val + 1)/2. + self.param_mins[i])

            self.param_current_values[i] = actual_val

            if i < self.num_teensy_params:

                # this data needs to get sent to nodes
                
                num_bytes_to_encode = self.number_of_bytes_to_encode[i]

                for b in range(num_bytes_to_encode - 1, -1, -1):
                    data_list.append((actual_val >> (b*8)) & 255)
            else:
                # this data sets parameters on master
                if i == 13:
                    self.delay_time_BP_NEIGHBOUR = actual_val
                if i == 14:
                    self.time_to_choose_random_SMA = actual_val
                if i == 15:
                    self.min_time_BP_SWEEP = actual_val
                if i == 16:
                    self.max_time_BP_SWEEP = actual_val

        # send data to each Teensy
        #print(str(action_list) + ", time: " + str(time.time()))
        send_data_and_code_to_all_Teensies(bytes(data_list), LEARNING_PARAMETERS, 'BP')
        
    def take_raw_action(self, action_list):
        # action list: [SMA1-1,SMA1-2,...,SMA1-6, RS1-1,moth1-1, SMA2-1,...,SMA2-6, RS2-1, moth2-1,
        #                SMA3-1, SMA3-2,...]
        # RS1, moth1, RS2, moth2
        #
        max_brightness = 200
        num_bytes_per_BP = 16
        for BP in range(12):
            SMA_data_list = []
            PWM_data_list = []
            
            # indices 0 to 5 are SMA on BP#-1
            for SMA in range(6):
                normed_val = action_list[num_bytes_per_BP*BP + SMA]
                if normed_val < 0:
                    # SMA off
                    actual_val = 0
                else:
                    #SMA on
                    actual_val = 1
                SMA_data_list.append(actual_val)
                
            # indices 8 to 13 are SMA on BP#-2
            for SMA in range(8, 14):
                normed_val = action_list[num_bytes_per_BP*BP + SMA]
                if normed_val < 0:
                    # SMA off
                    actual_val = 0
                else:
                    #SMA on
                    actual_val = 1
                SMA_data_list.append(actual_val)

            # indices 6 and 7 are RS#-1 and moth#-1
            normed_val = action_list[num_bytes_per_BP*BP + 6]
            actual_val = int(max_brightness*(normed_val + 1)/2.)
            PWM_data_list.append(actual_val)

            normed_val = action_list[num_bytes_per_BP*BP + 7]
            actual_val = int(max_brightness*(normed_val + 1)/2.)
            PWM_data_list.append(actual_val)

            # indices 14 and 15 are RS#-2 and moth#-2
            normed_val = action_list[num_bytes_per_BP*BP + 14]
            actual_val = int(max_brightness*(normed_val + 1)/2.)
            PWM_data_list.append(actual_val)

            normed_val = action_list[num_bytes_per_BP*BP + 15]
            actual_val = int(max_brightness*(normed_val + 1)/2.)
            PWM_data_list.append(actual_val)

            slave_mode.send_SET_ACTUATOR_VALUES_BP_command(PWM_data_list, SMA_data_list, BP+1)

    def setup_raw_action(self):
        print("setup raw action")
        send_data_and_code_to_all_Teensies(bytes([1]), SLAVE_MODE, 'BP')

    def get_reset_data_bytes_for_teensy(self):
        data_list = []
        for i in range(self.num_teensy_params):
            num_bytes_to_encode = self.number_of_bytes_to_encode[i]

            for b in range(num_bytes_to_encode - 1, -1, -1):
                data_list.append((self.param_defaults[i] >> (b*8)) & 255)
        return bytes(data_list)

    def reset(self):
        print("reset")
        action_list = [-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]*12
        learning_system.take_raw_action(action_list)
        send_data_and_code_to_all_Teensies(bytes([0]), SLAVE_MODE, 'BP')
        send_data_and_code_to_all_Teensies(self.reset_data_bytes, LEARNING_PARAMETERS, 'BP')
        self.delay_time_BP_NEIGHBOUR = self.param_defaults[13]
        self.time_to_choose_random_SMA = self.param_defaults[14]
        self.min_time_BP_SWEEP = self.param_defaults[15]
        self.max_time_BP_SWEEP = self.param_defaults[16]
        
            
        

class Sensor_Logging():
    def __init__(self):
        self.current_filename = ''
        self.file_creation_time = 0

    def new_file_and_header(self, filename):
        self.current_filename = filename + '__' + time.strftime("%B_%d_%Y_at_%H-%M-%S") + '.csv'
        self.file_creation_time = time.time()
        with open(self.current_filename, 'w') as f:
            f.write("---------------------------------------------------\n")
            f.write("----------------SENSOR VALUES----------------------\n")
            f.write("File creation time: " + str(self.file_creation_time) + "\n")
            f.write("---------------------------------------------------\n")
            f.write("timestamp,")
            for i in range(1,13):
                f.write('IR' + str(i) + '-1,IR' + str(i) + '-2,')
            f.write('\n')

    def record_sensor_samples(self, filename):
        with open(filename, 'a') as f:
            f.write(str(time.time() - self.file_creation_time) + ',')
            for i in range(1,13):
                key = 'IR' + str(i) + '-1'
                f.write(learning_system.current_sensor_values[key] + ',')
                key = 'IR' + str(i) + '-2'
                f.write(learning_system.current_sensor_values[key] + ',')
            f.write('\n')
            
    def record_sensor_value_list(self, sensor_value_list):
        with open(self.current_filename, 'a') as f:
            f.write(str(time.time() - self.file_creation_time) + ',')
            f.write(str(sensor_value_list)[1:len(str(sensor_value_list))-1] + '\n')


class Slave_Mode():
    def __init__(self):
        self.on = False

    def send_SLAVE_MODE_command_to_all(self, on_or_off):
        send_data_and_code_to_all_Teensies(bytes([on_or_off]), SLAVE_MODE, 'BP')

    def send_SET_ACTUATOR_VALUES_BP_command(self, PWM_values_list, SMA_states_list, BP):

        #print("BP: " + str(BP) + ", time: " + str(time.time()))
        #print("PWM: " + str(PWM_values_list))
        #print("SMA: " + str(SMA_states_list))

        # get data
        time_to_fade = 1000
        time_hi =(time_to_fade >> 8) & 255 # high byte
        time_lo = time_to_fade & 255 # low byte
        data = bytes([time_hi, time_lo] + PWM_values_list + SMA_states_list)
        length = bytes([len(data)])
        
        # get teensy
        pi = device_locator.amatria['BP' + str(BP) + '-1']['RS' + str(BP) + '-1']['pi_ip']
        tid = device_locator.amatria['BP' + str(BP) + '-1']['RS' + str(BP) + '-1']['teensy_id_bytes']
        raw_bytes = SOM + tid + length + SET_ACTUATOR_VALUES_BP + data + EOM
        send_bytes(raw_bytes, pi)      

system = SYSTEM()
learning_system = Learning_System()
sensor_logging = Sensor_Logging()
slave_mode = Slave_Mode()

# instruction codes
TEST_LED_PIN_AND_RESPOND = b'\x00'
REQUEST_TEENSY_IDS = b'\x01'
FADE_ACTUATOR_GROUP = b'\x06'
IR_TRIGGER = b'\x07'
IR_SAMPLING = b'\x08'
SET_IR_THRESHOLD = b'\x09'
SET_SINE_FREQUENCY = b'\x0a'
SET_SINE_AMPLITUDE = b'\x0b'
SET_SINE_PHASE = b'\x0c'
ACTUATE_SMA = b'\x0d'
EXCITOR_POSITION = b'\x0e'
EXCITOR_PROPERTIES = b'\x0f'
GAUSSIAN_SHOT = b'\x10'
SYSTEM_PROPERTIES = b'\x11'
DO_NEIGHBOUR_BEHAVIOUR = b'\x12'
STOP = b'\x13'
START = b'\x14'
LEARNING_PARAMETERS = b'\x15'
SET_ACTUATOR_VALUES_BP = b'\x17'
ACTUATOR_SAMPLING_BP = b'\x18'
SLAVE_MODE = b'\x19'

# command delimiters
SOM = b'\xff\xff'
EOM = b'\xfe\xfe'

connected_teensies = {} # connected_teensies[pi_addr] = [list of bytes objects, each element is bytes objects for one teensy]
received_connected_teensies = {} #received_connected_teensies[pi_addr] = True or False if we received connected Teensies

# initialize a queue for each pi
pi_incoming_bytes_queue = {} # pi_incoming_bytes_queue[pi ip address] = queue for that pi
for pi_addr in pi_ip_addresses:
    pi_incoming_bytes_queue[pi_addr] = queue.Queue()
    received_connected_teensies[pi_addr] = False

tested_teensies = False


# UDP Initialization    
UDP_PORT_RECEIVE = 4000
UDP_PORT_TRANSMIT = 4001
MY_IP ='0.0.0.0'

sock_transmit = socket.socket(socket.AF_INET, # Internet
                      socket.SOCK_DGRAM) # UDP

sock_receive = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock_receive.bind((MY_IP, UDP_PORT_RECEIVE))


def send_bytes(raw_bytes, ip_addr):
    sock_transmit.sendto(raw_bytes, (ip_addr, UDP_PORT_TRANSMIT))


def receive_bytes():
    while True:
        data, addr = sock_receive.recvfrom(1024) # buffer size is 1024 bytes
        pi_incoming_bytes_queue[addr[0]].put(data)
        #print("[" + time.strftime("%B_%d_%Y_at_%H-%M-%S") + "] Received UDP - Address: " + addr[0] + ", Data: " + str(data))

# this thread receives and stores UDP packets in the background
listening_thread = threading.Thread(target = receive_bytes)

# OSC Initialization
OSC_packet_queue = queue.Queue()

# Server
OSC_PORT_RECEIVE = 3001

# default handler function for all incoming OSC
def receive_all_OSC(addr, *values):
    # expect addresses like
    # /4D/code/data
    OSC_packet_queue.put([addr, values])
    #print(addr)

# parses and acts on all OSC messages
def parse_and_process_OSC(incoming_OSC):

    addr = incoming_OSC[0]
    data = incoming_OSC[1]

    # addr = '/SOURCE/CODE/IDENTIFIER'
    # data = [list of data]

    addr_list = addr.split('/')

    # addr[0] will always be ''
    source = addr_list[1]
    code = 'null'
    identifier = 'null'

    if len(addr_list) > 2:
        code = addr_list[2]

    if len(addr_list) > 3:
        identifier = addr_list[3]
        #print(identifier)

    #print(source)
    #print(code)
    if code == 'IR_SAMPLING':
        # message format
        # /TV/IR_SAMPLING/[START,STOP]
        if identifier == "START":
            send_IR_SAMPLING_command_to_all_nodes_with_sensors(1,100)
        else:
            send_IR_SAMPLING_command_to_all_nodes_with_sensors(0,100)     

    if code == 'FADE':

        # message format
        # /4D/FADE_ACTUATOR_GROUP RS-1-1-1 0 50 2000 RS-1-2-2 50 25 2000 MOTH-1-1-3 50 0 6000
        
        # data should look like
        # (actuator_id1,end1,time1,actuator_id2,end2,time2,...,actuator_idN,endN,timeN)

        pi_ip_teensy_id_tuples = []
        pin_lists = []
        end_lists = []
        time_lists = []

        num_args_per_actuator = 3
        for d in range(0, len(data),num_args_per_actuator):
            actuator = data[d]
            end = data[d+1]
            time = data[d+2]
            pin = device_locator.peripherals[actuator]['pin_number']

            pi_node = (device_locator.device_locator.peripherals[actuator]['pi_ip'], device_locator.device_locator.peripherals[actuator]['teensy_id_bytes'])
            if pi_node not in pi_ip_teensy_id_tuples:
                pi_ip_teensy_id_tuples.append(pi_node)
                pin_lists.append([])
                end_lists.append([])
                time_lists.append([])

            index = pi_ip_teensy_id_tuples.index(pi_node)
            pin_lists[index].append(pin)
            end_lists[index].append(end)
            time_lists[index].append(time)


        for node in range(len(pi_ip_teensy_id_tuples)):
            pi = pi_ip_teensy_id_tuples[node][0]
            teensy_bytes = pi_ip_teensy_id_tuples[node][1]
            pin_list = pin_lists[node]
            end_list = end_lists[node]
            time_list = time_lists[node]
            send_fade_command(pi,teensy_bytes, pin_list,end_list,time_list)


    elif "ENVFOLLOW" in code:
        # message format
        # /4D/ENVFOLLOW_[letter]:

        letter = code.split("_")[1]
        val = data[0]           

    elif code == "SET_IR_THRESHOLD":
        # message format:
        # /4D/SET_IR_THRESHOLD IR-1 400

        threshold = data[0]
        sensor_name = identifier
        send_SET_IR_THRESHOLD_to_sensor(sensor_name, threshold)

    elif "excitor" in source:
        if code == "positions":
            x = int(data[0]*1000)
            y = int(data[1]*1000)
            z = int(data[2]*1000)
            excitor.position = [x,y,z]

            send_excitor_position_to_all(excitor)
        if code == "dimensions":
            x_dist = data[0]
            force_moth = data[1]
            force_RS = data[2]
            #excitor.radius = max(1,int(x_dist*100/2))
            #excitor.force = max(0,min(int(255*force/100), 255))
            excitor.radius = max(1,int(abs(x_dist)*100/2))
            excitor.force_RS = max(0,min(int(255*abs(force_RS)/100), 255))
            excitor.force_moth = max(0,min(int(255*abs(force_moth)/100), 255))
            send_excitor_properties_to_all(excitor)
                    
    elif "SMA" in source:
        actuator = source
        send_actuate_SMA([actuator])
    elif 'RS' in source:
        actuator = source
        pi, teensy_bytes = device_locator.peripherals[actuator]['pi_ip'], device_locator.peripherals[actuator]['teensy_id_bytes']
        pin = device_locator.peripherals[actuator]['pin_number']
        end_list = [data[0]]
        time_list = [data[1]]
        #print('sending_fade')
        send_fade_command(pi,teensy_bytes, [pin],end_list,time_list)
        
    elif code == 'SYSTEM_PROPERTIES':
        system.background_behaviour_min_time = data[0]
        system.background_behaviour_max_time = data[1]

        system.prob_RANDOM_ACTUATOR = data[2]
        system.ramp_up_time_RANDOM_ACTUATOR = data[3]
        system.hold_time_RANDOM_ACTUATOR =data[4]
        system.ramp_down_time_RANDOM_ACTUATOR = data[5]
        system.cooldown_time_RANDOM_ACTUATOR = data[6]
        system.max_brightness_RANDOM_ACTUATOR = data[7]

        system.local_trigger_act_time = data[8]
        system.local_trigger_variance = data[9] 
        system.local_trigger_chain_width = data[10]
        system.local_trigger_act_time_AUTO = data[11]

        system.ramp_up_time_BP_moth=data[12]
        system.ramp_up_time_BP_RS=data[13]
        system.ramp_down_time_BP_moth=data[14]
        system.ramp_down_time_BP_RS=data[15]
        system.hold_time_BP_moth=data[16]
        system.hold_time_BP_RS=data[17]

        #IR cool down time between triggers
        system.IR_min_time_between_triggers=data[18]

        send_SYSTEM_PROPERTIES_to_all()


def send_excitor_position_to_all(ex):
    pos = ex.position

    x_sign, y_sign, z_sign = 0,0,0

    if pos[0] < 0:
        x_sign = 1
    if pos[1] < 0:
        y_sign = 1
    if pos[2] < 0:
        z_sign = 1
        
    x_hi =(abs(pos[0]) >> 8) & 255 # high byte
    x_lo = abs(pos[0]) & 255 # low byte
    y_hi =(abs(pos[1]) >> 8) & 255 # high byte
    y_lo = abs(pos[1]) & 255 # low byte
    z_hi =(abs(pos[2]) >> 8) & 255 # high byte
    z_lo = abs(pos[2]) & 255 # low byte

    data = bytes([x_sign, x_hi, x_lo, y_sign, y_hi, y_lo, z_sign, z_hi, z_lo])
    length = bytes([9])
    for pi in device_locator.pi_ip_addresses:
        for teensy_bytes in device_locator.network[pi]['teensy_ids_bytes']:
            raw_bytes = SOM + teensy_bytes + length + EXCITOR_POSITION + data + EOM
            send_bytes(raw_bytes, pi)
                    
# OSC initialization
dispatcher = dispatcher.Dispatcher()
dispatcher.set_default_handler(receive_all_OSC)
OSC_listener = osc_server.BlockingOSCUDPServer(('0.0.0.0', OSC_PORT_RECEIVE), dispatcher)
OSC_listener_thread = threading.Thread(target=OSC_listener.serve_forever)

# Client
OSC_PORT_TRANSMIT = 3000
OSC_client = udp_client.UDPClient(IP_4D_LAPTOP, OSC_PORT_TRANSMIT)

# UDP clients for TV
TV_PORT_TRANSMIT = 8051
TV1_client = ('140.182.98.224', TV_PORT_TRANSMIT)
TV2_client = ('140.182.98.225', TV_PORT_TRANSMIT)
TV3_client = ('140.182.98.226', TV_PORT_TRANSMIT)
TV4_client = ('140.182.98.227', TV_PORT_TRANSMIT)
TV5_client = ('140.182.98.228', TV_PORT_TRANSMIT)
TV6_client = ('140.182.98.229', TV_PORT_TRANSMIT)
TV7_client = ('140.182.98.230', TV_PORT_TRANSMIT)
TV8_client = ('140.182.98.231', TV_PORT_TRANSMIT)

TV_UDPsocket = socket.socket(socket.AF_INET, # Internet
                                  socket.SOCK_DGRAM) # UDP

TV_clients = [TV1_client, TV2_client, TV3_client, TV4_client, TV5_client, TV6_client, TV7_client,TV8_client]

def send_OSC_to_4D(addr, data):
    #print("[" + time.strftime("%B_%d_%Y_at_%H-%M-%S") + "] Sending to 4D: " + str([addr, data]))
    msg = osc_message_builder.OscMessageBuilder(address = addr)
    for d in data:
        msg.add_arg(d)
    msg = msg.build()
    OSC_client.send(msg)

def send_UDP_to_TV(bytes_to_send):
    count = 1
    for c in TV_clients:
    
        #print("[" + time.strftime("%B_%d_%Y_at_%H-%M-%S") + "] Sending to TV" + str(count) + ": " + str(bytes_to_send))
        TV_UDPsocket.sendto(bytes_to_send,c)
        count+=1



# UDP message handlers
def request_connected_teensies(f):
    

    # ask for connected Teensies
    tid = b'\x00\x00\x00' # if teensy ID is \x00\x00\x00 then raspberry pi knows this message is for itself
    length = b'\x00' # no data
    raw_bytes = SOM + tid + length + REQUEST_TEENSY_IDS + EOM
    for pi in pi_ip_addresses:
        time.sleep(0.05)
        send_bytes(raw_bytes, pi)
        print("Requesting Teensies from Pi at " + pi)
        f.write("Requesting Teensies from Pi at " + pi + "\n")

def get_connected_teensies(data):
    # data is list of ints, change back to bytes
    data_bytes = bytes(data)
    teensy_ids_bytes = []
    int_ids = []
    for i in range(0, len(data), 3):
        id_bytes = data_bytes[i:i+1] + data_bytes[i+1:i+2] + data_bytes[i+2:i+3]
        teensy_ids_bytes.append(id_bytes)
        int_id = ((data_bytes[i] << 16) | (data_bytes[i+1] << 8)) | data_bytes[i+2]
        int_ids.append(int_id)
        print(str(int_id) + " (" + str(id_bytes) + ")")
    return teensy_ids_bytes

def get_connected_teensies_tofile(data, f):
    # data is list of ints, change back to bytes
    data_bytes = bytes(data)
    teensy_ids_bytes = []
    int_ids = []
    for i in range(0, len(data), 3):
        id_bytes = data_bytes[i:i+1] + data_bytes[i+1:i+2] + data_bytes[i+2:i+3]
        teensy_ids_bytes.append(id_bytes)
        int_id = ((data_bytes[i] << 16) | (data_bytes[i+1] << 8)) | data_bytes[i+2]
        int_ids.append(int_id)
        f.write(str(int_id) + " (" + str(id_bytes) + ")\n")
        print(str(int_id) + " (" + str(id_bytes) + ")")
    return teensy_ids_bytes

def test_connected_teensies():
    # checks to see if we have collected Teensy IDs from connected Pis
    # if so, send a TEST command to each teensy and returns True
    # if not, exits and returns False
    for pi in pi_ip_addresses:
        if received_connected_teensies[pi] == False:
            return False

    # test connected Teensies
    length = b'\x01' # data is only number of blinks
    data = b'\x05' # blink 20 times
    print("Sending TEST_LED_PIN_AND_RESPOND to all connected Teensies")
    for pi in pi_ip_addresses:
        for teensy in connected_teensies[pi]:
            tid = teensy
            raw_bytes = SOM + tid + length + TEST_LED_PIN_AND_RESPOND + data + EOM
            send_bytes(raw_bytes, pi)


def send_fade_command(pi, tid, pin_list, end_list, time_list):

    # pi: ip address of pi
    # tid: teensy id [bytes of len 3]
    # pin_list: pins to actuate [int list]
    # end_list: end values [int list]
    # time_list: fade times in ms [list of int]

    # to recover: fade_time == (fade_hi << 8) + fade_lo

    num_bytes_per_actuator = 4

    length = bytes([len(pin_list)*num_bytes_per_actuator])
    data = b''
    for a in range(len(pin_list)):
        fade_hi =(time_list[a] >> 8) & 255 # high byte
        fade_lo = time_list[a] & 255 # low byte
        data = data + bytes([pin_list[a], end_list[a],fade_hi, fade_lo])

    raw_bytes = SOM + tid + length + FADE_ACTUATOR_GROUP + data + EOM
    #print("[" + time.strftime("%B_%d_%Y_at_%H-%M-%S") + "] Sending FADE_ACTUATOR_GROUP to " + str(tid) + ", raw_bytes: " + str(raw_bytes))

    #print("pin list: " + str(pin_list))
    send_bytes(raw_bytes, pi)

def send_IR_SAMPLING_command_to_all_nodes_with_sensors(on_or_off, sampling_interval):

    pi_node_tuples = get_nodes_with_sensors()
    for node in pi_node_tuples:
        pi = node[0]
        tid = node[1]
        length = bytes([3])
        sample_hi =(sampling_interval >> 8) & 255 # high byte
        sample_lo = sampling_interval & 255 # low byte
        data = bytes([on_or_off, sample_hi, sample_lo])
        raw_bytes = SOM + tid + length + IR_SAMPLING + data + EOM
        send_bytes(raw_bytes, pi)
    

def get_nodes_with_sensors():
    # returns a set of (pi, node) tuples that contains sensors
    pi_ip_teensy_id_tuples = []
    for peripheral in device_locator.peripherals.keys():
        if device_locator.peripheral[actuator]['type'] == 'sensor':
            pi_node = (device_locator.peripherals[peripheral]['pi_ip'], device_locator.peripherals[peripheral]['teensy_id_bytes'])
            if pi_node not in pi_ip_teensy_id_tuples:
                pi_ip_teensy_id_tuples.append(pi_node)
    return pi_ip_teensy_id_tuples


def send_SET_IR_THRESHOLD_to_sensor(sensor_name, threshold):
    
    pin_number = device_locator.peripherals[sensor_name]['pin_number']
    pi = device_locator.peripherals[sensor_name]['pi_ip']
    tid = device_locator.peripherals[sensor_name]['teensy_id_bytes']
    length = bytes([3])
    thresh_hi =(threshold >> 8) & 255 # high byte
    thresh_lo = threshold & 255 # low byte
    data = bytes([pin_number, thresh_hi, thresh_lo])

    raw_bytes = SOM + tid + length + SET_IR_THRESHOLD + data + EOM
    #print("Sending SET_IR_THRESHOLD (" + str(threshold) + ") to " + str(tid) + " on SSS" + str(SSS) + " for IR" + str(sensor) + ", raw_bytes: " + str(raw_bytes))
    send_bytes(raw_bytes, pi)

def send_SET_SINE_to_actuators_on_sphereunit(section, actuator_list, arg_list, instruction_code):

    # sphereunit: "SPHERE##"
    # actuator_list: "RS#", "MOTH#"
    # arg_list: frequencies, amplitudes, or phases [ints < 255]
    # instruction_code: SET_SINE_FREQUENCY, SET_SINE_AMPLITUDE, SET_SINE_PHASE

    pi_ip_teensy_id_tuples = []
    pin_lists = []
    arg_lists = []
    data_lists = []
    
    for a in range(len(actuator_list)):
        actuator = actuator_list[a]
        pi_node = (device_locator.amatria[section][actuator]['pi_ip'], device_locator.amatria[section][actuator]['teensy_id_bytes'])
        if pi_node not in pi_ip_teensy_id_tuples:
            pi_ip_teensy_id_tuples.append(pi_node)
            pin_lists.append([])
            arg_lists.append([])
            data_lists.append([])
            
        pin = device_locator.amatria[section][actuator]['pin_number']
        arg = arg_list[a]

        index = pi_ip_teensy_id_tuples.index(pi_node)
        pin_lists[index].append(pin)
        arg_lists[index].append(arg)
        data_lists[index].append(pin)
        data_lists[index].append(arg)

    num_bytes_per_actuator = 2
    for node in range(len(pi_ip_teensy_id_tuples)):
        pi = pi_ip_teensy_id_tuples[node][0]
        teensy_bytes = pi_ip_teensy_id_tuples[node][1]
        pin_list = pin_lists[node]
        data_list = data_lists[node]
        length = bytes([len(pin_list)*num_bytes_per_actuator])   
        data = bytes(data_list)
        raw_bytes = SOM + teensy_bytes + length + instruction_code + data + EOM
        send_bytes(raw_bytes, pi)

def send_actuate_SMA(actuator_list):
    pi_ip_teensy_id_tuples = []
    pin_lists = []
    
    for a in range(len(actuator_list)):
        actuator = actuator_list[a]
        pi_node = (device_locator.perihperals[actuator]['pi_ip'], device_locator.peripherals[actuator]['teensy_id_bytes'])
        if pi_node not in pi_ip_teensy_id_tuples:
            pi_ip_teensy_id_tuples.append(pi_node)
            pin_lists.append([])
            
        pin = device_locator.peripherals[actuator]['pin_number']

        index = pi_ip_teensy_id_tuples.index(pi_node)
        pin_lists[index].append(pin)

    num_bytes_per_actuator = 1
    for node in range(len(pi_ip_teensy_id_tuples)):
        pi = pi_ip_teensy_id_tuples[node][0]
        teensy_bytes = pi_ip_teensy_id_tuples[node][1]
        pin_list = pin_lists[node]
        length = bytes([len(pin_list)*num_bytes_per_actuator])   
        data = bytes(pin_list)
        raw_bytes = SOM + teensy_bytes + length + ACTUATE_SMA + data + EOM
        send_bytes(raw_bytes, pi)

def send_excitor_properties_to_all(ex):
    radius_hi =(ex.radius >> 8) & 255 # high byte
    radius_lo = ex.radius & 255 # low byte
    data = bytes([radius_hi, radius_lo, ex.force_RS, ex.force_moth])
    send_data_and_code_to_all_Teensies(data, EXCITOR_PROPERTIES, None)

def send_SYSTEM_PROPERTIES_to_all():

    data = bytes([(system.background_behaviour_min_time >> 16) & 255,(system.background_behaviour_min_time >> 8) & 255, (system.background_behaviour_min_time) & 255,
                  (system.background_behaviour_max_time >> 16) & 255,(system.background_behaviour_max_time >> 8) & 255, (system.background_behaviour_max_time) & 255,
                  system.prob_RANDOM_ACTUATOR,
                  (system.ramp_up_time_RANDOM_ACTUATOR >> 8) & 255, (system.ramp_up_time_RANDOM_ACTUATOR) & 255,
                  (system.hold_time_RANDOM_ACTUATOR >> 8) & 255, (system.hold_time_RANDOM_ACTUATOR) & 255,
                  (system.ramp_down_time_RANDOM_ACTUATOR >> 8) & 255, (system.ramp_down_time_RANDOM_ACTUATOR) & 255,
                  (system.cooldown_time_RANDOM_ACTUATOR >> 8) & 255, (system.cooldown_time_RANDOM_ACTUATOR) & 255,
                  system.max_brightness_RANDOM_ACTUATOR,
                  (system.local_trigger_act_time >> 8) & 255, (system.local_trigger_act_time) & 255,
                  system.local_trigger_variance,
                  system.local_trigger_chain_width,
                  (system.local_trigger_act_time_AUTO >> 8) & 255, (system.local_trigger_act_time_AUTO) & 255,
                  (system.ramp_up_time_BP_moth >> 8) & 255, (system.ramp_up_time_BP_moth) & 255,
                  (system.ramp_up_time_BP_RS >> 8) & 255, (system.ramp_up_time_BP_RS) & 255,
                  (system.ramp_down_time_BP_moth >> 8) & 255, (system.ramp_down_time_BP_moth) & 255,
                  (system.ramp_down_time_BP_RS >> 8) & 255, (system.ramp_down_time_BP_RS) & 255,
                  (system.hold_time_BP_moth >> 8) & 255, (system.hold_time_BP_moth) & 255,
                  (system.hold_time_BP_RS >> 8) & 255, (system.hold_time_BP_RS) & 255,
                  (system.IR_min_time_between_triggers >> 8) & 255, (system.IR_min_time_between_triggers) & 255])

    send_data_and_code_to_all_Teensies(data, SYSTEM_PROPERTIES, None)


def send_GAUSSIAN_SHOT_to_node(pi, teensy_id_bytes, num_frames, variance, offset_step):

    num_frames_hi =(num_frames >> 8) & 255 # high byte
    num_frames_lo = num_frames & 255 # low byte
    variance_hi =(variance >> 8) & 255 # high byte
    variance_lo = variance & 255 # low byte
    data = bytes([num_frames_hi, num_frames_lo, variance_hi, variance_lo, offset_step])
    length = bytes([len(data)])
    raw_bytes = SOM + teensy_id_bytes + length + GAUSSIAN_SHOT + data + EOM
    send_bytes(raw_bytes, pi)

def send_DO_NEIGHBOUR_BEHAVIOUR(section):
    BP = section[-1]
    ident = section[2:]
    pi = device_locator.sections[section]['pi_ip']
    teensy_bytes = device_locator.sections[section]['teensy_id_bytes']
    data = bytes([0])
    length = bytes([len(data)])
    raw_bytes = SOM + teensy_bytes + length + DO_NEIGHBOUR_BEHAVIOUR + data + EOM
    send_bytes(raw_bytes, pi)

def coordinate_neighbour_behaviour(section_list, triggered_section):
    delay_time = 2000
    for i in range(len(section_list)):
        dist = abs(i-section_list.index(triggered_section))
        if dist != 0:
            time_to_wait = dist*delay_time
            section = section_list[i]
            pi = device_locator.sections[section]['pi_ip']
            teensy_id_bytes = device_locator.sections[section]['teensy_id_bytes']
            future_manager.add_function(time_to_wait, send_GAUSSIAN_SHOT_to_node, pi, teensy_id_bytes, 3000, 1000, 1)
            #future_manager.add_function(time_to_wait, send_DO_NEIGHBOUR_BEHAVIOUR, section)

def sweep_actuator_list(actuator_list):
    ramp_up_time = 1500
    hold_time = 1000
    ramp_down_time = 2000
    PWM_value = 200
    time_between_leds = 250

    distance = 0
    for actuator in actuator_list:
        time_to_wait = distance*time_between_leds
        pi = device_locator.peripherals[actuator]['pi_ip']
        teensy_bytes = device_locator.peripherals[actuator]['teensy_id_bytes']
        pin = device_locator.peripherals[actuator]['pin_number']
        future_manager.add_function(time_to_wait, send_fade_command, pi,teensy_bytes, [pin],[PWM_value],[ramp_up_time])
        future_manager.add_function(time_to_wait + hold_time, send_fade_command, pi,teensy_bytes, [pin],[0],[ramp_down_time])

def print_and_write_to_file(string, filepath, arg):
    # string: string to print and write
    # filepath: path to file including filename
    # arg: argument for open() - 'w' or 'a'
    print(string)
    with open(filepath, arg) as f:
        f.write(string + "\n")

def send_data_and_code_to_all_Teensies(data_bytes, code, restriction):
    for pi in device_locator.pi_ip_addresses:
        for teensy_bytes in device_locator.network[pi]['teensy_ids_bytes']:
            length = bytes([len(data_bytes)])
            raw_bytes = SOM + teensy_bytes + length + code + data_bytes + EOM
            send_bytes(raw_bytes, pi)
    

def SHUT_OFF_ACTUATORS():

    # clear future (remove queued functions)
    future_manager.reset()

    # turn off every actuator on every pi
    send_data_and_code_to_all_Teensies(bytes([]), STOP, None)

def TURN_ON_ACTUATORS():
    # turn on every actuator on every pi
    send_data_and_code_to_all_Teensies(bytes([]), START, None)

def background_SMA():
    time.sleep(0.7);

    r_bpc = random.randint(1,12)
    r_bp = random.randint(1,2)
    r_SMA = random.randint(1,6)
    actuator_list = ['SMA' + str(r_bpc) + '-' + str(r_bp) + '-' + str(r_SMA)]
    send_actuate_SMA(actuator_list)
    future_manager.add_function(learning_system.time_to_choose_random_SMA, background_SMA)

   
    
    

##################################### MAIN ######################################
tools = Tools.Tools()
print('init')

learner = Learning.Learning(learning_system)

# for testing
debug = False
send_sampling_request = True
send_sampling_stop_request = False
send_set_ir_threshold = False

log_all_IR_samples = False
time_to_log_samples = 60*60*1 # seconds to log for
sensor_logging_file = path_to_logs_folder + 'IR_samples_ROM_' + time.strftime("%B_%d_%Y_at_%H-%M-%S") + '.txt'
# initialize file
if log_all_IR_samples:
    with open(sensor_logging_file, 'w') as f:
        f.write("---------------------------------------------------\n")
        f.write("----------------SENSOR VALUES----------------------\n")
        f.write("---------------------------------------------------\n")
        for i in range(1,13):
            f.write('IR' + str(i) + '-1\tIR' + str(i) + '-2')
        f.write('\n')
        

# don't remember why I paused for a second here but I don't think it's needed
# keeping it anyway to give time for network sockets and background threads to start
time.sleep(1)
     

network_alive = False
network_alive_timeout = 10 # seconds to wait for Pi
network_alive_start_time = time.time()
listening_thread.start() # UDP
# first check for reponses from each Pi
try:
    with open(path_to_logs_folder + 'registration_amatria_' + time.strftime("%B_%d_%Y_at_%H-%M-%S") + '.txt', 'w') as logfile:
        request_connected_teensies(logfile) # asks each pi in pi_ip_addresses for a list of its connected teensies
        while (not network_alive) and (time.time() - network_alive_start_time < network_alive_timeout):

            # check each Pi for incoming response
            for pi in pi_ip_addresses:
                try:
                    # try to get a packet from the queue
                    # raises queue.Empty exception if no packets waiting in queue
                    incoming_bytes = pi_incoming_bytes_queue[pi].get(block = False)
                    code, data, tid = tools.decode_bytes(incoming_bytes)
                    if code == REQUEST_TEENSY_IDS:
                        # response from asking for Teensy IDs
                        logfile.write("Received UDP - Address: " + pi + ", Packet: " + str(incoming_bytes) + "\n")
                        logfile.write("Decoded Message:\n")
                        logfile.write("Teensies connected to pi at address " + pi + ": \n")
                        print("Received UDP - Address: " + pi + ", Packet: " + str(incoming_bytes))
                        print("Decoded Message:")
                        print("Teensies connected to pi at address " + pi + ": ")
                        connected_teensies[pi] = get_connected_teensies_tofile(data,logfile)
                        received_connected_teensies[pi] = True
                except queue.Empty:
                    pass

            # check to see if we have received response from all Pi
            found_all_pi = True
            for pi in pi_ip_addresses:
                if received_connected_teensies[pi] == False:
                    found_all_pi = False

            network_alive = found_all_pi
        print("-------------------------------------------------------------")
        logfile.write("-------------------------------------------------------------\n")
        if network_alive:
            # if we get here we have received a response from each Pi
            print("All Raspberry Pi have responded with their connected Teensies")
            logfile.write("All Raspberry Pi have responded with their connected Teensies\n")
        else:
            print("A Pi has not responded. Check log file.")
            logfile.write("A Pi has not responded. Check log file.\n")
        print("-------------------------------------------------------------")
        logfile.write("-------------------------------------------------------------\n")

           

    # Initialization (like start() on arduino)
    if send_set_ir_threshold == True:
        print("[" + time.strftime("%B_%d_%Y_at_%H-%M-%S") + "] Setting IR thresholds")
        #send_SET_IR_THRESHOLD_to_sensor(IR, thresholds[IR - 1])
        
    if send_sampling_request == True:
        print("[" + time.strftime("%B_%d_%Y_at_%H-%M-%S") + "] Requesting IR sensor data stream")
        
        send_IR_SAMPLING_command_to_all_nodes_with_sensors(1,100)
        
    if send_sampling_stop_request == True:
        send_IR_SAMPLING_command_to_all_nodes_with_sensors(0,100)
        

    tools.set_params(pi_ip_addresses,connected_teensies)

    OSC_listener_thread.start() #OSC
    start_time = time.time()

    TURN_ON_ACTUATORS()
    learning_system.reset()

    background_SMA()
    
    # MAIN LOOP (like loop() on arduino)
    system.on = True # if system.on == False we still get OSC and UDP out of queue, but do not do anything with the data
    while True:
        #print("on: " + str(system.on))

        if (int(time.time()) > system.next_random_sweep_time):
            #sweep_actuator_list(actuator_list)
            system.next_random_sweep_time = int(time.time() + random.randint(learning_system.min_time_BP_SWEEP, learning_system.max_time_BP_SWEEP))
            

        # first see if we need to do any waiting functions
        if system.on:
            future_manager.do_if_time_elapsed_and_remove()

        # check for OSC message from 4d laptop
        try:
            incoming_OSC = OSC_packet_queue.get(block = False)
            #print("[" + time.strftime("%B_%d_%Y_at_%H-%M-%S") + "] Incoming OSC: " + str(incoming_OSC))

            addr = incoming_OSC[0]
            if "SHUT_OFF" in addr:
                SHUT_OFF_ACTUATORS()
                system.on = False
                print("[" + time.strftime("%B_%d_%Y_at_%H-%M-%S") + "] SHUT OFF")
                
            elif "TURN_ON" in addr:
                system.on = True
                TURN_ON_ACTUATORS()

                # create new sensor log
                sensor_logging.new_file_and_header(path_to_logs_folder + 'sensor_data')

                # setup learning algorithm
                learning_setup_thread = threading.Thread(target=learner.setup_learning)
                learning_setup_thread.start()

                print("[" + time.strftime("%B_%d_%Y_at_%H-%M-%S") + "] TURN ON")
            elif system.on:
                #print("[" + time.strftime("%B_%d_%Y_at_%H-%M-%S") + "] Incoming OSC: " + str(incoming_OSC))
                parse_and_process_OSC(incoming_OSC)
                
        except queue.Empty:
            pass

        for pi in pi_ip_addresses:
            # check for waiting UDP message from a Pi
            try:
                # try to get a packet from the queue
                # raises queue.Empty exception if no packets waiting in queue
                incoming_bytes = pi_incoming_bytes_queue[pi].get(block = False)
                code, data, tid = tools.decode_bytes(incoming_bytes)
                if system.on and code == REQUEST_TEENSY_IDS:
                    # response from asking for Teensy IDs
                    print("Received UDP - Address: " + pi + ", Packet: " + str(incoming_bytes))
                    print("Decoded Message:")
                    print("Teensies connected to pi at address " + pi + ": ")
                    connected_teensies[pi] = get_connected_teensies(data)
                    received_connected_teensies[pi] = True

                elif system.on and code == TEST_LED_PIN_AND_RESPOND:
                    print("Teensy response from " + str(tid) + " on " + pi + ": " + str(data))
                    
                elif system.on and code == IR_TRIGGER:

                    # get sensor index
                    pin_num = data[0]
                    sensor_value = (data[1] << 8) + data[2]

                    triggered_section = ''
                    triggered_tid = 0

                    for peripheral in device_locator.peripherals.keys():
                        if device_locator.peripherals[peripheral]['teensy_id_int'] == tid and device_locator.peripherals[peripheral]['pin_number'] == pin_num:
                            triggered_sensor = peripheral

                    send_OSC_to_4D(send_OSC_to_4D("/4D/TRIGGER/" + triggered_sensor, [sensor_value])
                    #DO NEIGHBOUR BEHAVIOUR

                elif system.on and code == IR_SAMPLING:
                    if time.time() - start_time > 15:

                        sampled_section = ''

                        for peipheral in device_locator.peripherals.keys():
                            if device_locator.peripherals[peripheral]['teensy_id_int'] == tid:
                                sampled_teensy = tid

                        ir1 = (data[0] << 8) + data[1]
                        ir2 = (data[2] << 8) + data[3]
                        ir3 = (data[4] << 8) + data[5]
                                   
                        # to do: track and send samples

            
            except queue.Empty:
                pass

except KeyboardInterrupt:
    print("Shutting down")
    SHUT_OFF_ACTUATORS()
            

        
            
            




