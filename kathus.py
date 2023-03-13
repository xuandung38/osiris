import configparser
import telegram
import psutil
import time
import subprocess
import pyautogui
import win32serviceutil
import win32service
import win32event

class ServiceManager:
    def __init__(self, config):
        # Lấy thông tin cấu hình từ file config
        self.config = config
        self.bot_token = config['Service']['bot_token']
        self.chat_id = config['Service']['chat_id']
        self.check_interval = int(config['Service']['check_interval'])
        self.processes = config['Processes']['process_list'].split(',')
        self.process_paths = {process: config['Processes']['{}_exe_path'.format(process)].replace('\\', '/') for process in self.processes}

    def start_process(self, process_name):
        # Khởi động chương trình chỉ định
        subprocess.Popen([self.process_paths[process_name]])
        time.sleep(5)
        return psutil.pid_exists(self.get_pid(process_name))

    def get_pid(self, process_name):
        # Lấy PID của chương trình chỉ định
        return psutil.Process('{}.exe'.format(process_name)).pid

    def click_button(self):
        # Click vào nút trên màn hình
        button_x, button_y = pyautogui.locateCenterOnScreen('path/button.png')
        pyautogui.click(button_x, button_y)

    def send_telegram_notification(self, message):
        # Gửi thông báo qua Telegram
        bot = telegram.Bot(token=self.bot_token)
        bot.sendMessage(chat_id=self.chat_id, text=message)

    def run(self):
        # Vòng lặp kiểm tra các chương trình
        while True:
            for process_name in self.processes:
                pid = self.get_pid(process_name)
                if not psutil.pid_exists(pid):
                    # Nếu chương trình không tồn tại, khởi động lại và gửi thông báo
                    if self.start_process(process_name):
                        self.click_button()
                        self.send_telegram_notification('{} đã bị đơ hoặc không khởi chạy. Đã khởi động lại.'.format(process_name))
                    else:
                        self.send_telegram_notification('Không thể khởi động lại {}.'.format(process_name))
            time.sleep(self.check_interval)

class KathusService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'KathusService'
    _svc_display_name_ = 'Kathus Service'
    _svc_description_ = 'Dịch vụ kiểm tra xem các chương trình được chỉ định có đang chạy hay không và khởi động lại chúng nếu chương trình bị lỗi hoặc không chạy.'

    def __init__(self, args):
        super().__init__(args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        # Đọc file config và khởi tạo ServiceManager
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.service_manager = ServiceManager(config)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        # Chạy ServiceManager
        self.service_manager.run()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(KathusService)