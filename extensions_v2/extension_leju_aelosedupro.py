import time
import serial
import queue
import threading
import logging

from codelab_adapter.core_extension import Extension

logger = logging.getLogger('myapp')
hdlr = logging.FileHandler('/tmp/myapp.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)


def is_positive_valid(s):
    try:
        num = int(s)
        if 0 < num < 255:
            return True
        else:
            return False
    except ValueError:
        return False


def parse_cmd(content):
    cmd = 0
    if is_positive_valid(content):
        cmd = int(content)
    return cmd


class Dongle2401:
    def __init__(self):
        self._running = True
        self.id = '1A86:7523'
        self.port = self.auto_detect()
        self.dongle = self.open_port(self.port)
        self.q_tx = queue.Queue(maxsize=512)
        self.q_rx = queue.Queue(maxsize=512)
        # threading.Thread(target=thread_handle_connect, args=(conn,)).start()

    def auto_detect(self):
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            logger.info("port = {}; desc = {} ;hwid = {}".format(port, desc, hwid))
            if self.id in hwid:
                try:
                    with serial.Serial(port, 9600) as ser:
                        ser.close()
                    print('found port {}'.format(port))
                    return port
                except Exception as err:
                    pass
                    # print('open port failed', port, err)

        assert False, 'Aelos usb dongle not found!'

    def open_port(self, port):
        return serial.Serial(port, 9600)

    def thread_tx(self):
        while self._running:
            pass

    def thread_rx(self):
        while self._running:
            pass

    def reset_cache(self):
        self.dongle.reset_input_buffer()

    def send(self, data):
        self.dongle.reset_input_buffer()
        self.dongle.write(bytes(data))

    def read(self, size):
        return self.dongle.read(size)

    def set_channel(self, channel):
        channel = channel & 0xff
        self.send([0xcc, 0xcc, 0xcc, 0xcc, 0xcc])
        rx_buf = self.read(6)
        logger.info(rx_buf)
        self.send([0x29, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, channel])
        # rx_buf = self.read(5)
        return None

    def connect_to_robot(self):
        self.send([0x83])
        return None

    def set_servo_pos(self, index, pos, speed=30):
        """设置单个舵机位置 76 00 00 00 00 00 00 00 01 60"""
        self.send([0x76, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00,
                   index, pos & 0xff])
        rx_buf = self.read(9)
        logger.info(rx_buf)
        return list(rx_buf)

    def get_servo_pos(self, index):
        """获取单个舵机位置"""
        self.send([0x75, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, index])
        rx_buf = self.read(10)
        return list(rx_buf)

    def set_servos_pos(self, angles, speed=30):
        """设置全身 19 个舵机位置"""
        pass

    def get_servos_pos(self):
        """获取全身 19 个舵机位置"""
        pass

    def lock_servo(self, index):
        """单舵机加锁"""
        pass

    def unlock_servo(self, index):
        """单舵机解锁"""
        pass

    def get_sensor(self, index):
        """获取磁吸传感器数值"""
        pass

    def set_sensor(self, index, value):
        """获取磁吸传感器数值 0~255 """
        pass

    def read_sensor_name(name):
        """按照传感器名称读取数值"""
        pass

    def run_act(self, name):
        """运行动作文件"""
        pass


def parse_content(content):
    try:
        if type(content) == str:
            arr = content.split(':')
            if len(arr) != 2:
                return None
            return arr
    except Exception as err:
        return None


class LejuAelosEduExtention(Extension):
    """
    Leju Robotics Aelos Edu Extension V2
    """
    def __init__(self):
        super().__init__()
        self.EXTENSION_ID = "eim/leju/aelosedupro"
        self.usb_dongle = Dongle2401()

    def extension_message_handle(self, topic, payload):
        self.logger.info(f'topic = {topic}')
        if type(payload) == str:
            self.logger.info(f'scratch eim message:{payload}')
            return
        elif type(payload) == dict:
            self.logger.info(f'eim message:{payload}')

            python_code = payload.get('content')

            try:
                output = eval(python_code, {"__builtins__": None}, {
                    'usb_dongle': self.usb_dongle
                })
            except Exception as e:
                output = e
                self.logger.error(output)

            payload["content"] = str(output)
            message = {"payload": payload}
            self.publish(message)

    def run(self):
        while self._running:
            time.sleep(1)


export = LejuAelosEduExtention

if __name__ == "__main__":
    LejuAelosEduExtention().run()  # or start_as_thread()
