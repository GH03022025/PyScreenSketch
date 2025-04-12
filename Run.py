import tkinter as tk
from pynput import mouse
import pyautogui
import queue
import threading


class MouseTracker:
    def __init__(self):
        # 创建主窗口
        self.root = tk.Tk()

        # 获取屏幕分辨率
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # 设置全屏窗口
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.5)


        # 创建画布
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 初始化轨迹记录相关变量
        self.points_queue = queue.Queue()
        self.last_x, self.last_y = None, None

        # 设置鼠标监听器
        self.listener = None
        self.running = True

        # 绑定退出事件
        self.root.bind('<Escape>', self.exit_program)
        self.root.protocol("WM_DELETE_WINDOW", self.exit_program)

        # 启动鼠标监听线程
        self.setup_listener()

        # 启动队列处理循环
        self.root.after(10, self.process_queue)
        self.root.mainloop()

    def setup_listener(self):
        """初始化鼠标监听器"""
        self.listener = mouse.Listener(on_move=self.on_move)
        self.listener.start()

    def on_move(self, x, y):
        """鼠标移动事件回调"""
        self.points_queue.put((x, y))

    def process_queue(self):
        """处理坐标队列绘制轨迹"""
        while not self.points_queue.empty():
            x, y = self.points_queue.get()

            # 在当前位置绘制采样点圆形
            radius = 15  # 圆形半径
            self.canvas.create_oval(
                x - radius, y - radius,
                x + radius, y + radius,
                fill='red',  # 圆形颜色
                outline='',  # 无边框
                tags='point'  # 添加标签方便后期管理
            )

            # 如果存在前一个点，则绘制轨迹线段
            if self.last_x is not None and self.last_y is not None:
                self.canvas.create_line(
                    self.last_x, self.last_y, x, y,
                    fill='lime',  # 轨迹颜色
                    width=10,  # 轨迹粗细
                    capstyle=tk.ROUND,
                    smooth=tk.TRUE,
                    tags='trail'  # 添加标签方便后期管理
                )

            # 更新上一个点的坐标
            self.last_x, self.last_y = x, y

        # 继续处理队列
        if self.running:
            self.root.after(10, self.process_queue)

    def exit_program(self, event=None):
        """安全退出程序"""
        self.running = False
        if self.listener:
            self.listener.stop()
        self.root.destroy()


if __name__ == "__main__":
    # 运行前提示
    print("程序已启动 - 按ESC键或关闭窗口退出")
    print("正在绘制鼠标轨迹...")

    # 创建并运行跟踪器
    tracker = MouseTracker()