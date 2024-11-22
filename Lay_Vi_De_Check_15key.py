from mnemonic import Mnemonic
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from tkinter import Tk, Button, Label, Text, messagebox
import threading
import queue

# Biến toàn cục để kiểm soát việc kiểm tra
stop_flag = False  # Dùng để tạm dừng việc kiểm tra

# Hàm tạo cụm từ gợi nhớ và ví con
def generate_wallets():
    mnemo = Mnemonic("english")
    mnemonic = mnemo.generate(strength=160)  # Tạo cụm từ gợi nhớ 15 từ
    seed = Bip39SeedGenerator(mnemonic).Generate()
    bip44_mst = Bip44.FromSeed(seed, Bip44Coins.ETHEREUM)  # Ethereum coin (BEP-20 sử dụng cùng chuẩn)
    
    wallets = []
    for i in range(10):  # Tạo 10 ví con
        bip44_acc = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i)
        address = bip44_acc.PublicKey().ToAddress()
        wallets.append(address)
    return mnemonic, wallets

# Hàm lưu log vào file (bổ sung vào file thay vì ghi đè)
def save_log_to_file(log_text):
    with open("log.txt", "a") as f:  # Mở file ở chế độ append (thêm vào cuối file)
        f.write(log_text.get("1.0", "end"))

# Hàm kiểm tra liên tục với đa luồng
def generate_wallets_in_thread(log_queue):
    global stop_flag
    while not stop_flag:
        mnemonic, wallets = generate_wallets()
        # In ra cụm từ gợi nhớ và các ví con
        log_message = f"Mnemonic: {mnemonic}\n"
        log_message += "Generated Wallets:\n"
        for addr in wallets:
            log_message += f"  {addr}\n"
        log_message += "-" * 50 + "\n"
        log_queue.put(log_message)  # Gửi log vào queue để xử lý trên main thread

# Hàm bắt đầu kiểm tra
def start_generating(log_text, log_queue):
    global stop_flag
    stop_flag = False  # Đặt flag stop về False khi bắt đầu tạo ví
    # Tạo thread để sinh cụm từ gợi nhớ và ví liên tục
    generate_thread = threading.Thread(target=generate_wallets_in_thread, args=(log_queue,))
    generate_thread.daemon = True  # Thread này sẽ kết thúc khi main thread kết thúc
    generate_thread.start()

# Hàm tạm dừng kiểm tra
def stop_generating():
    global stop_flag
    stop_flag = True  # Đặt flag stop về True để dừng tạo ví

# Hàm xử lý log từ queue
def process_log_queue(log_text, log_queue):
    try:
        while True:
            log_message = log_queue.get_nowait()  # Lấy log từ queue
            log_text.insert("end", log_message)
            log_text.yview("end")  # Tự động cuộn xuống cuối
    except queue.Empty:
        pass

# Hàm xử lý khi đóng cửa sổ và lưu tiến trình
def on_close(window):
    global stop_flag
    if not stop_flag:  # Nếu chưa tạm dừng thì cảnh báo người dùng
        if messagebox.askokcancel("Warning", "Bạn tắt thì dữ liệu sẽ không được lưu , hãy lưu trước khi tắt , Bấm hủy để dừng việc tắt phần mềm "):
            stop_generating()
            window.quit()  # Đóng cửa sổ
    else:
        window.quit()  # Nếu đã tạm dừng thì thoát bình thường

# Thiết lập giao diện người dùng với Tkinter
def setup_gui():
    window = Tk()
    window.title("Lưu ý , bấm cập nhật rồi thì phải tắt đi bật lại mới được chạy tiếp")

    # Cập nhật kích thước và màu nền để có dark mode
    window.geometry("1100x600")  # Phóng to lên 30%
    window.configure(bg="#2E2E2E")  # Màu nền dark mode

    # Hiển thị số lần kiểm tra từ "Mnemonic"
    counter_label = Label(window, text="Mnemonics: 0", fg="white", bg="#2E2E2E", font=("Arial", 14))
    counter_label.pack(pady=10)

    # Text box để hiển thị log
    log_text = Text(window, height=20, width=120, bg="#3A3A3A", fg="white", font=("Arial", 12))
    log_text.pack(pady=10)

    # Nút Bắt đầu
    start_button = Button(window, text="Bắt đầu", command=lambda: start_generating(log_text, log_queue), bg="#4CAF50", fg="white", font=("Arial", 14))
    start_button.pack(pady=10)

    # Nút Dừng
    stop_button = Button(window, text="Tạm dừng", command=stop_generating, bg="#F44336", fg="white", font=("Arial", 14))
    stop_button.pack(pady=10)

    # Nút Lưu log
    save_button = Button(window, text="Cập nhật vào file", command=lambda: save_log_to_file(log_text), bg="#2196F3", fg="white", font=("Arial", 14))
    save_button.pack(pady=10)

    # Queue để giao tiếp giữa các thread
    log_queue = queue.Queue()

    # Kiểm tra log và cập nhật giao diện
    def update_gui():
        process_log_queue(log_text, log_queue)
        # Đếm số lần xuất hiện từ "Mnemonic"
        mnemonic_count = log_text.get("1.0", "end").count("Mnemonic")
        counter_label.config(text=f"Tổng ví hiện lấy được: {mnemonic_count}")
        window.after(100, update_gui)  # Cập nhật mỗi 100ms

    update_gui()

    # Gọi hàm on_close() khi cửa sổ được đóng
    window.protocol("WM_DELETE_WINDOW", lambda: on_close(window))
    window.mainloop()

if __name__ == "__main__":
    setup_gui()
