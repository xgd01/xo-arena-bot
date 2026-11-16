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
    keyboard = []
    for r in range(3):
        row = []
        for c in range(3):
            cell = board[r][c]
            if cell == "X":
                text = "❌ أبو مِيلاف"
            elif cell == "O":
                text = "⭕ أم مِيلاف"
            else:
                text = "⬛ فارغ"
            row.append(InlineKeyboardButton(text, callback_data=f"cell_{r}_{c}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔄 جولة جديدة", callback_data="action_reset")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔥 **XO ARENA - ساحة التحدي** 🔥\n\n"
        "🎮 **طريقة اللعب السريع مع صديقك:**\n"
        "فقط ادخل إلى محادثة صديقك واكتب:\n"
        "`@Blend_XO_Game_Bot` مع مسافة، واضغط على النتيجة لتظهر اللعبة بينكم مباشرة!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    
    board = [[" " for _ in range(3)] for _ in range(3)]
    text = (
        "⚔️ **معركة XO ARENA جارية** ⚔️\n\n"
        "🏆 النقاط: ❌ أبو مِيلاف (0) | ⭕ أم مِيلاف (0)\n\n"
        "⚡ **الدور الحالي:** أبو مِيلاف (❌)"
    )
    
    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="🎮 ابدأ تحدي XO Arena الآن",
            description="اضغط هنا لإرسال اللعبة ومراجعة التحدي مع صديقك فوراً",
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
    if not message:
        return
        
    reply_markup = message.reply_markup
    if not reply_markup:
        return
        
    keyboard_rows = reply_markup.inline_keyboard
    
    if data == "action_reset":
        new_board = [[" " for _ in range(3)] for _ in range(3)]
        text = "🔄 **جولة جديدة بدأت!**\n\n⚡ الدور الحالي: أبو مِيلاف (❌)"
        await query.edit_message_text(text=text, reply_markup=get_fancy_board(new_board), parse_mode="Markdown")
        return

    if data.startswith("cell_"):
        _, r, c = data.split("_")
        r, c = int(r), int(c)
        
        current_board = []
        for row in keyboard_rows[:-1]:
            board_row = []
            for btn in row:
                if "أبو مِيلاف" in btn.text:
                    board_row.append("X")
                elif "أم مِيلاف" in btn.text:
                    board_row.append("O")
                else:
                    board_row.append(" ")
            current_board.append(board_row)
            
        if current_board[r][c] == " ":
            x_count = sum(row.count("X") for row in current_board)
            o_count = sum(row.count("O") for row in current_board)
            current_turn = "X" if x_count == o_count else "O"
            
            current_board[r][c] = current_turn
            winner = check_winner(current_board)
            
            if winner:
                if winner == "X":
                    msg = "🎉 **فاز في الجولة: أبو مِيلاف (❌)!**"
                elif winner == "O":
                    msg = "🎉 **فاز في الجولة: أم مِيلاف (⭕)!**"
                else:
                    msg = "🤝 **تعادلت المعركة!**"
                text = f"🏁 **انتهت الجولة!**\n\n{msg}\n\n👇 اضغط على زر جولة جديدة للبدء من جديد."
            else:
                next_turn = "O" if current_turn == "X" else "X"
                next_name = "أم مِيلاف (⭕)" if next_turn == "O" else "أبو مِيلاف (❌)"
                text = f"⚔️ **المعركة مستمرة**\n\n⚡ الدور الحالي: {next_name}"
                
            await query.edit_message_text(text=text, reply_markup=get_fancy_board(current_board), parse_mode="Markdown")
        else:
            await query.answer("⚠️ هذا المربع محجوز!", show_alert=True)

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("خطأ: لم يتم العثور على توكن البوت!")
        return
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("XO Arena Clean Inline Pro is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
