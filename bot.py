import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, InlineQueryHandler
from uuid import uuid4

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def check_winner(board):
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] and board[i][0] != " ":
            return board[i][0]
        if board[0][i] == board[1][i] == board[2][i] and board[0][i] != " ":
            return board[0][i]
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != " ":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != " ":
        return board[0][2]
    if all(cell != " " for row in board for cell in row):
        return "Tie"
    return None

def get_fancy_board(board):
    """تصميم مربعات عريض ونظيف تماماً مثل الصورة"""
    keyboard = []
    for r in range(3):
        row = []
        for c in range(3):
            cell = board[r][c]
            if cell == "X":
                text = "❌"
            elif cell == "O":
                text = "⭕"
            else:
                text = "▪️"  # مربعات فارغة وأنيقة
            row.append(InlineKeyboardButton(text, callback_data=f"cell_{r}_{c}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔄 ── إعادة ضبط المعركة ── 🔄", callback_data="action_reset")])
    return InlineKeyboardMarkup(keyboard)

def parse_board_from_markup(reply_markup):
    """استخراج حالة المربعات مباشرة من الأزرار الظاهرة على الشاشة لتفادي أي أخطاء"""
    board = [[" " for _ in range(3)] for _ in range(3)]
    if not reply_markup or not reply_markup.inline_keyboard:
        return board
    
    for r in range(3):
        for c in range(3):
            if r < len(reply_markup.inline_keyboard) and c < len(reply_markup.inline_keyboard[r]):
                btn_text = reply_markup.inline_keyboard[r][c].text
                if "❌" in btn_text:
                    board[r][c] = "X"
                elif "⭕" in btn_text:
                    board[r][c] = "O"
                else:
                    board[r][c] = " "
    return board

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🎮 **لوحة التحدي الكبرى (X-O)** 🎮\n\n"
        "اكتب في محادثة صديقك:\n"
        "`@Blend_XO_Game_Bot` وحط مسافة لبدء المعركة!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    
    board = [[" " for _ in range(3)] for _ in range(3)]
    text = (
        "🎮 **لوحة التحدي الكبرى (X-O)** 🕹️\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📊 **لوحة النتيجة الحالية:** 📊\n"
        "👑 أبو مِيلاف: 0 | 🎯 أم مِيلاف: 0 | 🤝 تعادل: 0\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "دور اللاعب الحالي: أبو مِيلاف 👑 (❌)"
    )
    
    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="🎮 ابدأ لوحة التحدي الكبرى (X-O)",
            description="اضغط هنا لإرسال اللعبة بتصميم عريض واستجابة مضمونة",
            input_message_content=InputTextMessageContent(
                message_text=text,
                parse_mode="Markdown"
            ),
            reply_markup=get_fancy_board(board)
        )
    ]
    await query.answer(results, cache_time=0)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    message = query.message
    inline_message_id = query.inline_message_id
    
    if not message and not inline_message_id:
        return
        
    reply_markup = message.reply_markup if message else None
    if not reply_markup:
        return
        
    current_board = parse_board_from_markup(reply_markup)
    
    x_count = sum(row.count("X") for row in current_board)
    o_count = sum(row.count("O") for row in current_board)
    current_turn = "X" if x_count <= o_count else "O"

    if data == "action_reset":
        new_board = [[" " for _ in range(3)] for _ in range(3)]
        text = (
            "🎮 **لوحة التحدي الكبرى (X-O)** 🕹️\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "📊 **لوحة النتيجة الحالية:** 📊\n"
            "👑 أبو مِيلاف: 0 | 🎯 أم مِيلاف: 0 | 🤝 تعادل: 0\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "دور اللاعب الحالي: أبو مِيلاف 👑 (❌)"
        )
        new_markup = get_fancy_board(new_board)
        if inline_message_id:
            await context.bot.edit_message_text(inline_message_id=inline_message_id, text=text, reply_markup=new_markup, parse_mode="Markdown")
        else:
            await query.edit_message_text(text=text, reply_markup=new_markup, parse_mode="Markdown")
        return

    if data.startswith("cell_"):
        _, r, c = data.split("_")
        r, c = int(r), int(c)
        
        if current_board[r][c] == " ":
            current_board[r][c] = current_turn
            winner = check_winner(current_board)
            
            if winner:
                if winner == "X":
                    status_msg = "🎉 **فاز في الجولة: أبو مِيلاف 👑 (❌)!**"
                elif winner == "O":
                    status_msg = "🎉 **فاز في الجولة: أم مِيلاف 🎯 (⭕)!**"
                else:
                    status_msg = "🤝 **تعادلت المعركة بينكم!**"
                
                current_board = [[" " for _ in range(3)] for _ in range(3)]
                text = f"🎮 **انتهت الجولة!**\n{status_msg}\n👇 اضغط على المربعات للجولة التالية:"
            else:
                next_turn = "O" if current_turn == "X" else "X"
                turn_str = "دور اللاعب الحالي: أبو مِيلاف 👑 (❌)" if next_turn == "X" else "دور اللاعب الحالي: أم مِيلاف 🎯 (⭕)"
                
                text = (
                    "🎮 **لوحة التحدي الكبرى (X-O)** 🕹️\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    "📊 **لوحة النتيجة الحالية:** 📊\n"
                    "👑 أبو مِيلاف: 0 | 🎯 أم مِيلاف: 0 | 🤝 تعادل: 0\n"
                    "━━━━━━━━━━━━━━━━━━━\n"
                    f"{turn_str}"
                )
            
            new_markup = get_fancy_board(current_board)
            if inline_message_id:
                await context.bot.edit_message_text(inline_message_id=inline_message_id, text=text, reply_markup=new_markup, parse_mode="Markdown")
            else:
                await query.edit_message_text(text=text, reply_markup=new_markup, parse_mode="Markdown")
        else:
            await query.answer("⚠️ هذا المربع محجوز يا بطل!", show_alert=True)

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("خطأ: لم يتم العثور على توكن البوت!")
        return
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("XO Arena Universal Sync Pro is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
