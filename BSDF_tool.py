import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import pandas as pd
import io
import os
import re
import glob
import numpy as np

def lt_folder_to_asap_scan():
    # 讓使用者選資料夾
    folder = filedialog.askdirectory(title="選擇包含 LightTools TXT 的資料夾")
    if not folder:
        return

    pattern = os.path.join(folder, "*.txt")
    txt_files = sorted(glob.glob(pattern))

    if not txt_files:
        messagebox.showwarning("找不到檔案", f"此資料夾沒有 .txt 檔：\n{folder}")
        return

    # 抓 AOI（支援負號與小數）
    aoi_regex = re.compile(r"_(-?\d+(?:\.\d+)?)deg", re.IGNORECASE)

    file_aoi_list = []
    aoi_set = set()

    for fp in txt_files:
        base = os.path.basename(fp)
        m = aoi_regex.search(base)

        if m:
            aoi = float(m.group(1))
            file_aoi_list.append((base, aoi))
            aoi_set.add(aoi)
        else:
            file_aoi_list.append((base, None))

    sorted_aois = sorted(aoi_set)

    # 讓使用者選擇儲存位置
    save_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt")],
        title="儲存 AOI 清單檔案"
    )

    if not save_path:
        return

    # 寫入檔案
    with open(save_path, "w", encoding="utf-8") as f:
        f.write("LT → ASAP AOI Summary\n")
        f.write("====================================\n")
        f.write(f"來源資料夾: {folder}\n\n")

        f.write("Unique AOI (deg):\n")
        if sorted_aois:
            for aoi in sorted_aois:
                f.write(f"{aoi}\n")
        else:
            f.write("None detected\n")

        f.write("\n------------------------------------\n")
        f.write("File → AOI Mapping\n\n")

        for filename, aoi in file_aoi_list:
            if aoi is None:
                f.write(f"{filename}  →  (AOI not detected)\n")
            else:
                f.write(f"{filename}  →  {aoi} deg\n")

    messagebox.showinfo("完成", f"AOI 清單已儲存至：\n{save_path}")
    # 讓使用者選資料夾
    # folder = filedialog.askdirectory(title="選擇包含 LightTools TXT 的資料夾")
    # if not folder:
        # return  # 使用者取消

    # 找出所有 txt
    pattern = os.path.join(folder, "*.txt")
    txt_files = sorted(glob.glob(pattern))
    if not txt_files:
        messagebox.showwarning("找不到檔案", f"此資料夾沒有 .txt 檔：\n{folder}")
        return

    # 從檔名抓 AOI：支援 _80deg, _-10deg, _12.5deg（大小寫不敏感）
    aoi_regex = re.compile(r"_(-?\d+(?:\.\d+)?)deg", re.IGNORECASE)

    found = []          # (filename, aoi_float or None)
    aoi_set = set()     # unique AOIs

    for fp in txt_files:
        base = os.path.basename(fp)
        m = aoi_regex.search(base)
        if m:
            aoi = float(m.group(1))
            found.append((base, aoi))
            aoi_set.add(aoi)
        else:
            found.append((base, None))

    # 排序輸出（數值排序）
    aoi_list = sorted(aoi_set)

    # --- 輸出到 GUI 上方文字框（當成 log）---
    text_input.delete("1.0", tk.END)
    text_input.insert(tk.END, f"[LT→ASAP 掃描資料夾]\n{folder}\n\n")
    text_input.insert(tk.END, f"共找到 {len(txt_files)} 個 TXT\n\n")

    text_input.insert(tk.END, "抓到的 AOI (deg)：\n")
    if aoi_list:
        text_input.insert(tk.END, ", ".join(str(a) for a in aoi_list) + "\n\n")
    else:
        text_input.insert(tk.END, "(沒有任何檔名符合 *_XXdeg)\n\n")

    text_input.insert(tk.END, "逐檔結果：\n")
    for base, aoi in found:
        if aoi is None:
            text_input.insert(tk.END, f" - {base}  →  (未抓到 AOI)\n")
        else:
            text_input.insert(tk.END, f" - {base}  →  AOI = {aoi} deg\n")

    # --- 同時用彈窗提示 AOI 一覽（你說要 print 出來）---
    if aoi_list:
        messagebox.showinfo("AOI 擷取完成", "抓到的 AOI (deg)：\n" + ", ".join(str(a) for a in aoi_list))
    else:
        messagebox.showwarning("AOI 擷取失敗", "未從檔名擷取到 *_XXdeg 格式的 AOI。\n請確認檔名格式。")

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

            for i in range(0, rows - 1):
                for j in range(0, cols - 1):
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
                    
                    elif df_array[i, j] < 0:
                        # 對於小於 0 的值，將其設為 0
                        df_array[i, j] = 0

            # 將內插後的值寫回 DataFrame
            df_flipped = pd.DataFrame(df_array, columns=df_flipped.columns, index=df_flipped.index)
        else:
            pass


        # 取得左右兩部分的欄位（根據欄位名稱值進行篩選）
        df_flipped.columns = df_flipped.columns.astype(float)
        
        # 物理重疊平均：若原始表格同時有 -180 與 180，取平均後存入 180 欄
        if 180.0 in df_flipped.columns and -180.0 in df_flipped.columns:
            df_flipped.loc[:, 180.0] = (df_flipped.loc[:, 180.0] + df_flipped.loc[:, -180.0]) / 2.0
            
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

def _read_lt_txt_as_matrix(txt_path: str):
    """
    讀 LightTools TXT → 回傳純數值矩陣 (rows=theta samples, cols=phi samples)

    Robust 解析策略：
    - 逐行掃描，抽出「可解析成一串浮點數」的行
    - 以「數字欄位數最多」作為矩陣欄數候選
    - 取該欄數的最長連續區段作為矩陣
    - 回傳 numpy float matrix
    """
    float_pat = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")

    numeric_rows = []  # (count, values_list)

    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue

            # 把 tab、逗號都視為分隔符；先用 regex 抓所有浮點
            nums = float_pat.findall(s)
            if len(nums) < 2:
                continue  # 太短多半不是矩陣

            try:
                vals = [float(x) for x in nums]
            except Exception:
                continue

            numeric_rows.append((len(vals), vals))

    if not numeric_rows:
        raise ValueError(f"找不到任何可解析的數值矩陣行：{os.path.basename(txt_path)}")

    # 以最多欄位數作為候選矩陣欄數
    max_cols = max(c for c, _ in numeric_rows)

    # 找「欄位數 == max_cols」的最長連續區段
    best_start = None
    best_len = 0

    cur_start = None
    cur_len = 0

    for i, (c, _) in enumerate(numeric_rows):
        if c == max_cols:
            if cur_start is None:
                cur_start = i
                cur_len = 1
            else:
                cur_len += 1
        else:
            if cur_start is not None and cur_len > best_len:
                best_start = cur_start
                best_len = cur_len
            cur_start = None
            cur_len = 0

    # 收尾
    if cur_start is not None and cur_len > best_len:
        best_start = cur_start
        best_len = cur_len

    if best_start is None or best_len < 2:
        # 如果 max_cols 太嚴格（例如某些行多了 1-2 個垃圾數字），退一步：
        # 改用「最常見欄位數」的最長連續區段
        from collections import Counter
        counts = [c for c, _ in numeric_rows]
        common_cols = Counter(counts).most_common(1)[0][0]

        best_start = None
        best_len = 0
        cur_start = None
        cur_len = 0

        for i, (c, _) in enumerate(numeric_rows):
            if c == common_cols:
                if cur_start is None:
                    cur_start = i
                    cur_len = 1
                else:
                    cur_len += 1
            else:
                if cur_start is not None and cur_len > best_len:
                    best_start = cur_start
                    best_len = cur_len
                cur_start = None
                cur_len = 0

        if cur_start is not None and cur_len > best_len:
            best_start = cur_start
            best_len = cur_len

        if best_start is None or best_len < 2:
            raise ValueError(
                f"無法定位矩陣區段：{os.path.basename(txt_path)} "
                f"(max_cols={max_cols}, common_cols={common_cols})"
            )

        cols = common_cols
    else:
        cols = max_cols

    mat_rows = []
    for k in range(best_start, best_start + best_len):
        _, vals = numeric_rows[k]
        # 保險：裁切到 cols（避免偶發多抓到尾端數字）
        mat_rows.append(vals[:cols])

    mat = np.array(mat_rows, dtype=float)

    if mat.shape[0] < 2 or mat.shape[1] < 2:
        raise ValueError(f"矩陣尺寸太小：{os.path.basename(txt_path)} -> {mat.shape}")

    return mat
    """
    讀 LightTools TXT → 回傳 (theta_count, phi_count, data_matrix)

    假設 TXT 是 tab 分隔的數值表格：
    - 有些檔第一欄可能是 theta 或「列標籤」之類；若第一欄非數值，會自動丟掉。
    - 最終只取純數值矩陣 (rows=theta samples, cols=phi samples)
    """
    # 盡量用 tab 分隔讀入
    df = pd.read_csv(txt_path, sep="\t", engine="python")

    # 丟掉可能的中文欄（你原本就有）
    if '列標籤' in df.columns:
        df = df.drop(columns=['列標籤'])

    # 嘗試把所有欄轉 float，轉不了就先丟掉那欄（常見：第一欄是 row label）
    keep_cols = []
    for c in df.columns:
        try:
            float(str(c).strip())
            keep_cols.append(c)
        except Exception:
            # 欄名非數值：不一定要丟；但通常是 row label 欄
            pass

    # 若欄名有數值，保留它們；否則就保留全部欄，再從內容挑數值
    if len(keep_cols) >= 2:
        df = df[keep_cols]

    # 內容轉 float，轉不了就變 NaN
    df = df.apply(pd.to_numeric, errors="coerce")

    # 移除全 NaN 欄/列
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")

    if df.shape[0] < 2 or df.shape[1] < 2:
        raise ValueError(f"資料矩陣太小或無法解析：{os.path.basename(txt_path)}")

    mat = df.values.astype(float)
    return mat

def _clean_matrix(mat: np.ndarray, exclude_abnormal: bool):
    """
    依你原本邏輯：
    - <0 設為 0
    - ==0 用上下左右非 0 鄰居平均補
    """
    if not exclude_abnormal:
        return mat

    a = mat.copy()
    rows, cols = a.shape

    # 先把負值設 0
    a[a < 0] = 0

    # 0 值用四向鄰居補（只用非 0）
    # 注意邊界：只處理內圈，避免 i-1 越界
    for i in range(1, rows - 1):
        for j in range(1, cols - 1):
            if a[i, j] == 0:
                neighbors = [a[i-1, j], a[i+1, j], a[i, j-1], a[i, j+1]]
                valid = [v for v in neighbors if v != 0]
                if valid:
                    a[i, j] = sum(valid) / len(valid)

    return a

def _build_theta_phi_axes(mat: np.ndarray):
    """
    依你的規格：
    THETA：由行數 N 決定，0..90 等距
    PHI：由列數 M 決定，0..360 等距（先做 0..360，不含 360；最後輸出時補 360）
    """
    n_theta, n_phi = mat.shape
    theta = np.linspace(0.0, 90.0, n_theta)        # 含 0 與 90
    phi = np.linspace(0.0, 360.0, n_phi)  # 0.. <360
    return theta, phi

def _shift_phi_270_to_0(phi: np.ndarray, mat: np.ndarray):
    """
    把 phi=270 平移成新 0：
    phi' = (phi - 270) mod 360
    平移前，若網格同時存在 0° 與 360°，先將兩者取平均以降低邊界雜訊，再剔除 360°。
    之後按 phi' 升冪排序重排欄位，並在最後補一欄 360° (= 0° 的重複)，讓最小 0 最大 360。
    """
    # 1. 預處理防呆：將物理同點的 0° 與 360° 資料取平均，再剔除尾端的 360°
    if np.isclose(phi[-1], 360.0) and np.isclose(phi[0], 0.0):
        # 將 0° 與 360° 的數值平均，並覆蓋回 0° 的欄位
        mat[:, 0] = (mat[:, 0] + mat[:, -1]) / 2.0
        # 剔除 360° 的欄位與軸座標
        phi = phi[:-1]
        mat = mat[:, :-1]

    # 2. 平移並取餘數
    phi_shift = (phi - 270.0) % 360.0
    
    # 3. 升冪排序
    order = np.argsort(phi_shift)
    phi_sorted = phi_shift[order]
    mat_sorted = mat[:, order]

    # 4. 補 360° 欄：複製 phi=0 的那一欄到最後，確保邊界閉合
    idx0 = int(np.argmin(np.abs(phi_sorted - 0.0)))
    col0 = mat_sorted[:, idx0:idx0+1]

    phi_out = np.concatenate([phi_sorted, np.array([360.0])])
    mat_out = np.concatenate([mat_sorted, col0], axis=1)
    
    return phi_out, mat_out    
def _fold_phi_to_180(phi: np.ndarray, mat: np.ndarray):
    """
    將 0~360 的矩陣，以 180 度為對稱軸進行左右平均。
    回傳：0~180 的 phi 軸與平均後的矩陣。
    """
    # 擷取 <= 180 的有效索引
    valid_idx = np.where(phi <= 180.0)[0]
    phi_180 = phi[valid_idx]
    mat_180 = np.zeros((mat.shape[0], len(phi_180)))

    for i, p in enumerate(phi_180):
        p_sym = 360.0 - p
        # 使用 np.argmin 尋找最接近對稱角度的索引，避免浮點數誤差導致找不到
        idx_sym = np.argmin(np.abs(phi - p_sym))
        
        # 左右對稱平均
        mat_180[:, i] = (mat[:, i] + mat[:, idx_sym]) / 2.0

    return phi_180, mat_180

def lt_folder_to_asap_merge():
    # 1) 選資料夾
    folder = filedialog.askdirectory(title="選擇包含 LightTools TXT 的資料夾（檔名含 *_XXdeg）")
    if not folder:
        return

    # 2) 掃 TXT
    txt_files = sorted(glob.glob(os.path.join(folder, "*.txt")))
    if not txt_files:
        messagebox.showwarning("找不到檔案", f"此資料夾沒有 .txt 檔：\n{folder}")
        return

    # 3) 擷取 AOI（*_80deg）
    aoi_regex = re.compile(r"_(-?\d+(?:\.\d+)?)deg", re.IGNORECASE)
    aoi_map = []  # (aoi_float, filepath)

    for fp in txt_files:
        base = os.path.basename(fp)
        m = aoi_regex.search(base)
        if m:
            aoi = float(m.group(1))
            aoi_map.append((aoi, fp))

    if not aoi_map:
        messagebox.showwarning("AOI 擷取失敗", "沒有任何檔名符合 *_XXdeg 的 TXT。")
        return

    # 4) 依 AOI 排序
    aoi_map.sort(key=lambda x: x[0])

    # 5) 選輸出 ASAP 檔
    save_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt")],
        title="另存合併後的 ASAP scatter 檔"
    )
    if not save_path:
        return

    # 6) 逐 AOI 讀矩陣 + 建軸 + shift phi + 對稱平均 + theta 處理
    blocks = []
    theta_ref = None
    phi_ref = None

    for aoi, fp in aoi_map:
        mat = _read_lt_txt_as_matrix(fp)
        mat = _clean_matrix(mat, exclude_abnormal=option_var.get())

        theta, phi = _build_theta_phi_axes(mat)
        
        # 轉到 0~360
        phi_out, mat_out = _shift_phi_270_to_0(phi, mat)
        
        # 將 0~360 折疊並左右平均為 0~180
        phi_out, mat_out = _fold_phi_to_180(phi_out, mat_out)

        # 依原設定：Theta 順序維持，僅矩陣列顛倒
        theta_out = theta 
        mat_out = mat_out[::-1, :]

        # 檢查軸一致
        if theta_ref is None:
            theta_ref = theta_out
            phi_ref = phi_out
        else:
            if len(theta_out) != len(theta_ref) or len(phi_out) != len(phi_ref):
                raise ValueError(
                    "不同 AOI 的 TXT 矩陣尺寸不一致，無法合併成同一個 ASAP scatter 檔。\n"
                    f"目前檔案：{os.path.basename(fp)}"
                )

        blocks.append((aoi, mat_out))

    # 7) 寫 ASAP 格式
    # 你給的格式：
    # DEG
    # <theta list> !! THETA
    # <phi list>   !! PHI
    # ! 0 DEGREES
    # 0
    # matrix...
    #
    # 註：theta_ref 已是 90->0，符合你「Theta順序要顛倒」
    def _fmt_list(arr):
        # 盡量輸出整潔：整數就不帶小數
        out = []
        for v in arr:
            if abs(v - round(v)) < 1e-9:
                out.append(str(int(round(v))))
            else:
                out.append(f"{v:.6g}")
        return " ".join(out)

    with open(save_path, "w", encoding="utf-8") as f:
        f.write("DEG\n")
        f.write(_fmt_list(theta_ref) + "  !! THETA\n")
        f.write(_fmt_list(phi_ref) + "  !! PHI\n\n")

        for aoi, mat_out in blocks:
            # block header
            # 依你的示例：! 0 DEGREES + 下一行 0
            if abs(aoi - round(aoi)) < 1e-9:
                aoi_str = str(int(round(aoi)))
            else:
                aoi_str = f"{aoi:.6g}"

            f.write(f"! {aoi_str} DEGREES\n")
            f.write(f"{aoi_str}\n")

            # matrix：每列一行，tab 分隔（ASAP 常見可接受空白或 tab；tab 較安全）
            for r in range(mat_out.shape[0]):
                f.write("\t".join(f"{x:.6e}" for x in mat_out[r, :]) + "\n")
            f.write("\n")
        # 8) 將輸出的 ASAP 檔內容顯示在上方文字框（print 出來）
    try:
        with open(save_path, "r", encoding="utf-8", errors="ignore") as rf:
            asap_text = rf.read()
        text_input.delete("1.0", tk.END)
        text_input.insert(tk.END, asap_text)
    except Exception as e:
        messagebox.showwarning("提示", f"ASAP 檔已輸出，但無法顯示內容：{e}")


    messagebox.showinfo("完成", f"已合併輸出 ASAP scatter 檔：\n{save_path}")


# 建立 GUI 視窗
root = tk.Tk()
root.title("TASA LightTools BSDF 數據轉置工具")
root.geometry("1000x600")

# 貼上區域
tk.Label(root, text="請貼上原始表格資料：").pack()
text_input = scrolledtext.ScrolledText(root, height=15)
text_input.pack(fill=tk.BOTH, padx=10, pady=5, expand=True)

# 建立底部控制區（同一行）
bottom_frame = tk.Frame(root)
bottom_frame.pack(fill=tk.X, pady=10)

# 左側佔位（讓中間區真正置中）
left_spacer = tk.Frame(bottom_frame)
left_spacer.pack(side=tk.LEFT, expand=True)

left_spacer2 = tk.Frame(bottom_frame)
left_spacer2.pack(side=tk.LEFT, expand=True)

# 中間區（轉 LT + 排除異常）
center_frame = tk.Frame(bottom_frame)
center_frame.pack(side=tk.LEFT)

convert_btn = tk.Button(
    center_frame,
    text="🔁 轉換並儲存成 LightTools 檔案",
    command=process_data,
    height=2,
    width=30
)
convert_btn.pack(side=tk.LEFT, padx=10)

option_var = tk.BooleanVar(value=True)
option_check = tk.Checkbutton(
    center_frame,
    text="排除異常值",
    variable=option_var
)
option_check.pack(side=tk.LEFT, padx=10)

# 右側佔位（把 ASAP 推到最右）
right_spacer = tk.Frame(bottom_frame)
right_spacer.pack(side=tk.LEFT, expand=True)

# ASAP 按鈕（同一行最右）
asap_convert_btn = tk.Button(
    bottom_frame,
    text="🔁 轉換 LT 成 ASAP 資料",
    command=lt_folder_to_asap_merge,
    height=2,
    width=20
)
asap_convert_btn.pack(side=tk.RIGHT, padx=10)


# 啟動 GUI
root.mainloop()
