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

# 執行按鈕
tk.Button(root, text="🔁 轉換並儲存至檔案", command=process_data, height=2, width=25).pack(pady=10)

# 啟動 GUI
root.mainloop()
