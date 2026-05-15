#include <gpiod.hpp> // libgpiod 的 C++ 標頭檔，提供物件導向的硬體控制介面
#include <iostream> // 標準輸入輸出 (cout, cerr)
#include <chrono> // 時間庫，用於定義「秒」、「毫秒」等時間單位
#include <thread> // 執行緒庫，提供 sleep 功能

using namespace std;

int main() {
    const int PIN = 23; // 定義我們要控制的 GPIO 編號
    const string CHIP_NAME = "/dev/gpiochip0"; // 定義硬體設備路徑，/dev/ 代表設備資料夾

    try {
        // 1. 開啟 GPIO 控制晶片
        gpiod::chip chip(CHIP_NAME);

        // 2. 準備與發送接腳請求 (C++ 專屬的 Builder Pattern 寫法)
        auto request = chip.prepare_request()
            .set_consumer("Blink_Program")
            .add_line_settings(
                PIN,
                gpiod::line_settings()
                    .set_direction(gpiod::line::direction::OUTPUT)
                    .set_output_value(gpiod::line::value::INACTIVE)
            )
            .do_request(); // 最後執行請求，並回傳 request 物件

        cout << "libgpiod v2 成功啟動！LED 開始閃爍... (按 Ctrl+C 結束)" << endl;

        // 3. 進入閃爍迴圈
        while(true) {
            request.set_value(PIN, gpiod::line::value::ACTIVE);   // 寫入高電位 (亮)
            this_thread::sleep_for(chrono::seconds(1));           // 延遲 1 秒

            request.set_value(PIN, gpiod::line::value::INACTIVE); // 寫入低電位 (暗)
            this_thread::sleep_for(chrono::seconds(1));           // 延遲 1 秒
        }

    } catch (const exception& e) {
        cerr << "[錯誤] 發生例外狀況: " << e.what() << endl;
        return -1;
    }

    return 0;
}