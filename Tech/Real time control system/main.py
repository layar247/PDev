import tkinter as tk
from tkinter import ttk, messagebox
import time
import math
import random


class MNSLControlSystem:
    def __init__(self):
        self.ADC_resolution = 10
        self.DAC_resolution = 16
        self.ADC_input_range = (0, 64)
        self.DAC_output_range = (0, 24)
        self.target_level = 70
        self.max_level = 100
        self.level_0_percent_voltage = 50
        self.level_100_percent_voltage = 10.5
        self.initial_voltage = 9.8
        self.control_step = 0.025
        self.control_interval = 0.2
        self.level_threshold = 2
        self.calculate_conversion_factors()

    def calculate_conversion_factors(self):
        self.ADC_max_value = 2 ** self.ADC_resolution - 1
        self.ADC_voltage_per_step = (self.ADC_input_range[1] - self.ADC_input_range[0]) / self.ADC_max_value

        self.DAC_max_value = 2 ** self.DAC_resolution - 1
        self.DAC_voltage_per_step = (self.DAC_output_range[1] - self.DAC_output_range[0]) / self.DAC_max_value

        # Преобразование уровня в напряжение ДУМК
        self.voltage_per_percent = (self.level_0_percent_voltage - self.level_100_percent_voltage) / 100
#Преобразование уровня в напряжение ДУМК
    def level_to_voltage(self, level):
        return self.level_100_percent_voltage + (100 - level) * self.voltage_per_percent
#Преобразование напряжения ДУМК в уровень
    def voltage_to_level(self, voltage):
        return 100 - (voltage - self.level_100_percent_voltage) / self.voltage_per_percent
#Преобразование напряжения в значение АЦП
    def voltage_to_ADC_value(self, voltage):
        adc_value = int((voltage - self.ADC_input_range[0]) / self.ADC_voltage_per_step)
        return max(0, min(self.ADC_max_value, adc_value))
#Преобразование значения ЦАП в напряжение
    def DAC_value_to_voltage(self, dac_value):
        return self.DAC_output_range[0] + dac_value * self.DAC_voltage_per_step
#Преобразование напряжения в скорость ролика (м/мин)
    def voltage_to_roller_speed(self, voltage):
        return 1.0 + (voltage - 9.8)  # м/мин

class StreamController:
    def __init__(self, stream_id, control_system):
        self.stream_id = stream_id
        self.cs = control_system

        self.current_level = 70.0
        self.current_voltage = control_system.initial_voltage  # В
        self.roller_speed = 0
        self.roller_angle = 0
        self.roller_rpm = 0

        self.crystallizer_color = "green"
        self.state = "Норма"
        self.correction_count = 0

        self.previous_level = 70.0
        self.control_timer = 0

        self.update_conversions()
#обновки значений
    def update_conversions(self):
        # Напряжение ДУМК
        self.dumk_voltage = self.cs.level_to_voltage(self.current_level)
        # Значение АЦП
        self.current_ADC_value = self.cs.voltage_to_ADC_value(self.dumk_voltage)
        # Значение ЦАП
        self.current_DAC_value = int(
            (self.current_voltage - self.cs.DAC_output_range[0]) / self.cs.DAC_voltage_per_step)
        # Скорость ролика
        self.roller_speed = self.cs.voltage_to_roller_speed(self.current_voltage)
        # Обороты для анимации
        circumference = math.pi * 0.2  # диаметр ролика 0.2 м
        self.roller_rpm = self.roller_speed / circumference if circumference > 0 else 0
#физа проца
    def simulate_physics(self, dt):
        self.previous_level = self.current_level
        base_inflow = 0.22
        # Небольшие случайные возмущения
        noise = random.gauss(0, 0.01)
        slow_variation = 0.01 * math.sin(time.time() * 0.5)

        extraction_effect = (self.current_voltage - 9.8) * 0.12

        level_change = base_inflow + noise + slow_variation - extraction_effect
        self.current_level += level_change * dt
        self.current_level = max(0, min(100, self.current_level))

        # Обновление анимации ролика
        self.roller_angle += self.roller_rpm * 6 * dt

        self.update_conversions()
        self.analyze_state()
#состы
    def analyze_state(self):

        deviation = abs(self.current_level - self.cs.target_level)

        if deviation <= 1.0:
            self.state = "Идеально"
            self.crystallizer_color = "#00FF00"
        elif deviation <= 2.0:
            self.state = "Норма"
            self.crystallizer_color = "#90EE90"
        elif deviation <= 5.0:
            self.state = "Коррекция"
            self.crystallizer_color = "#FFA500"
        else:
            self.state = "Критично"
            self.crystallizer_color = "#FF0000"
#техн процес
    def control_loop(self, dt):
        self.control_timer += dt

        if self.control_timer >= self.cs.control_interval:
            level_error = self.current_level - self.cs.target_level
            level_change = self.current_level - self.previous_level
            hysteresis = 0.02
            if 2.0 <= level_error:
                if level_change >= -hysteresis:
                    self.current_voltage += self.cs.control_step
                    self.correction_count += 1
                    print(
                        f"Ручей {self.stream_id + 1}: ↑ Напряжение {self.current_voltage:.3f}В (уровень {self.current_level:.1f}%)")

            elif level_error <= -2.0:
                if level_change <= hysteresis:
                    self.current_voltage -= self.cs.control_step
                    self.correction_count += 1
                    print(
                        f"Ручей {self.stream_id + 1}: ↓ Напряжение {self.current_voltage:.3f}В (уровень {self.current_level:.1f}%)")

            # Ограничение напряжения
            self.current_voltage = max(self.cs.DAC_output_range[0],
                                       min(self.cs.DAC_output_range[1], self.current_voltage))

            self.control_timer = 0

class MNSLApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Система управления МНЛЗ - 4 ручья")
        self.root.geometry("1400x900")
        self.control_system = MNSLControlSystem()
        self.streams = [StreamController(i, self.control_system) for i in range(4)]
        self.simulation_running = False
        self.time_elapsed = 0
        self.last_update_time = time.time()
        self.setup_ui()
        self.draw_visualization()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        title_label = tk.Label(main_frame,
                               text="СИСТЕМА УПРАВЛЕНИЯ УРОВНЕМ МЕТАЛЛА В КРИСТАЛЛИЗАТОРАХ МНЛЗ",
                               font=("Arial", 16, "bold"),
                               bg="lightblue", relief=tk.RAISED, padx=10, pady=5)
        title_label.pack(pady=10, fill=tk.X)

        self.viz_canvas = tk.Canvas(main_frame, width=1350, height=450, bg="white", highlightthickness=2,
                                    highlightbackground="gray")
        self.viz_canvas.pack(pady=10)
        voltage_frame = ttk.LabelFrame(main_frame, text="Ручное управление напряжением", padding=10)
        voltage_frame.pack(pady=5, fill=tk.X)

        for i in range(4):
            stream_frame = ttk.Frame(voltage_frame)
            stream_frame.pack(side=tk.LEFT, padx=10)

            tk.Label(stream_frame, text=f"Ручей {i + 1}:", font=("Arial", 10, "bold")).pack()

            btn_frame = ttk.Frame(stream_frame)
            btn_frame.pack(pady=2)

            tk.Button(btn_frame, text="+25мВ",
                      command=lambda idx=i: self.manual_voltage_change(idx, +0.025),
                      font=("Arial", 9), bg="#2196F3", fg="white", width=8).pack(side=tk.LEFT, padx=2)

            tk.Button(btn_frame, text="-25мВ",
                      command=lambda idx=i: self.manual_voltage_change(idx, -0.025),
                      font=("Arial", 9), bg="#FF5722", fg="white", width=8).pack(side=tk.LEFT, padx=2)

        global_frame = ttk.Frame(voltage_frame)
        global_frame.pack(side=tk.RIGHT, padx=20)

        tk.Label(global_frame, text="Все ручьи:", font=("Arial", 10, "bold")).pack()

        global_btn_frame = ttk.Frame(global_frame)
        global_btn_frame.pack(pady=2)

        tk.Button(global_btn_frame, text="ВСЕМ +25мВ",
                  command=lambda: self.manual_voltage_change_all(+0.025),
                  font=("Arial", 9), bg="#4CAF50", fg="white", width=12).pack(side=tk.LEFT, padx=2)

        tk.Button(global_btn_frame, text="ВСЕМ -25мВ",
                  command=lambda: self.manual_voltage_change_all(-0.025),
                  font=("Arial", 9), bg="#F44336", fg="white", width=12).pack(side=tk.LEFT, padx=2)

        control_frame = ttk.Frame(main_frame)
        control_frame.pack(pady=5)

        self.start_button = tk.Button(control_frame, text="▶ Запуск симуляции",
                                      command=self.start_simulation, font=("Arial", 12),
                                      bg="#4CAF50", fg="white", padx=15)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(control_frame, text="⏹ Остановка",
                                     command=self.stop_simulation, font=("Arial", 12),
                                     bg="#f44336", fg="white", padx=15, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=5)

        reset_button = tk.Button(control_frame, text="🔄 Сброс",
                                 command=self.reset_simulation, font=("Arial", 12),
                                 bg="#FF9800", fg="white", padx=15)
        reset_button.pack(side=tk.LEFT, padx=5)

        advanced_frame = ttk.Frame(main_frame)
        advanced_frame.pack(pady=5)

        tk.Button(advanced_frame, text="📈 Скачок +1%",
                  command=lambda: self.simulate_level_jump(1.0), font=("Arial", 10),
                  bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=3)

        tk.Button(advanced_frame, text="📉 Скачок -1%",
                  command=lambda: self.simulate_level_jump(-1.0), font=("Arial", 10),
                  bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=3)

        tk.Button(advanced_frame, text="⚡ Помехи +0.2%",
                  command=self.simulate_noise, font=("Arial", 10),
                  bg="#9C27B0", fg="white").pack(side=tk.LEFT, padx=3)

        tk.Button(advanced_frame, text="🎯 Тест 71.9%",
                  command=lambda: self.test_algorithm(71.9), font=("Arial", 10),
                  bg="#009688", fg="white").pack(side=tk.LEFT, padx=3)

        tk.Button(advanced_frame, text="🎯 Тест 68.1%",
                  command=lambda: self.test_algorithm(68.1), font=("Arial", 10),
                  bg="#009688", fg="white").pack(side=tk.LEFT, padx=3)

        tk.Button(advanced_frame, text="📊 Статистика",
                  command=self.show_statistics, font=("Arial", 10),
                  bg="#607D8B", fg="white").pack(side=tk.LEFT, padx=3)

        self.time_label = tk.Label(main_frame, text="Время: 0.0 сек", font=("Arial", 12, "bold"))
        self.time_label.pack()

        info_frame = tk.Frame(main_frame, relief=tk.GROOVE, borderwidth=2)
        info_frame.pack(pady=5, fill=tk.X)

        system_info = tk.Label(info_frame,
                               text="ДУМК: 0% = 50В, 100% = 10.5В | АЦП: 10 бит, 0-64В | ЦАП: 16 бит, 0-24В | Алгоритм: +-25 мВ каждые 0.2с при отклонении 2-5%",
                               font=("Arial", 10), fg="blue", bg="#F0F0F0", pady=5)
        system_info.pack()
        self.draw_legend()

    def manual_voltage_change(self, stream_index, delta_voltage):
        if self.simulation_running:
            stream = self.streams[stream_index]
            old_voltage = stream.current_voltage
            stream.current_voltage += delta_voltage
            stream.current_voltage = max(self.control_system.DAC_output_range[0],
                                         min(self.control_system.DAC_output_range[1], stream.current_voltage))

            direction = "↑" if delta_voltage > 0 else "↓"
            print(
                f"🎛️ РУЧНОЕ УПРАВЛЕНИЕ: Ручей {stream_index + 1}: {direction} Напряжение {old_voltage:.3f}В → {stream.current_voltage:.3f}В")
    def manual_voltage_change_all(self, delta_voltage):

        if self.simulation_running:
            for i, stream in enumerate(self.streams):
                old_voltage = stream.current_voltage
                stream.current_voltage += delta_voltage
                stream.current_voltage = max(self.control_system.DAC_output_range[0],
                                             min(self.control_system.DAC_output_range[1], stream.current_voltage))

            direction = "↑" if delta_voltage > 0 else "↓"
            print(f"🎛️ РУЧНОЕ УПРАВЛЕНИЕ: ВСЕ ручьи: {direction} Напряжение на {delta_voltage:.3f}В")
#cкачки
    def simulate_level_jump(self, jump_size):

        if self.simulation_running:
            for stream in self.streams:
                stream.current_level += jump_size
                stream.current_level = max(0, min(100, stream.current_level))
            direction = "↑" if jump_size > 0 else "↓"
            print(f"🔔 Имитирован скачок уровня {direction}{abs(jump_size):.1f}%!")
#помехи
    def simulate_noise(self):
        if self.simulation_running:
            for stream in self.streams:
                noise = 0.2
                stream.current_level += noise
                stream.current_level = max(0, min(100, stream.current_level))
            print("🔔 Добавлены помехи +0.2%!")
    def test_algorithm(self, test_level):
        if self.simulation_running:
            for stream in self.streams:
                stream.current_level = test_level
            print(f"🔔 Запущен тест алгоритма на уровне {test_level}%!")
#стата кнопка
    def show_statistics(self):
        total_corrections = sum(stream.correction_count for stream in self.streams)
        avg_level = sum(stream.current_level for stream in self.streams) / len(self.streams)

        ideal_count = sum(1 for s in self.streams if s.state == "Идеально")
        normal_count = sum(1 for s in self.streams if s.state == "Норма")
        correction_count = sum(1 for s in self.streams if s.state == "Коррекция")
        critical_count = sum(1 for s in self.streams if s.state == "Критично")
        stats = (f"📊 Статистика системы:\n"
                 f"Общее время: {self.time_elapsed:.1f} сек\n"
                 f"Всего коррекций: {total_corrections}\n"
                 f"Средний уровень: {avg_level:.1f}%\n"
                 f"Идеально: {ideal_count} ручьев\n"
                 f"Норма: {normal_count} ручьев\n"
                 f"Коррекция: {correction_count} ручьев\n"
                 f"Критично: {critical_count} ручьев")
        tk.messagebox.showinfo("Статистика системы", stats)
#лега состов
    def draw_legend(self):
        legend_x = 1200
        legend_y = 30
        states = [
            ("Идеально (≤1%)", "#00FF00"),
            ("Норма (≤2%)", "#90EE90"),
            ("Коррекция (2-5%)", "#FFA500"),
            ("Критично (>5%)", "#FF0000")
        ]
        for i, (text, color) in enumerate(states):
            self.viz_canvas.create_rectangle(legend_x, legend_y + i * 30,
                                             legend_x + 20, legend_y + i * 30 + 20,
                                             fill=color, outline="black", width=2)
            self.viz_canvas.create_text(legend_x + 30, legend_y + i * 30 + 10,
                                        text=text, anchor="w", font=("Arial", 10, "bold"))

    def draw_visualization(self):
        self.viz_canvas.delete("all")
        self.draw_legend()
        for i, stream in enumerate(self.streams):
            self.draw_stream(i, stream)
#равсцветка на рручьи
    def draw_stream(self, index, stream):

        x_start = 150 + index * 300
        y_base = 350
        self.viz_canvas.create_rectangle(x_start - 100, y_base - 280, x_start + 100, y_base + 80,
                                         fill="#F8F8F8", outline="gray", width=1)
        self.viz_canvas.create_rectangle(x_start - 40, y_base - 200, x_start + 40, y_base,
                                         fill="lightblue", outline="black", width=2)
        metal_height = 200 * (stream.current_level / 100)
        for i in range(int(metal_height)):
            y_pos = y_base - i
            color_intensity = int(255 * (i / metal_height)) if metal_height > 0 else 0
            color = f"#{color_intensity:02x}{color_intensity // 2:02x}00"
            self.viz_canvas.create_line(x_start - 38, y_pos, x_start + 38, y_pos, fill=color)
        target_y = y_base - 140
        self.viz_canvas.create_line(x_start - 45, target_y, x_start + 45, target_y,
                                    fill="red", width=3, dash=(4, 2))
        # ролик
        roller_x = x_start
        roller_y = y_base + 40
        roller_radius = 30
        # Основание ролика
        self.viz_canvas.create_rectangle(roller_x - 40, roller_y - 12,
                                         roller_x + 40, roller_y + 12,
                                         fill="#666666", outline="black", width=2)
        # Вращающийся ролик
        self.draw_roller(roller_x, roller_y, roller_radius, stream.roller_angle, stream.roller_speed)
        # Стрелка направления
        self.viz_canvas.create_line(roller_x + roller_radius + 5, roller_y,
                                    roller_x + roller_radius + 25, roller_y,
                                    arrow=tk.LAST, width=3, fill="blue")
        # панель ифны
        info_x = x_start - 90
        info_y = y_base - 250
        info_texts = [
            f"Ручей {stream.stream_id + 1}",
            f"Уровень: {stream.current_level:5.1f}%",
            f"ДУМК: {stream.dumk_voltage:5.2f} В",
            f"Напряжение: {stream.current_voltage:5.3f} В",
            f"Скорость: {stream.roller_speed:5.2f} м/мин",
            f"Обороты: {abs(stream.roller_rpm):5.1f} об/мин",
            f"Коррекции: {stream.correction_count:3d}",
            f"Состояние: {stream.state}",
            f"АЦП: {stream.current_ADC_value:4d}",
            f"ЦАП: {stream.current_DAC_value:5d}"
        ]
        for i, text in enumerate(info_texts):
            color = "black"
            if "Идеально" in text:
                color = "green"
            elif "Критично" in text:
                color = "red"
            elif "Коррекция" in text:
                color = "orange"
            self.viz_canvas.create_text(info_x, info_y + i * 18,
                                        text=text, anchor="w", font=("Arial", 9), fill=color)
        # Индикатор состояния
        self.viz_canvas.create_rectangle(x_start - 90, info_y + 172, x_start - 70, info_y + 192,
                                         fill=stream.crystallizer_color, outline="black", width=2)
#отрисовка ролика
    def draw_roller(self, x, y, radius, angle, speed):
        # Основной круг ролика
        self.viz_canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                                    fill="#C0C0C0", outline="black", width=2)
        # Ось вращения
        self.viz_canvas.create_oval(x - 6, y - 6, x + 6, y + 6,
                                    fill="red", outline="black")
        # Индикатор вращения
        rad_angle = math.radians(angle)
        end_x = x + radius * 0.7 * math.cos(rad_angle)
        end_y = y + radius * 0.7 * math.sin(rad_angle)
        self.viz_canvas.create_line(x, y, end_x, end_y, width=4, fill="darkblue")
        # Индикатор скорости
        speed_abs = abs(speed)
        if speed_abs < 0.1:
            speed_color = "gray"
        elif speed_abs < 0.5:
            speed_color = "green"
        elif speed_abs < 1.0:
            speed_color = "orange"
        else:
            speed_color = "red"

        self.viz_canvas.create_rectangle(x - radius + 5, y - radius + 5,
                                         x - radius + 15, y - radius + 15,
                                         fill=speed_color, outline="black", width=2)
#старт симуляции
    def start_simulation(self):
        self.simulation_running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.last_update_time = time.time()
        self.simulation_loop()
#стоп
    def stop_simulation(self):
        self.simulation_running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

    # сбос
    def reset_simulation(self):
        self.simulation_running = False
        self.time_elapsed = 0
        self.streams = [StreamController(i, self.control_system) for i in range(4)]
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.time_label.config(text="Время: 0.0 сек")
        self.draw_visualization()
#цикл симки
    def simulation_loop(self):
        if not self.simulation_running:
            return
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time

        # Ограничим dt для стабильности
        dt = min(dt, 0.1)
        self.time_elapsed += dt

        for stream in self.streams:

            stream.simulate_physics(dt)
            stream.control_loop(dt)

        self.time_label.config(text=f"Время: {self.time_elapsed:.1f} сек")
        self.draw_visualization()

        if self.simulation_running:
            self.root.after(50, self.simulation_loop)
def main():
    root = tk.Tk()
    app = MNSLApplication(root)
    root.mainloop()
if __name__ == "__main__":
    main()

