# Raspberry Pi 5 實戰教學 (rpi_tutorial)

本專案包含針對 Raspberry Pi 5（Bookworm 作業系統）最佳化的硬體控制與電腦視覺 Demo 程式碼，涵蓋相機、人臉辨識、LCD 顯示器以及 GPIO 控制等基礎應用。

---

## 環境準備與系統設定

在執行本專案的程式碼之前，請先確認您的 Raspberry Pi 5 已完成以下基本設定。

### 1. 更新系統套件清單

建議先將系統套件更新至最新版本，以避免安裝相依套件時發生錯誤。

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. 開啟 I2C 介面（供 LCD 螢幕使用）

1602 LCD 模組會透過 I2C 傳輸，因此需先啟用 Raspberry Pi 的 I2C 功能。

請輸入以下指令進入設定介面：

```bash
sudo raspi-config
```

接著依序進入：

```text
Interface Options -> I2C -> Yes
```

啟用完成後重新開機：

```bash
sudo reboot
```

---

# 執行教學

## 1. GPIO LED 閃爍（C++ + libgpiod）

由於 Raspberry Pi 5 採用了全新的 RP1 南橋晶片架構，GPIO 控制方式與舊版 Raspberry Pi 有所不同，因此建議使用官方推薦的 `libgpiod v2` 函式庫進行控制。

本範例展示如何使用 C++ 撰寫 LED 閃爍程式，控制實體 GPIO 接腳輸出高低電位。

### 環境安裝

編譯程式前，請先安裝 `libgpiod` 開發套件：

```bash
sudo apt install libgpiod-dev -y
```

### 編譯程式

使用 `g++` 編譯並連結 `gpiodcxx` 函式庫：

```bash
g++ led_blink.cpp -o led_blink -lgpiodcxx
```

### 硬體接線

請將 LED 與電阻依下列方式接線：

* LED 正極（長腳）→ 串聯 220Ω ~ 470Ω 電阻 → GPIO 23（Pin 16）
* LED 負極（短腳）→ GND

### 執行程式

```bash
./led_blink
```

---

## 2. 1602 LCD 螢幕控制（Python + I2C）

本程式展示如何使用 I2C 擴充板（PCF8574）控制 1602 LCD 顯示器，並於螢幕上輸出指定文字訊息。

### 環境安裝

請安裝 LCD 所需 Python 套件：

```bash
pip3 install RPLCD smbus2
```

### 硬體接線

請依照下列方式將 LCD I2C 模組接至 Raspberry Pi：

* **GND** → Raspberry Pi GND
* **VCC** → Raspberry Pi 5V
* **SDA** → Raspberry Pi Pin 3（SDA）
* **SCL** → Raspberry Pi Pin 5（SCL）

### 執行程式

```bash
python3 lcd_demo.py
```

### 常見問題排除

若 LCD 螢幕未正常顯示，請檢查以下兩點：

1. 使用十字起子微調 LCD 背後的藍色對比度旋鈕。
2. 使用以下指令確認 I2C 裝置位址是否成功偵測到（通常為 `0x27`）：

```bash
i2cdetect -y 1
```

---

## 3. 人臉偵測（Python + Picamera2）

本程式展示如何使用 Raspberry Pi 5 原生支援的 Picamera2 相機介面擷取即時畫面，並透過 OpenCV 的 Haar Cascade 分類器進行人臉辨識。

### 環境安裝

請先安裝 OpenCV：

```bash
sudo apt install python3-opencv -y
```

### 下載特徵模型檔

本程式需使用 OpenCV 官方提供的人臉特徵模型 `haarcascade_frontalface_default.xml`，請於程式所在目錄下載：

```bash
wget https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml
```

### 執行程式

> 注意：此程式需在有連接 HDMI 螢幕的桌面環境，或透過 VNC 遠端桌面執行，否則無法顯示即時影像視窗。

```bash
python3 face_demo.py
```
