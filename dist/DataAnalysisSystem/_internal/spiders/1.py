import pandas as pd

def update_types(file_path, output_file):
    """
    读取 Excel 文件，检查每一行“电影”和“票房（万）”列后的列，如果有“1”，则把那一列的列名加到该行对应的“类型”列中。
    如果“类型”列原先有内容，就保留原先的内容并在其基础上追加新的类型。

    :param file_path: 输入 Excel 文件的路径
    :param output_file: 输出 Excel 文件的路径
    """
    # 读取 Excel 文件
    df = pd.read_excel(file_path)

    # 获取所有列名
    columns = df.columns.tolist()

    # 找到“电影”和“票房（万）”列的位置
    movie_col = columns.index('电影')

    # 遍历每一行
    for index, row in df.iterrows():
        existing_types = str(row['类型']).strip()  # 获取现有的类型内容
        new_types = []

        # 检查“票房（万）”列之后的每一列
        for col in columns[movie_col + 2:]:
            if row[col] == 1:
                new_types.append(col)

        # 将找到的类型连接起来，并追加到现有类型后面
        if existing_types:
            updated_types = f"{existing_types}, {' '.join(new_types)}"
        else:
            updated_types = ', '.join(new_types)

        df.at[index, '类型'] = updated_types.strip()

    # 保存到新的 Excel 文件
    df.to_excel(output_file, index=False)
    print(f"数据已更新并保存到 {output_file}")

if __name__ == '__main__':
    # 定义输入和输出文件路径
    path = "D:\\桌面\\数据新闻\\结果\\2015七夕.xlsx"
    file_path = path  # 替换为你的输入 Excel 文件路径
    output_file = path  # 替换为你的输出 Excel 文件路径

    # 调用函数更新类型
    update_types(file_path, output_file)