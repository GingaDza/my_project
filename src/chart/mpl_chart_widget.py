from PyQt6.QtWidgets import QWidget, QVBoxLayout
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

class MplChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = plt.figure(figsize=(4, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.ax = None

    def plot_radar_chart(self, data, categories, title):
        """データを基にレーダーチャートを描画する。"""
        if self.ax is None:
            self.ax = self.figure.add_subplot(111, polar=True)
        else:
            self.ax.clear()

        num_vars = len(categories)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1]

        data += data[:1]

        self.ax.plot(angles, data, linewidth=2, linestyle='solid')
        self.ax.fill(angles, data, 'b', alpha=0.1)

        self.ax.set_xticks(angles[:-1])
        self.ax.set_xticklabels(categories)

        self.ax.set_theta_offset(np.pi / 2)
        self.ax.set_theta_direction(-1)

        self.ax.set_ylim(0, 5)
        self.ax.set_yticks([1, 2, 3, 4, 5])
        self.ax.set_yticklabels(['1', '2', '3', '4', '5'])

        self.ax.set_title(title)

        self.canvas.draw()


    def update_chart(self, data, categories):
        """データを基にレーダーチャートを更新するメソッド"""
        if self.ax is None:
            self.ax = self.figure.add_subplot(111, polar=True)
        else:
            self.ax.clear()

        num_vars = len(categories)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1]

        data += data[:1]

        self.ax.plot(angles, data, linewidth=2, linestyle='solid')
        self.ax.fill(angles, data, 'b', alpha=0.1)

        self.ax.set_xticks(angles[:-1])
        self.ax.set_xticklabels(categories)

        self.ax.set_theta_offset(np.pi / 2)
        self.ax.set_theta_direction(-1)

        self.ax.set_ylim(0, 5)
        self.ax.set_yticks([1, 2, 3, 4, 5])
        self.ax.set_yticklabels(['1', '2', '3', '4', '5'])

        self.canvas.draw()

    def update_comparison_chart(self, data_list, categories, worker_names):
        """複数のワーカーのデータを基にレーダーチャートを更新する。"""
        if self.ax is None:
            self.ax = self.figure.add_subplot(111, polar=True)
        else:
            self.ax.clear()

        num_vars = len(categories)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles += angles[:1]

        # 各ワーカーのデータをプロット
        for i, data in enumerate(data_list):
            data += data[:1]
            self.ax.plot(angles, data, linewidth=2, linestyle='solid', label=worker_names[i])
            self.ax.fill(angles, data, alpha=0.1)

        self.ax.set_xticks(angles[:-1])
        self.ax.set_xticklabels(categories)

        self.ax.set_theta_offset(np.pi / 2)
        self.ax.set_theta_direction(-1)

        self.ax.set_ylim(0, 5)
        self.ax.set_yticks([1, 2, 3, 4, 5])
        self.ax.set_yticklabels(['1', '2', '3', '4', '5'])

        # 凡例
        self.ax.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))

        self.canvas.draw()