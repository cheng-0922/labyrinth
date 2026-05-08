from RPLCD.i2c import CharLCD
import time

# 根據你的 i2cdetect 結果修改位址 (例如 0x27)
# cols=16 代表 1602 螢幕
lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1,
              cols=16, rows=2, dotsize=8)

try:
    lcd.clear()
    lcd.write_string('Hello Pi 5!')
    lcd.cursor_pos = (1, 0) # 移動到第二列第 0 格
    lcd.write_string('I2C is Working!')

    while True:
        time.sleep(1)

except KeyboardInterrupt:
    lcd.clear()
    print("程式結束")