import pandas as pd
from datetime import datetime
import openpyxl
import openpyxl.drawing.image
import os
import logging

logger = logging.getLogger(__name__)
class ExcelExporter:
    def __init__(self):
        # スクリプトのディレクトリを基準に output ディレクトリのパスを設定
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'output')
       
    def export_to_excel(self, worker_data, filepath):
        logger.debug(f"ExcelExporter.export_to_excel called ,filepath: {filepath}")
        # 現在の日時を取得してフォルダ名に使用
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_folder = os.path.join(self.output_dir, f"SkillMatrix_App_data_{timestamp}")
        
        # output_folder が存在しない場合は作成
        os.makedirs(output_folder, exist_ok=True)

        # データフレームの作成準備
        all_categories = set()
        for worker in worker_data.values():
            all_categories.update(worker.categories)
        all_categories = list(all_categories)

        data = {}
        for name, worker in worker_data.items():
            data[name] = pd.Series(worker.skill_levels, index=worker.categories)

        df = pd.DataFrame(data).fillna(0) #NaNを0で補完
        df = df.reindex(all_categories)

        # ファイル名に使用
        if not filepath:
            filename = os.path.join(output_folder, f"skill_data_{timestamp}.xlsx")
        else:
            filename = os.path.join(output_folder, filepath)
        logger.debug(f"ExcelExporter.export_to_excel: full_filepath = {filename}")

        # Excelファイルに出力
        try:
            df.to_excel(filename, index=True, header=True)
            logger.debug(f"ExcelExporter.export_to_excel:Excel saved to {filename}")
        except Exception as e:
            logger.error(f"ExcelExporter.export_to_excel: Error saving Excel file: {e}")
            return None

        return filename