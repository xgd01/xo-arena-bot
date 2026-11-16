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
    """تصميم مربعات نظيفة وفارغة وأنيقة تماماً"""
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
                text = "⬜"  # مربع فارغ ونظيف
            row.append(InlineKeyboardButton(text, callback_data=f"cell_{r}_{c}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔄 ── إعادة ضبط المعركة ── 🔄", callback_data="action_reset")])
    return InlineKeyboardMarkup(keyboard)

def parse_board_from_markup(reply_markup):
    """استخراج مصفوفة اللعبة مباشرة من حالة الأزرار الحالية على الشاشة"""
    board = [[" " for _ in range(3)] for _ in range(3)]
    if not reply_markup or not reply_markup.inline_keyboard:
        return board
    
    for r in range(3):
        for c in range(3):
            # التأكد من عدم تجاوز حدود الأزرار
            if r < len(reply_markup.inline_keyboard) and c < len(reply_markup.inline_keyboard[r]):
                btn_text = reply_markup.inline_keyboard[r][c].text
                if "أبو مِيلاف" in btn_text or "❌" in btn_text:
                    board[r][c] = "X"
                elif "أم مِيلاف" in btn_text or "⭕" in btn_text:
                    board[r][c] = "O"
                else:
                    board[r][c] = " "
    return board

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔥 **XO ARENA - ساحة التحدي** 🔥\n\n"
        "🎮 **طريقة اللعب:**\n"
        "اكتب في محادثة صديقك:\n"
        "`@Blend_XO_Game_Bot` وحط مسافة، ثم اختر اللعبة وابدؤوا التحدي!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query
    
    board = [[" " for _ in range(3)] for _ in range(3)]
    text = (
        "⚔️ **معركة XO ARENA الكبرى** ⚔️\n\n"
        "📊 **[ لوحة عداد النقاط ]**\n"
        "❌ أبو مِيلاف: `0` نقاط\n"
        "⭕ أم مِيلاف: `0` نقاط\n"
        "🤝 التعادل: `0`\n\n"
        "⚡ **الدور الحالي:** أبو مِيلاف (❌)"
    )
    
    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="🎮 ابدأ معركة XO Arena التفاعلية",
            description="اضغط هنا لإرسال اللعبة بمربعات فارغة وتفاعل فوري",
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
        
    # استخراج الكيبورد الحالي من رسالة الإنلاين
    reply_markup = message.reply_markup if message else None
    if not reply_markup:
        return
        
    current_board = parse_board_from_markup(reply_markup)
    
    # حساب عدد الـ X و O لمعرفة الدور الحالي
    x_count = sum(row.count("X") for row in current_board)
    o_count = sum(row.count("O") for row in current_board)
    current_turn = "X" if x_count <= o_count else "O"

    if data == "action_reset":
        new_board = [[" " for _ in range(3)] for _ in range(3)]
        text = (
            "🔄 **بدأت جولة جديدة! التحدي مستمر**\n\n"
            "⚡ **الدور الحالي:** أبو مِيلاف (❌)"
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
                    status_msg = "🎉 **فاز في هذه الجولة: أبو مِيلاف (❌)!** 🏆"
                elif winner == "O":
                    status_msg = "🎉 **فاز في هذه الجولة: أم مِيلاف (⭕)!** 🏆"
                else:
                    status_msg = "🤝 **تعادلت المعركة! لا يوجد فائز.**"
                
                # مسح اللوحة للجولة التالية مع الحفاظ على التفاعل
                current_board = [[" " for _ in range(3)] for _ in range(3)]
                text = f"🏁 **انتهت الجولة!**\n\n{status_msg}\n\n👇 اضغط على المربعات للجولة التالية!"
            else:
                next_turn = "O" if current_turn == "X" else "X"
                next_name = "أم مِيلاف (⭕)" if next_turn == "O" else "أبو مِيلاف (❌)"
                text = f"⚔️ **معركة XO ARENA جارية**\n\n⚡ **الدور الحالي:** {next_name}"
            
            new_markup = get_fancy_board(current_board)
            if inline_message_id:
                await context.bot.edit_message_text(inline_message_id=inline_message_id, text=text, reply_markup=new_markup, parse_mode="Markdown")
            else:
                await query.edit_message_text(text=text, reply_markup=new_markup, reply_markup=new_markup, parse_mode="Markdown")
        else:
            await query.answer("⚠️ هذا المربع محجوز يا بطل، اختر مكاناً آخر!", show_alert=True)

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("خطأ: لم يتم العثور على توكن البوت!")
        return
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("XO Arena Direct Sync Pro is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
