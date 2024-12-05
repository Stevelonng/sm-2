# main.py

from db_manager import DatabaseManager
from anki_sm2 import AnkiStyleSM2
from datetime import datetime


def format_interval(interval):
    if interval < 1:
        minutes = int(interval * 24 * 60)
        return f"{minutes}分钟"
    else:
        days = int(interval)
        return f"{days}天"


def show_next_review(next_review, interval):
    if interval < 1:
        print(f"下次复习时间: {format_interval(interval)}后 ({next_review.strftime('%H:%M')})")
    else:
        print(f"下次复习时间: {format_interval(interval)}后 ({next_review.strftime('%Y-%m-%d')})")


class FlashcardApp:
    def __init__(self):
        self.db = DatabaseManager()
        self.sm2 = AnkiStyleSM2()

    def add_new_card(self, front, back):
        return self.db.add_card(front, back)

    def review_card(self, card_id, quality):
        current_state = self.db.get_card_state(card_id)
        new_state = self.sm2.review_card(current_state, quality)
        new_state['quality'] = quality
        self.db.add_review_record(card_id, new_state)
        return new_state

    def get_cards_to_review(self):
        return self.db.get_due_cards()

    def show_card_history(self, card_id):
        try:
            card_id = int(card_id)
            history = self.db.get_review_history(card_id)

            if history:
                print(f"\n卡片 {card_id} 的复习历史:")
                print("-" * 60)
                print("日期\t\t评分\t简易度\t间隔\t\t下次复习")
                print("-" * 60)

                for record in history:
                    review_date = record[0]
                    next_review = record[4]
                    interval_str = format_interval(record[3])
                    print(f"{review_date}\t{record[1]}\t{record[2]:.2f}\t{interval_str}\t{next_review}")
            else:
                print(f"\n提示：卡片 {card_id} 不存在或尚未有复习记录")
        except ValueError:
            print("\n错误：请输入有效的卡片ID（数字）")


def get_quality_score():
    print("\n请为这张卡片评分:")
    print("0 - 完全不记得 (重来)")
    print("1 - 记得但很困难 (困难)")
    print("2 - 记得还可以 (良好)")
    print("3 - 记得很轻松 (简单)")

    while True:
        try:
            quality = int(input("\n你的评分 (0-3): "))
            if 0 <= quality <= 3:
                return quality
            print("请输入0-3之间的数字!")
        except ValueError:
            print("请输入有效数字!")


def main():
    app = FlashcardApp()

    while True:
        print("\n=== Anki风格闪卡系统 ===")
        print("1. 添加新卡片")
        print("2. 开始复习")
        print("3. 查看卡片历史")
        print("4. 退出")

        choice = input("\n请选择操作 (1-4): ")

        if choice == '1':
            front = input("请输入卡片正面内容: ")
            back = input("请输入卡片背面内容: ")
            card_id = app.add_new_card(front, back)
            print(f"成功添加卡片 (ID: {card_id})")

        elif choice == '2':
            due_cards = app.get_cards_to_review()
            if not due_cards:
                print("没有需要复习的卡片!")
                continue

            for card in due_cards:
                print(f"\n正面: {card[1]}")
                input("按回车查看答案...")
                print(f"背面: {card[2]}")

                quality = get_quality_score()
                new_state = app.review_card(card[0], quality)
                show_next_review(new_state['next_review'], new_state['interval'])

        elif choice == '3':
            card_id = input("请输入卡片ID: ")
            app.show_card_history(card_id)

        elif choice == '4':
            print("感谢使用!")
            break

        else:
            print("无效选择,请重试!")


if __name__ == "__main__":
    main()