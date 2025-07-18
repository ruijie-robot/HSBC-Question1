import pandas as pd
from tabula.io import read_pdf

def extract_tables(pdf_path):
    # 使用tabula提取表格数据
    tables = read_pdf(pdf_path, pages='all', multiple_tables=True)
    
    # 转换为结构化数据
    structured_data = []
    for table in tables:
        df = pd.DataFrame(table)
        # 清理数据
        df = df.dropna(how='all').reset_index(drop=True)
        structured_data.append(df.to_dict('records'))
    
    return structured_data

extract_tables("docs/Bank_Tariff_EN.pdf")