import sqlite3
from datetime import datetime


def adapt_datetime(dt):
    """Convert datetime to string for SQLite storage"""
    return dt.isoformat()


def convert_datetime(bytes_val):
    """Convert SQLite datetime string back to Python datetime"""
    try:
        return datetime.fromisoformat(bytes_val.decode())
    except (ValueError, AttributeError):
        return None


def view_all_cards(db_path="flashcards.db"):
    """View all cards and their latest review status with proper timestamp handling"""
    # Register the datetime converter
    sqlite3.register_adapter(datetime, adapt_datetime)
    sqlite3.register_converter("timestamp", convert_datetime)

    conn = sqlite3.connect(
        db_path,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n=== 闪卡系统数据概览 ===")
    print("-" * 100)
    print(f"{'ID':<4} {'创建时间':<19} {'最近复习':<19} {'复习次数':<8} {'正面内容':<20} {'背面内容':<20}")
    print("-" * 100)

    cursor.execute('''
        SELECT 
            c.id,
            c.created_at,
            c.front_content,
            c.back_content,
            MAX(rh.review_date) as last_review,
            COUNT(rh.id) as review_count
        FROM cards c
        LEFT JOIN review_history rh ON c.id = rh.card_id
        GROUP BY c.id
        ORDER BY c.id
    ''')

    cards = cursor.fetchall()
    for card in cards:
        created_at = card[1]
        if isinstance(created_at, datetime):
            created_at = created_at.strftime('%Y-%m-%d %H:%M')

        last_review = card[4]
        if isinstance(last_review, datetime):
            last_review = last_review.strftime('%Y-%m-%d %H:%M')
        else:
            last_review = '未复习'

        print(f"{card[0]:<4} "
              f"{created_at:<19} "
              f"{last_review:<19} "
              f"{card[5]:<8} "
              f"{card[2][:20]:<20} "
              f"{card[3][:20]:<20}")

    # Get additional statistics
    cursor.execute('SELECT COUNT(*) FROM cards')
    total_cards = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM review_history')
    total_reviews = cursor.fetchone()[0]

    print("\n=== 统计信息 ===")
    print(f"卡片总数: {total_cards}")
    print(f"总复习次数: {total_reviews}")
    if total_cards > 0:
        print(f"平均每张卡片复习次数: {total_reviews / total_cards:.1f}")

    conn.close()


def view_card_history(card_id, db_path="flashcards.db"):
    """View detailed history for a specific card with proper timestamp handling"""
    sqlite3.register_adapter(datetime, adapt_datetime)
    sqlite3.register_converter("timestamp", convert_datetime)

    conn = sqlite3.connect(
        db_path,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    cursor = conn.cursor()

    cursor.execute('''
        SELECT front_content, back_content, created_at,
               (SELECT COUNT(*) FROM review_history WHERE card_id = ?) as review_count
        FROM cards 
        WHERE id = ?
    ''', (card_id, card_id))
    card = cursor.fetchone()

    if not card:
        print(f"\n未找到ID为 {card_id} 的卡片")
        return

    print(f"\n=== 卡片详情 (ID: {card_id}) ===")
    print(f"正面内容: {card[0]}")
    print(f"背面内容: {card[1]}")
    print(f"创建时间: {card[2].strftime('%Y-%m-%d %H:%M') if card[2] else 'Unknown'}")
    print(f"复习次数: {card[3]}")

    cursor.execute('''
        SELECT review_date, quality, ease_factor, interval, next_review
        FROM review_history
        WHERE card_id = ?
        ORDER BY review_date DESC
    ''', (card_id,))
    history = cursor.fetchall()

    if history:
        print("\n复习历史:")
        print("-" * 90)
        print(f"{'复习时间':<19} {'质量评分':<8} {'简易度':<8} {'间隔':<12} {'下次复习':<19}")
        print("-" * 90)

        for record in history:
            interval = record[3]
            if interval < 1:
                interval_str = f"{int(interval * 24 * 60)}分钟"
            else:
                interval_str = f"{int(interval)}天"

            print(f"{record[0].strftime('%Y-%m-%d %H:%M'):<19} "
                  f"{record[1]:<8} "
                  f"{record[2]:<8.2f} "
                  f"{interval_str:<12} "
                  f"{record[4].strftime('%Y-%m-%d %H:%M')}")
    else:
        print("\n该卡片尚无复习记录")

    conn.close()


if __name__ == "__main__":
    while True:
        print("\n=== 闪卡查看器 ===")
        print("1. 查看所有卡片概览")
        print("2. 查看特定卡片历史")
        print("3. 退出")

        choice = input("\n请选择功能 (1-3): ")

        if choice == "1":
            view_all_cards()
        elif choice == "2":
            try:
                card_id = int(input("请输入卡片ID: "))
                view_card_history(card_id)
            except ValueError:
                print("错误：请输入有效的卡片ID（数字）")
        elif choice == "3":
            print("感谢使用！")
            break
        else:
            print("无效选择，请重试")