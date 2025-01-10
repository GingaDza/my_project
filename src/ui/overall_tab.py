from PyQt6.QtWidgets import QWidget, QVBoxLayout
from ..chart.mpl_chart_widget import MplChartWidget
class OverallTab(QWidget):
    """
    全ワーカーのスキルレベルを総合的に表示するタブ
    """
    def __init__(self, data_manager, categories, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.categories = categories
        self.chart_widget = MplChartWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(self.chart_widget)
    
    def update_chart(self):
        """ワーカーのスキルレベルに基づいてチャートを更新する"""
        workers = self.data_manager.get_all_workers()
        if not workers:
           self.chart_widget.update_chart([],self.categories)
           print("No worker data available to update the chart.")
           return

        aggregated_skill_levels = [0] * len(self.categories)
        
        for worker in workers: # 修正箇所
           for i, level in enumerate(worker['skill_levels']):
                print("--- OverallTab: update_chart: worker skill level ---")
                print(f"  Worker: {worker['name']}, Skill Index: {i}, Level: {level}, type: {type(level)}")
                if i < len(aggregated_skill_levels):
                    aggregated_skill_levels[i] += int(level)
                else:
                   aggregated_skill_levels.append(int(level))
        
        
        self.chart_widget.update_chart(aggregated_skill_levels, self.categories)