import sys
import time
import random
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QSpinBox, QCheckBox
from PyQt6.QtCore import QThread, pyqtSignal
from pynput import mouse
import pyautogui

class AutoClicker(QWidget):
    def __init__(self):
        super().__init__()

        self.monitor_resolutions = {
            "Full HD (1080p)": (1920, 1080),
            "2K": (2560, 1440),
            "4K": (3840, 2160),
        }

        self.running = False
        self.is_clicking = False
        self.initUI()
        self.listener = mouse.Listener(on_click=self.on_mouse_click)
        self.listener.start()

    def initUI(self):
        layout = QVBoxLayout()

        # Разрешение экрана
        self.label_monitor = QLabel("Выберите разрешение экрана:", self)
        layout.addWidget(self.label_monitor)
        
        self.monitor_select = QComboBox(self)
        self.monitor_select.addItems(self.monitor_resolutions.keys())
        layout.addWidget(self.monitor_select)
        
        self.label_time = QLabel("Задержка между кликами (мс):", self)
        layout.addWidget(self.label_time)
        
        # Ввод минимальной и максимальной задержки
        self.time_min = QSpinBox(self)
        self.time_min.setRange(1, 1000)
        self.time_min.setValue(10)
        layout.addWidget(self.time_min)

        self.time_max = QSpinBox(self)
        self.time_max.setRange(1, 1000)
        self.time_max.setValue(100)
        layout.addWidget(self.time_max)

        # Количество кликов от и до
        self.label_shots = QLabel("Количество кликов (от и до):", self)
        layout.addWidget(self.label_shots)

        self.shots_min = QSpinBox(self)
        self.shots_min.setRange(1, 10)
        self.shots_min.setValue(2)
        layout.addWidget(self.shots_min)

        self.shots_max = QSpinBox(self)
        self.shots_max.setRange(1, 10)
        self.shots_max.setValue(6)
        layout.addWidget(self.shots_max)
        
        # Разброс кликов
        self.enable_scatter = QCheckBox("Разброс кликов", self)
        self.enable_scatter.stateChanged.connect(self.toggle_scatter)
        layout.addWidget(self.enable_scatter)
        
        self.scatter_range = QSpinBox(self)
        self.scatter_range.setRange(1, 5)  # Максимум 5
        self.scatter_range.setValue(3)  # Стандартный разброс 3
        self.scatter_range.setEnabled(False)  # Изначально заблокировано
        layout.addWidget(self.scatter_range)
        
        # Дублирование Mouse2
        self.enable_mouse2 = QCheckBox("Дублировать Mouse2", self)
        self.enable_mouse2.stateChanged.connect(self.toggle_mouse2)
        layout.addWidget(self.enable_mouse2)
        
        self.mouse2_repeats = QComboBox(self)
        self.mouse2_repeats.addItems(["1X", "2X", "4X", "8X"])
        self.mouse2_repeats.setEnabled(False)  # Изначально заблокировано
        layout.addWidget(self.mouse2_repeats)
        
        # Кнопка запуска/остановки
        self.start_btn = QPushButton("Запустить", self)
        self.start_btn.clicked.connect(self.toggle_listener)
        layout.addWidget(self.start_btn)
        
        self.setLayout(layout)
        self.setWindowTitle("Pixel_Ping")
        self.setGeometry(100, 100, 300, 350)
    
    def toggle_listener(self):
        """Метод для старта/стопа автокликера"""
        if self.running:
            self.running = False
            self.start_btn.setText("Запустить")
            self.enable_fields(True)  # Разблокируем поля после остановки
        else:
            self.running = True
            self.start_btn.setText("Остановить")
            self.enable_fields(False)  # Блокируем поля при запуске
    
    def enable_fields(self, enable):
        """Блокирует или разблокирует поля ввода в зависимости от состояния"""
        self.shots_min.setEnabled(enable)
        self.shots_max.setEnabled(enable)
        self.time_min.setEnabled(enable)
        self.time_max.setEnabled(enable)
        self.monitor_select.setEnabled(enable)
        self.enable_scatter.setEnabled(enable)
        self.scatter_range.setEnabled(enable and self.enable_scatter.isChecked())
        self.enable_mouse2.setEnabled(enable)
        self.mouse2_repeats.setEnabled(enable and self.enable_mouse2.isChecked())

    def toggle_scatter(self):
        """Изменяет доступность поля разброса"""
        self.scatter_range.setEnabled(self.enable_scatter.isChecked())
    
    def toggle_mouse2(self):
        """Изменяет доступность поля повторов Mouse2"""
        self.mouse2_repeats.setEnabled(self.enable_mouse2.isChecked())
    
    def get_screen_center(self):
        """Возвращает центр выбранного экрана"""
        resolution = self.monitor_select.currentText()
        return self.monitor_resolutions[resolution][0] // 2, self.monitor_resolutions[resolution][1] // 2

    def on_mouse_click(self, x, y, button, pressed):
        """Запуск автоклика на нажатие правой кнопки мыши"""
        if button == mouse.Button.right and pressed and self.running and not self.is_clicking:
            self.is_clicking = True
            shots_min = self.shots_min.value()
            shots_max = self.shots_max.value()
            time_min = self.time_min.value()
            time_max = self.time_max.value()
            scatter_range = self.scatter_range.value()
            mouse2_repeats = int(self.mouse2_repeats.currentText()[0]) if self.enable_mouse2.isChecked() else 1

            # Создание и запуск потока автокликера
            self.auto_click_thread = AutoClickThread(self, shots_min, shots_max, time_min, time_max, scatter_range, mouse2_repeats)
            self.auto_click_thread.finished.connect(self.on_click_finished)
            self.auto_click_thread.start()
    
    def on_click_finished(self):
        """Установка флага завершения кликов"""
        self.is_clicking = False

class AutoClickThread(QThread):
    finished = pyqtSignal()

    def __init__(self, parent, shots_min, shots_max, time_min, time_max, scatter_range, mouse2_repeats):
        super().__init__(parent)
        self.parent = parent
        self.shots_min = shots_min
        self.shots_max = shots_max
        self.time_min = time_min
        self.time_max = time_max
        self.scatter_range = scatter_range
        self.mouse2_repeats = mouse2_repeats

    def run(self):
        """Функция для кликов на экране с учетом параметров"""
        center_x, center_y = self.parent.get_screen_center()
        shots = random.randint(self.shots_min, self.shots_max)  # Случайное количество кликов в заданном диапазоне
        scatter = self.scatter_range if self.parent.enable_scatter.isChecked() else 0
        mouse2_repeat = self.mouse2_repeats if self.parent.enable_mouse2.isChecked() else 1
        
        for _ in range(shots):
            if not self.parent.running:
                break
            # Добавлен случайный разброс кликов
            x = center_x + random.randint(-scatter, scatter)
            y = center_y + random.randint(-scatter, scatter)
            
            for _ in range(mouse2_repeat):
                pyautogui.mouseDown(x, y)
                pyautogui.mouseUp(x, y)
            
            # Время между кликами теперь зависит от заданного диапазона
            time.sleep(random.uniform(self.time_min / 1000, self.time_max / 1000))
        
        self.finished.emit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AutoClicker()
    window.show()
    sys.exit(app.exec())
