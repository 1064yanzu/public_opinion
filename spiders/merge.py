import pandas as pd
import os


def merge_excel_files(file_paths, output_file):
    """
    合并多个 Excel 文件中的“电影”和“类型”列到一个新的 Excel 文件中，并跳过“类型”为空或为“null”的行。

    :param file_paths: 包含所有要合并的 Excel 文件路径的列表
    :param output_file: 输出文件的路径
    """
    # 存储所有数据的 DataFrame 列表
    dfs = []

    # 遍历每个文件路径，读取“电影”和“类型”列
    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"警告：文件 {file_path} 不存在，跳过此文件。")
            continue

        df = pd.read_excel(file_path, usecols=['电影', '类型'])

        # 跳过“类型”为空或为“null”的行
        df = df[(df['类型'].notna()) & (df['类型'] != 'null')]

        dfs.append(df)

    # 合并所有 DataFrame
    merged_df = pd.concat(dfs, ignore_index=True)

    # 去重
    merged_df.drop_duplicates(subset=['电影'], keep='first', inplace=True)

    # 保存到新的 Excel 文件
    merged_df.to_excel(output_file, index=False)
    print(f"数据已成功合并并保存到 {output_file}")


if __name__ == '__main__':
    # 定义要合并的 Excel 文件路径
    file_paths = [
        "D:\\桌面\\数据新闻\\结果\\2015七夕.xlsx",
        "D:\\桌面\\数据新闻\\结果\\merged.xlsx"
    ]

    # 定义输出文件路径
    output_file = "D:\\桌面\\数据新闻\\结果\\merged.xlsx"

    # 调用函数合并文件
    merge_excel_files(file_paths, output_file)
