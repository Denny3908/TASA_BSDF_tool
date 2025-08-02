import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import pandas as pd
import io
import os

def process_data():
    raw_text = text_input.get("1.0", tk.END).strip()
    if not raw_text:
        messagebox.showwarning("警告", "請先貼上表格資料！")
        return

    try:
        df = pd.read_csv(io.StringIO(raw_text), sep="\t")

        if '列標籤' in df.columns:
            df = df.drop(columns=['列標籤'])

        # 將每一欄反轉（即將每列上下翻轉），再轉置矩陣（行列互換）
        df.iloc[0] = df.iloc[0][0]
        df_flipped = df.iloc[::-1]
        row_count = df_flipped.shape[0]  # 新矩陣列數
        col_count = df_flipped.shape[1]  # 新矩陣行數

        if option_var.get():
            # 對 df_final 中的 0 做四向平均內插（只用非 0 鄰居）
            df_array = df_flipped.values.astype(float)
            rows, cols = df_array.shape

            for i in range(1, rows - 1):
                for j in range(1, cols - 1):
                    if df_array[i, j] == 0:
                        neighbors = [
                            df_array[i-1, j],  # 上
                            df_array[i+1, j],  # 下
                            df_array[i, j-1],  # 左
                            df_array[i, j+1]   # 右
                        ]
                        valid_neighbors = [val for val in neighbors if val != 0]
                        if valid_neighbors:
                            df_array[i, j] = sum(valid_neighbors) / len(valid_neighbors)

            # 將內插後的值寫回 DataFrame
            df_flipped = pd.DataFrame(df_array, columns=df_flipped.columns, index=df_flipped.index)
        else:
            pass


        # 取得左右兩部分的欄位（根據欄位名稱值進行篩選）
        df_flipped.columns = df_flipped.columns.astype(float)
        left = df_flipped.loc[:, df_flipped.columns >= -90]
        middle = df_flipped.loc[:, (df_flipped.columns > -180) & (df_flipped.columns < -90)]
        right = left.iloc[:,0]
        df_final = pd.concat([left, middle, right], axis=1)
        
        
        # 選擇輸出檔案路徑
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            title="儲存轉換後的檔案"
        )
        if not filepath:
            return  # 使用者取消

        with open(filepath, 'w', encoding='utf-8') as f:
            # 寫入前置資訊
            f.write("#            \tLongDim\tLatDim\tLongMin\tLatMin\tLongMax\tLatMax\n")
            f.write(f"SphereMesh:\t{col_count}\t{row_count}\t0\t0\t360\t90\n")

            # 寫入轉換後資料
            for _, row in df_final.iterrows():
                f.write('\t'.join(f"{x:.5f}" for x in row) + '\n')

        messagebox.showinfo("完成", f"已儲存至：{filepath}")

    except Exception as e:
        messagebox.showerror("錯誤", f"處理失敗：{e}")

# 建立 GUI 視窗
root = tk.Tk()
root.title("TASA LightTools BSDF 數據轉置工具")
root.geometry("1000x600")

# 貼上區域
tk.Label(root, text="請貼上原始表格資料：").pack()
text_input = scrolledtext.ScrolledText(root, height=15)
text_input.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

# 建立底部控制區（水平排列按鈕與勾選框）
bottom_frame = tk.Frame(root)
bottom_frame.pack(pady=10)

# 轉換按鈕
convert_btn = tk.Button(bottom_frame, text="🔁 轉換並儲存至檔案", command=process_data, height=2, width=25)
convert_btn.pack(side=tk.LEFT, padx=10)

# 勾選框變數
option_var = tk.BooleanVar(value=True)

# 勾選框
option_check = tk.Checkbutton(
    bottom_frame,
    text="排除異常值",
    variable=option_var
    # TODO: 在這裡處理勾選與否的功能
)
option_check.pack(side=tk.LEFT)

# 啟動 GUI
root.mainloop()
