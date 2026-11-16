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
    """تصميم واجهة فخمة وكبيرة وواضحة للمربعات"""
    keyboard = []
    for r in range(3):
        row = []
        for c in range(3):
            cell = board[r][c]
            if cell == "X":
                text = "❌ [ أبو مِيلاف ]"
            elif cell == "O":
                text = "⭕ [ أم مِيلاف ]"
            else:
                text = "▫️  اضغط هنا  ▫️"
            row.append(InlineKeyboardButton(text, callback_data=f"cell_{r}_{c}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔄 ── إعادة ضبط المعركة ── 🔄", callback_data="action_reset")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔥 **XO ARENA - ساحة التحدي المباشر** 🔥\n\n"
        "🎮 **طريقة اللعب مع صديقك:**\n"
        "اكتب في محادثة صديقك:\n"
        "`@Blend_XO_Game_Bot` وحط مسافة، ثم اختر اللعبة لتظهر بينكم مباشرة!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    
    board = [[" " for _ in range(3)] for _ in range(3)]
    text = (
        "⚔️ **معركة XO ARENA الكبرى** ⚔️\n\n"
        "🏆 النقاط: ❌ أبو مِيلاف (0) | ⭕ أم مِيلاف (0)\n\n"
        "⚡ **الدور الحالي:** أبو مِيلاف (❌)"
    )
    
    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="🎮 ابدأ معركة XO Arena المحدثة",
            description="اضغط هنا لإرسال لوحة اللعب الكبيرة والواضحة مع صديقك",
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
        
    # استخراج الأزرار الحالية من الرسالة
    if message and message.reply_markup:
        reply_markup = message.reply_markup
    elif query.inline_message_id:
        # بالنسبة للإنلاين نعتمد على محتوى الكيبورد عبر الكอลباك
        # ولضمان قراءة اللوحة بدقة من الرسالة المحدثة:
        pass

    # سنقوم بالتعامل مع تحديث الـ Inline بمرونة تامة عبر دالة التعديل المناسبة
    # جلب اللوحة الحالية من نص الأزرار أو تخزينها
    if message:
        reply_markup = message.reply_markup
        keyboard_rows = reply_markup.inline_keyboard
        
        if data == "action_reset":
            new_board = [[" " for _ in range(3)] for _ in range(3)]
            text = "🔄 **بدأت جولة جديدة!**\n\n⚡ الدور الحالي: أبو مِيلاف (❌)"
            if inline_message_id:
                await context.bot.edit_message_text(inline_message_id=inline_message_id, text=text, reply_markup=get_fancy_board(new_board), parse_mode="Markdown")
            else:
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
                    text = f"🏁 **انتهت الجولة!**\n\n{msg}\n\n👇 اضغط على زر إعادة الضبط لجولة جديدة."
                else:
                    next_turn = "O" if current_turn == "X" else "X"
                    next_name = "أم مِيلاف (⭕)" if next_turn == "O" else "أبو مِيلاف (❌)"
                    text = f"⚔️ **معركة XO ARENA جارية**\n\n⚡ الدور الحالي: {next_name}"
                    
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
    
    print("XO Arena Big Interface Pro is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
