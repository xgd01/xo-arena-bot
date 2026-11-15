
import os
import sqlite3

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")

DB = "xo_stats.db"
games = {}

# أسماء العرض ثابتة كما طلبت
PLAYER_X = "أبو مِيلاف"
PLAYER_O = "أم مِيلاف"


# =========================
# DATABASE
# =========================

def db():
    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            games INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            draws INTEGER DEFAULT 0
        )
    """)
    con.commit()
    return con


def save(user, result):
    con = db()

    wins = int(result == "win")
    losses = int(result == "loss")
    draws = int(result == "draw")

    con.execute("""
        INSERT INTO players
        (id, name, games, wins, losses, draws)
        VALUES (?, ?, 1, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            games = games + 1,
            wins = wins + excluded.wins,
            losses = losses + excluded.losses,
            draws = draws + excluded.draws
    """, (
        user.id,
        user.full_name,
        wins,
        losses,
        draws
    ))

    con.commit()
    con.close()


# =========================
# GAME DISPLAY
# =========================

def keyboard(chat_id, board):
    rows = []

    for r in range(3):
        row = []

        for c in range(3):
            i = r * 3 + c

            row.append(
                InlineKeyboardButton(
                    board[i] or "▫️",
                    callback_data=f"m|{chat_id}|{i}"
                )
            )

        rows.append(row)

    return InlineKeyboardMarkup(rows)


def game_text(g):
    s = (
        "💕 XO ARENA 💕\n"
        "━━━━━━━━━━━━\n"
        f"❌ X: {PLAYER_X}\n"
        f"⭕ O: {PLAYER_O}\n\n"
    )

    if not g["o"]:
        return s + "بانتظار أم مِيلاف للانضمام 🥰"

    if g["status"] == "playing":
        p = PLAYER_X if g["turn"] == "X" else PLAYER_O
        return s + f"🎮 الدور الآن: {p}"

    if g["status"] == "draw":
        return s + "🤝 تعادل! الحب فاز ❤️"

    winner = PLAYER_X if g["status"] == "X" else PLAYER_O
    return s + f"🏆 الفائز: {winner} ❤️"


# =========================
# COMMANDS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💕 أهلاً بكم في XO ARENA 💕\n"
        "لعبة XO مفتوحة للجميع!\n\n"
        "استخدموا /newgame داخل مجموعتكم."
    )


async def newgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text(
            "استخدم الأمر داخل المجموعة."
        )
        return

    old = games.get(chat.id)

    if old and old["status"] in ("waiting", "playing"):
        await update.message.reply_text(
            "هناك مباراة جارية بالفعل! انتظروا حتى تنتهي ❤️"
        )
        return

    g = {
        "x": user,
        "o": None,
        "board": [""] * 9,
        "turn": "X",
        "status": "waiting"
    }

    games[chat.id] = g

    await update.message.reply_text(
        game_text(g),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "💕 انضمام أم مِيلاف",
                callback_data=f"j|{chat.id}"
            )
        ]])
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    con = db()
    row = con.execute(
        "SELECT games, wins, losses, draws "
        "FROM players WHERE id = ?",
        (user.id,)
    ).fetchone()
    con.close()

    if not row:
        await update.message.reply_text(
            "📊 لا توجد مباريات مسجلة لك بعد."
        )
        return

    total, wins, losses, draws = row
    rate = round(wins / total * 100, 1) if total else 0

    await update.message.reply_text(
        f"📊 إحصائيات {user.full_name}\n"
        "━━━━━━━━━━━━\n"
        f"🎮 المباريات: {total}\n"
        f"🏆 الفوز: {wins}\n"
        f"💔 الخسارة: {losses}\n"
        f"🤝 التعادل: {draws}\n"
        f"📈 نسبة الفوز: {rate}%"
    )


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    con = db()

    rows = con.execute(
        "SELECT name, wins, games FROM players "
        "ORDER BY wins DESC, games ASC LIMIT 10"
    ).fetchall()

    con.close()

    if not rows:
        await update.message.reply_text(
            "🏆 لا توجد إحصائيات حتى الآن."
        )
        return

    msg = "🏆 ترتيب أبطال XO ARENA\n━━━━━━━━━━━━\n"
    medals = ["🥇", "🥈", "🥉"]

    for i, (name, wins, total) in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i + 1}."
        msg += f"{medal} {name}: {wins} فوز | {total} مباراة\n"

    await update.message.reply_text(msg)


# =========================
# GAME BUTTONS
# =========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data.split("|")

    if len(data) < 2:
        await q.answer("طلب غير صالح!", show_alert=True)
        return

    action = data[0]

    try:
        chat_id = int(data[1])
    except ValueError:
        await q.answer("بيانات غير صحيحة!", show_alert=True)
        return

    # التأكد أن الزر تابع للمجموعة نفسها
    if not q.message or q.message.chat.id != chat_id:
        await q.answer("هذه المباراة ليست في هذه المجموعة!", show_alert=True)
        return

    g = games.get(chat_id)

    if not g:
        await q.answer("المباراة غير موجودة أو انتهت!", show_alert=True)
        return

    user = q.from_user

    # الانضمام للمباراة
    if action == "j":

        if g["status"] != "waiting":
            await q.answer("المباراة بدأت بالفعل أو انتهت!", show_alert=True)
            return

        if user.id == g["x"].id:
            await q.answer("لا يمكنك اللعب ضد نفسك!", show_alert=True)
            return

        g["o"] = user
        g["status"] = "playing"

        await q.answer("أهلاً بك في المباراة ❤️")

        await q.edit_message_text(
            game_text(g),
            reply_markup=keyboard(chat_id, g["board"])
        )
        return

    # تنفيذ حركة
    if action != "m" or len(data) != 3:
        await q.answer("حركة غير صالحة!", show_alert=True)
        return

    if g["status"] != "playing":
        await q.answer("المباراة انتهت!", show_alert=True)
        return

    try:
        index = int(data[2])
    except ValueError:
        await q.answer("مربع غير صالح!", show_alert=True)
        return

    if not 0 <= index <= 8:
        await q.answer("مربع غير صالح!", show_alert=True)
        return

    current = g["x"] if g["turn"] == "X" else g["o"]

    if user.id != current.id:
        await q.answer("ليس دورك الآن ❤️", show_alert=True)
        return

    if g["board"][index]:
        await q.answer("هذا المربع محجوز!", show_alert=True)
        return

    symbol = g["turn"]
    g["board"][index] = symbol

    lines = [
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6)
    ]

    won = any(
        all(g["board"][j] == symbol for j in line)
        for line in lines
    )

    if won:
        g["status"] = symbol

        winner = g["x"] if symbol == "X" else g["o"]
        loser = g["o"] if symbol == "X" else g["x"]

        save(winner, "win")
        save(loser, "loss")

    elif all(g["board"]):
        g["status"] = "draw"

        save(g["x"], "draw")
        save(g["o"], "draw")

    else:
        g["turn"] = "O" if symbol == "X" else "X"

    await q.answer()

    await q.edit_message_text(
        game_text(g),
        reply_markup=(
            keyboard(chat_id, g["board"])
            if g["status"] == "playing"
            else None
        )
    )


# =========================
# HELP
# =========================

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💕 XO ARENA 💕\n"
        "━━━━━━━━━━━━\n"
        "/newgame - إنشاء مباراة جديدة\n"
        "/stats - إحصائياتك\n"
        "/leaderboard - ترتيب اللاعبين\n"
        "/help - المساعدة\n\n"
        "اللعبة مفتوحة لجميع أعضاء المجموعة ❤️"
    )


# =========================
# MAIN
# =========================

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN غير موجود في متغيرات البيئة!")

    db().close()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newgame", newgame))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("help", help_cmd))

    app.add_handler(CallbackQueryHandler(buttons))

    print("XO ARENA is running!")

    app.run_polling()


if __name__ == "__main__":
    main()
