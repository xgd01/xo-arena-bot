import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler,
    CallbackQueryHandler, ContextTypes
)

TOKEN = os.getenv("BOT_TOKEN")

DB = "xo_stats.db"
games = {}

PLAYER_X = "أبو مِيلاف"
PLAYER_O = "أم مِيلاف"


# DATABASE

def db():
    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY,
            name TEXT,
            games INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            draws INTEGER DEFAULT 0
        )
    """)
    con.commit()
    return con


def save(user, result, name):
    con = db()
    con.execute("""
        INSERT INTO players VALUES (?, ?, 1, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
        name=excluded.name,
        games=games+1,
        wins=wins+excluded.wins,
        losses=losses+excluded.losses,
        draws=draws+excluded.draws
    """, (
        user.id,
        name,
        int(result == "win"),
        int(result == "loss"),
        int(result == "draw")
    ))
    con.commit()
    con.close()


# GAME DISPLAY

def keyboard(chat_id, board):
    rows = []
    for r in range(3):
        row = []
        for c in range(3):
            i = r * 3 + c
            row.append(InlineKeyboardButton(
                board[i] or "▫️",
                callback_data=f"m|{chat_id}|{i}"
            ))
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def game_text(g):
    s = (
        "💕 XO ARENA 💕\n"
        "━━━━━━━━━━━━\n"
        "❌ X: أبو مِيلاف\n"
        "⭕ O: أم مِيلاف\n\n"
    )

    if not g["o"]:
        return s + "بانتظار انضمام اللاعب الثاني 🥰"

    if g["status"] == "playing":
        p = PLAYER_X if g["turn"] == "X" else PLAYER_O
        return s + f"🎮 الدور الآن: {p}"

    if g["status"] == "draw":
        return s + "🤝 تعادل! الحب فاز ❤️"

    winner = PLAYER_X if g["status"] == "X" else PLAYER_O
    return s + f"🏆 الفائز: {winner} ❤️"


# COMMANDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💕 أهلاً بكم في XO ARENA 💕\n"
        "اللعبة الخاصة بأبو مِيلاف وأم مِيلاف.\n\n"
        "استخدموا الأمر /newgame للبدء في الخاص أو في أي مجموعة."
    )


async def newgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # السماح باللعب في الخاص أو المجموعات
    if chat.type not in ("private", "group", "supergroup"):
        await update.message.reply_text("استخدم الأمر في الخاص أو داخل المجموعة.")
        return

    old = games.get(chat.id)
    if old and old["status"] in ("waiting", "playing"):
        await update.message.reply_text("هناك مباراة جارية بالفعل!")
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
                "💕 انضمام للعبة",
                callback_data=f"j|{chat.id}"
            )
        ]])
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    con = db()
    row = con.execute(
        "SELECT games,wins,losses,draws FROM players WHERE id=?",
        (user.id,)
    ).fetchone()
    con.close()

    if not row:
        await update.message.reply_text("لا توجد مباريات مسجلة بعد.")
        return

    total, wins, losses, draws = row
    rate = round(wins / total * 100, 1) if total > 0 else 0

    await update.message.reply_text(
        f"📊 إحصائيات {user.full_name}\n"
        f"🎮 المباريات: {total}\n"
        f"🏆 الفوز: {wins}\n"
        f"💔 الخسارة: {losses}\n"
        f"🤝 التعادل: {draws}\n"
        f"📈 نسبة الفوز: {rate}%"
    )


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    con = db()
    rows = con.execute(
        "SELECT name,wins,games FROM players "
        "ORDER BY wins DESC LIMIT 10"
    ).fetchall()
    con.close()

    msg = "🏆 ترتيب أبطال الحب\n━━━━━━━━━━━━\n"
    medals = ["🥇", "🥈", "🥉"]

    for i, (name, wins, total) in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i+1}."
        msg += f"{medal} {name}: {wins} فوز\n"

    await update.message.reply_text(msg)


# GAME BUTTONS

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data.split("|")
    action = data[0]
    chat_id = int(data[1])
    g = games.get(chat_id)

    if not g:
        await q.answer("المباراة غير موجودة!", show_alert=True)
        return

    user = q.from_user

    if action == "j":
        if g["status"] != "waiting":
            await q.answer("المباراة بدأت بالفعل!", show_alert=True)
            return

        if g["x"] and user.id == g["x"].id:
            await q.answer("لا يمكنك اللعب ضد نفسك!", show_alert=True)
            return

        g["o"] = user
        g["status"] = "playing"

        await q.answer("تم انضمام اللاعب بنجاح ❤️")
        await q.edit_message_text(
            game_text(g),
            reply_markup=keyboard(chat_id, g["board"])
        )
        return

    if g["status"] != "playing":
        await q.answer("المباراة انتهت!", show_alert=True)
        return

    current = g["x"] if g["turn"] == "X" else g["o"]

    if not current or user.id != current.id:
        await q.answer("ليس دورك الآن ❤️", show_alert=True)
        return

    index = int(data[2])

    if g["board"][index]:
        await q.answer("هذا المربع محجوز!", show_alert=True)
        return

    symbol = g["turn"]
    g["board"][index] = symbol

    lines = [
        (0,1,2), (3,4,5), (6,7,8),
        (0,3,6), (1,4,7), (2,5,8),
        (0,4,8), (2,4,6)
    ]

    won = any(
        all(g["board"][j] == symbol for j in line)
        for line in lines
    )

    if won:
        g["status"] = symbol
        winner = g["x"] if symbol == "X" else g["o"]
        loser = g["o"] if symbol == "X" else g["x"]

        save(winner, "win", PLAYER_X if symbol == "X" else PLAYER_O)
        save(loser, "loss", PLAYER_O if symbol == "X" else PLAYER_X)

    elif all(g["board"]):
        g["status"] = "draw"
        save(g["x"], "draw", PLAYER_X)
        save(g["o"], "draw", PLAYER_O)

    else:
        g["turn"] = "O" if symbol == "X" else "X"

    await q.answer()
    await q.edit_message_text(
        game_text(g),
        reply_markup=(
            keyboard(chat_id, g["board"])
            if g["status"] == "playing" else None
        )
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💕 XO ARENA 💕\n"
        "/newgame - مباراة جديدة\n"
        "/stats - إحصائياتك\n"
        "/leaderboard - الترتيب\n"
        "/help - المساعدة"
    )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN غير موجود!")

    db().close()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newgame", newgame))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(buttons))

    print("XO ARENA - Private & Group Supported")
    app.run_polling()


if __name__ == "__main__":
    main()
