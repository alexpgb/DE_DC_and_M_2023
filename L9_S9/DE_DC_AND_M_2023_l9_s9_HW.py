import pandas as pd
import numpy as np
import sys
from pathlib import Path

def main():
    file_for_process = ''
    file_with_marks = ''
    if len(sys.argv) < 3:
        print('Переданы не все параметры.')
        return
    file_for_process = sys.argv[1]
    file_with_marks = sys.argv[2]
    if not (Path(file_for_process).exists() and Path(file_with_marks).exists()):
        print('Файл (файлы) не существуют.')
    file_result = Path(file_with_marks).parent / (Path(file_for_process).stem + '_processed' + Path(file_for_process).suffix)
    df_google = pd.read_csv(file_for_process) # './L8_S8/googleplaystore.csv')
    df_marks = pd.read_csv(file_with_marks) # './L9_S9/googleplaystore_content_rating.csv')
    print(df_marks)
    cr_col_name = 'Content Rating'
    cri_col_name = 'Content Rating Index'
    df_google[cri_col_name] = np.NAN
    row_index = 0
    prompt = f"Укажите индекс категории {', '.join([f'{i}-{r}' for i, r in enumerate(df_marks[cr_col_name].values.tolist(), start=1)])} : " 
    df_content_ratingd_len = df_marks[cr_col_name].shape[0]
    while True:
        print(f"Наименование приложения : {df_google.loc[df_google.index[row_index], 'App']} (подсказка : {df_google.loc[df_google.index[row_index], 'Content Rating']})")
        s = input(prompt)
        if s == 'q':
            break
        try:
            n = int(s)
        except:
            continue
        if 0 < n <= df_content_ratingd_len:
            # print(df_marks.iloc[n - 1, 0])
            df_google.loc[df_google.index[row_index], cri_col_name] = df_marks.loc[df_marks.index[n - 1], 'index']
        else:
            continue
        print(df_google.loc[df_google.index[row_index], cri_col_name])
        row_index += 1
        if row_index + 1 > df_google.shape[0]:
            break
    df_google.to_csv(file_result, index=False)

if __name__ == '__main__':
    main()