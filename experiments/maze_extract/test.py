"""
靜態影像球位置測試
用法：
  python3 test_ball.py --ref empty.jpg --balls ball1.jpg ball2.jpg ball3.jpg -d
"""
import argparse
import sys
import cv2
from maze_extract import MazeGraphExtractor
from ball_detector import BallDetector


def main():
    parser = argparse.ArgumentParser(description="Ball Position Tester")
    parser.add_argument("--ref",   required=True,        help="空迷宮圖片路徑")
    parser.add_argument("--balls", required=True, nargs="+", help="含球的圖片路徑（可多張）")
    parser.add_argument("-d", "--debug", action="store_true", help="開啟除錯視窗")
    args = parser.parse_args()

    extractor = MazeGraphExtractor(maze_size=9, wall_threshold=0.333, debug=False)
    detector  = BallDetector(maze_size=9, debug=args.debug)

    # ── Step 1：載入空迷宮，透視校正後設為背景參考 ───────────────────────────
    ref_frame = cv2.imread(args.ref)
    if ref_frame is None:
        print(f"❌ 找不到參考圖片：{args.ref}")
        sys.exit(1)

    warped_ref, _ = extractor.process(ref_frame)
    if warped_ref is None:
        print("❌ 參考圖片無法找到定位點，請確認綠色標記可見")
        sys.exit(1)

    detector.set_reference(warped_ref)
    print(f"✅ 背景參考設定完成：{args.ref}")
    # ────────────────────────────────────────────────────────────────────────

    # ── Step 2：逐張處理球的圖片 ─────────────────────────────────────────────
    for path in args.balls:
        print(f"\n📷 處理：{path}")
        frame = cv2.imread(path)
        if frame is None:
            print(f"  ❌ 找不到圖片，跳過")
            continue

        warped_ball, _ = extractor.process(frame)
        if warped_ball is None:
            print(f"  ❌ 無法找到定位點，跳過")
            continue

        pos = detector.find_ball(warped_ball)
        print(f"  球的位置：{pos}")

        if args.debug:
            cv2.imshow(f"Warped: {path}", warped_ball)
            cv2.waitKey(0)
    # ────────────────────────────────────────────────────────────────────────

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()