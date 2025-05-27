import tkinter as tk
from tkinter import messagebox, simpledialog
import time
import winsound
import threading

# --- 設定ダイアログクラス ---
class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, initial_work_time_mins, initial_break_time_mins):
        super().__init__(parent)
        self.transient(parent) # 親ウィンドウの上に表示されるようにする
        self.grab_set() # 親ウィンドウの操作を無効にする（モーダルダイアログ）
        self.title("設定")
        self.geometry("300x180")
        self.resizable(False, False)

        self.result_work_time_mins = initial_work_time_mins
        self.result_break_time_mins = initial_break_time_mins

        # 作業時間設定
        tk.Label(self, text="作業時間 (分):", font=("Helvetica", 12)).pack(pady=5)
        self.work_time_entry = tk.Entry(self, width=10, font=("Helvetica", 12))
        self.work_time_entry.insert(0, str(initial_work_time_mins))
        self.work_time_entry.pack(pady=2)

        # 休憩時間設定
        tk.Label(self, text="休憩時間 (分):", font=("Helvetica", 12)).pack(pady=5)
        self.break_time_entry = tk.Entry(self, width=10, font=("Helvetica", 12))
        self.break_time_entry.insert(0, str(initial_break_time_mins))
        self.break_time_entry.pack(pady=2)

        # 保存ボタン
        tk.Button(self, text="保存", command=self.save_settings, font=("Helvetica", 12)).pack(pady=10)

        self.protocol("WM_DELETE_WINDOW", self.on_closing) # ウィンドウ閉じるときの処理

        self.parent = parent
        self.wait_window(self) # ダイアログが閉じるまで待機

    def save_settings(self):
        try:
            work_mins = int(self.work_time_entry.get())
            break_mins = int(self.break_time_entry.get())

            if work_mins <= 0 or break_mins <= 0:
                messagebox.showerror("入力エラー", "時間は1分以上の整数で入力してください。", parent=self)
                return

            self.result_work_time_mins = work_mins
            self.result_break_time_mins = break_mins
            self.destroy() # ダイアログを閉じる

        except ValueError:
            messagebox.showerror("入力エラー", "時間を正しく入力してください（整数）。", parent=self)

    def on_closing(self):
        # ウィンドウを閉じるボタンが押された場合も、現在の値を結果として保持して閉じる
        self.destroy()


# --- ポモドーロタイマークラス ---
class PomodoroTimer:
    def __init__(self, master):
        self.master = master
        master.title("ポモドーロタイマー")
        master.geometry("400x300") # ウィンドウサイズを少し大きくする
        master.resizable(False, False)

        # デフォルトの設定時間 (分)
        self.default_work_time_mins = 25
        self.default_break_time_mins = 5

        # 現在の設定時間 (秒単位)
        self.work_time = self.default_work_time_mins * 60
        self.break_time = self.default_break_time_mins * 60

        self.current_time = 0
        self.running = False
        self.is_work_phase = True # 現在が作業フェーズか休憩フェーズか

        # ウィジェットの作成
        self.label_phase = tk.Label(master, text="準備完了", font=("Helvetica", 20, "bold"), fg="blue")
        self.label_phase.pack(pady=10)

        self.label_timer = tk.Label(master, text="00:00", font=("Helvetica", 48, "bold"), fg="green")
        self.label_timer.pack(pady=10)

        # ボタンフレーム
        self.button_frame = tk.Frame(master)
        self.button_frame.pack(pady=10)

        self.btn_start_work = tk.Button(self.button_frame, text="作業開始", command=self.start_work_timer, font=("Helvetica", 12))
        self.btn_start_work.pack(side=tk.LEFT, padx=5)

        self.btn_start_break = tk.Button(self.button_frame, text="休憩開始", command=self.start_break_timer, font=("Helvetica", 12))
        self.btn_start_break.pack(side=tk.LEFT, padx=5)
        self.btn_start_break["state"] = "disabled"

        self.btn_pause = tk.Button(self.button_frame, text="一時停止", command=self.pause_timer, font=("Helvetica", 12), state="disabled")
        self.btn_pause.pack(side=tk.LEFT, padx=5)

        self.btn_reset = tk.Button(self.button_frame, text="リセット", command=self.reset_timer, font=("Helvetica", 12), state="disabled")
        self.btn_reset.pack(side=tk.LEFT, padx=5)

        # 設定ボタン
        self.btn_settings = tk.Button(master, text="設定", command=self.open_settings, font=("Helvetica", 12))
        self.btn_settings.pack(pady=10)

        self.update_timer_display(self.work_time) # 初期表示は設定された作業時間

    def update_timer_display(self, seconds):
        """残り時間を表示を更新する"""
        mins, secs = divmod(int(seconds), 60)
        time_str = f"{mins:02d}:{secs:02d}"
        self.label_timer.config(text=time_str)

    def start_timer(self):
        """タイマーのカウントダウンを開始する"""
        if self.running:
            self.current_time -= 1
            self.update_timer_display(self.current_time)

            if self.current_time <= 0:
                self.running = False
                self.play_sound()
                if self.is_work_phase:
                    messagebox.showinfo("時間終了", f"{self.default_work_time_mins}分の作業時間が終了しました！休憩しましょう。")
                    self.label_phase.config(text="休憩準備完了", fg="green")
                    self.btn_start_break["state"] = "normal"
                    self.btn_start_work["state"] = "disabled"
                else:
                    messagebox.showinfo("時間終了", f"{self.default_break_time_mins}分の休憩時間が終了しました！作業に戻りましょう。")
                    self.label_phase.config(text="作業準備完了", fg="blue")
                    self.btn_start_work["state"] = "normal"
                    self.btn_start_break["state"] = "disabled"

                self.btn_pause["state"] = "disabled"
                self.btn_reset["state"] = "normal"
                self.btn_settings["state"] = "normal" # 設定ボタンを有効化
            else:
                self.master.after(1000, self.start_timer) # 1秒後に再度呼び出す

    def start_work_timer(self):
        """設定された作業時間タイマーを開始する"""
        if not self.running:
            self.current_time = self.work_time
            self.is_work_phase = True
            self.running = True
            self.label_phase.config(text="作業中", fg="red")
            self.update_timer_display(self.current_time)
            self.start_timer()
            self.enable_buttons_on_start()

    def start_break_timer(self):
        """設定された休憩時間タイマーを開始する"""
        if not self.running:
            self.current_time = self.break_time
            self.is_work_phase = False
            self.running = True
            self.label_phase.config(text="休憩中", fg="darkgreen")
            self.update_timer_display(self.current_time)
            self.start_timer()
            self.enable_buttons_on_start()

    def pause_timer(self):
        """タイマーを一時停止/再開する"""
        if self.running:
            self.running = False
            self.btn_pause.config(text="再開")
            self.btn_settings["state"] = "normal" # 一時停止中は設定変更可能に
        else:
            self.running = True
            self.btn_pause.config(text="一時停止")
            self.btn_settings["state"] = "disabled" # 再開中は設定変更不可に
            self.start_timer()

    def reset_timer(self):
        """タイマーをリセットする"""
        self.running = False
        # 設定された作業時間でリセット
        self.current_time = self.work_time
        self.is_work_phase = True
        self.update_timer_display(self.current_time)
        self.label_phase.config(text="準備完了", fg="blue")
        self.btn_start_work["state"] = "normal"
        self.btn_start_break["state"] = "disabled"
        self.btn_pause.config(text="一時停止", state="disabled")
        self.btn_reset["state"] = "disabled"
        self.btn_settings["state"] = "normal" # リセット後は設定変更可能に

    def enable_buttons_on_start(self):
        """タイマー開始時のボタン状態を設定"""
        self.btn_start_work["state"] = "disabled"
        self.btn_start_break["state"] = "disabled"
        self.btn_pause["state"] = "normal"
        self.btn_reset["state"] = "normal"
        self.btn_settings["state"] = "disabled" # タイマー実行中は設定変更不可に

    def play_sound(self):
        """時間終了時にビープ音を鳴らす"""
        for _ in range(3):
            winsound.Beep(2000, 300)
            time.sleep(0.1)
            winsound.Beep(1000, 300)
            time.sleep(0.1)

    def open_settings(self):
        """設定ダイアログを開き、設定を更新する"""
        # 現在設定されている分数を渡す
        settings_dialog = SettingsDialog(
            self.master,
            self.work_time // 60,
            self.break_time // 60
        )
        # ダイアログが閉じたら、結果を取得
        new_work_time_mins = settings_dialog.result_work_time_mins
        new_break_time_mins = settings_dialog.result_break_time_mins

        if (new_work_time_mins != (self.work_time // 60) or
            new_break_time_mins != (self.break_time // 60)):
            # 設定が変更された場合のみ更新
            self.default_work_time_mins = new_work_time_mins
            self.default_break_time_mins = new_break_time_mins
            self.work_time = new_work_time_mins * 60
            self.break_time = new_break_time_mins * 60
            messagebox.showinfo("設定完了", "新しい設定が適用されました。")
            self.reset_timer() # 設定変更後はタイマーをリセットして初期状態に戻す

# アプリケーションの実行
if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()