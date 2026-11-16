import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, InlineQueryHandler
from uuid import uuid4

# تفعيل نظام التنبيهات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# تخزين الألعاب الجارية بالـ chat_id أو بالـ inline_message_id
games_state = {}

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

def get_fancy_board(board, x_name, o_name, turn_name, game_over):
    """تصميم واجهة فخمة وأنيقة لأزرار اللعبة"""
    keyboard = []
    for r in range(3):
        row = []
        for c in range(3):
            cell = board[r][c]
            if cell == "X":
                text = "❌ (أبو مِيلاف)"
            elif cell == "O":
                text = "⭕ (أم مِيلاف)"
            else:
                text = "⬛ ··· فارغ ···"
            row.append(InlineKeyboardButton(text, callback_data=f"cell_{r}_{c}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔄 إعادة تشغيل المعركة", callback_data="action_reset")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب وطريقة اللعب بالإنلاين"""
    text = (
        "╔═══════════════════════╗\n"
        "     🔥 **XO ARENA - ساحة التحدي** 🔥     \n"
        "╚═══════════════════════╝\n\n"
        "🎮 **طريقة اللعب مع صديقك في المحادثة مباشرة:**\n"
        "1️⃣ افتح محادثة صديقك الخاصة.\n"
        "2️⃣ اكتب في خانة الرسائل يوزر البوت واضغط مسافة (مثال: `@YourBotUsername`).\n"
        "3️⃣ ستظهر لك لوحة اللعبة، اضغط عليها لتُرسل لصديقك وتبدأوا اللعب فوراً وجهاً لوجه!\n\n"
        "👑 اللاعب الأول: **أبو مِيلاف (❌)**\n"
        "👑 اللاعب الثاني: **أم مِيلاف (⭕)**"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال اللوحة عبر الانلاين لأي محادثة تريدها مع صديقك"""
    query = update.inline_query
    
    # تهيئة لوحة جديدة فارغة للعبة الانلاين
    game_id = str(uuid4())
    board = [[" " for _ in range(3)] for _ in range(3)]
    
    games_state[game_id] = {
        "board": board,
        "turn": "X",
        "scores": {"X": 0, "O": 0, "ties": 0},
        "game_over": False
    }
    
    text = (
        "╔═══════════════════════╗\n"
        "     ⚔️ **معركة XO ARENA جارية** ⚔️     \n"
        "╚═══════════════════════╝\n\n"
        "🏆 النقاط: ❌ أبو مِيلاف (0) | ⭕ أم مِيلاف (0)\n\n"
        "⚡ **الدور الحالي لـ:** أبو مِيلاف (❌)\n"
        "👇 اضغط على المربعات أدناه للعب داخل الدردشة!"
    )
    
    keyboard = get_fancy_board(board, "أبو مِيلاف", "أم مِيلاف", "أبو مِيلاف", False)
    
    results = [
        InlineQueryResultArticle(
            id=game_id,
            title="🎮 ابدأ معركة XO Arena الآن!",
            description="اضغط هنا لإرسال اللعبة إلى صديقك واللعب معاً فوراً (أبو مِيلاف ضد أم مِيلاف)",
            input_message_content=InputTextMessageContent(
                text=text,
                parse_mode="Markdown"
            ),
            reply_markup=keyboard
        )
    ]
    await query.answer(results, cache_time=0)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدارة تفاعل الضغطات على المربعات وتحديث اللعبة"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    message = query.message
    
    # البحث عن اللعبة عبر نص الرسالة أو مفتاحها
    # بما أن اللعبة في الانلاين نعتمد على محتوى الرسالة المحدث
    # سنقوم بالتعامل مع الأزرار وتحديث اللوحة مباشرة
    
    # للتسهيل والضمان في تحديث الـ Inline Message عبر الأزرار:
    # نقوم باستخراج الحالة أو تعديل اللوحة مباشرة من الـ reply_markup الحالي
    reply_markup = message.reply_markup
    keyboard_rows = reply_markup.inline_keyboard
    
    if data == "action_reset":
        # إعادة تعيين اللوحة
        new_board = [[" " for _ in range(3)] for _ in range(3)]
        new_keyboard = get_fancy_board(new_board, "أبو مِيلاف", "أم مِيلاف", "أبو مِيلاف", False)
        text = (
            "╔═══════════════════════╗\n"
            "     🔄 **تم إعادة تعيين الساحة** 🔄     \n"
            "╚═══════════════════════╝\n\n"
            "⚡ **الدور الحالي لـ:** أبو مِيلاف (❌)\n"
            "👇 أكملوا التحدي!"
        )
        await query.edit_message_text(text=text, reply_markup=new_keyboard, parse_mode="Markdown")
        return

    if data.startswith("cell_"):
        _, r, c = data.split("_")
        r, c = int(r), int(c)
        
        # استخراج اللوحة الحالية من الأزرار
        current_board = []
        for row in keyboard_rows[:-1]: # استثناء زر الإعادة الأخير
            board_row = []
            for btn in row:
                if "أبو مِيلاف" in btn.text:
                    board_row.append("X")
                elif "أم مِيلاف" in btn.text:
                    board_row.append("O")
                else:
                    board_row.append(" ")
            current_board.append(board_row)
            
        if current_board[r][c] == " " :
            # تحديد الدور بناءً على من الضغط أو تتبع الرموز
            x_count = sum(row.count("X") for row in current_board)
            o_count = sum(row.count("O") for row in current_board)
            current_turn = "X" if x_count == o_count else "O"
            
            current_board[r][c] = current_turn
            
            winner = check_winner(current_board)
            
            if winner:
                if winner == "X":
                    msg = "🎉 **فاز في هذه الجولة: أبو مِيلاف (❌)!** 🏆"
                elif winner == "O":
                    msg = "🎉 **فاز في هذه الجولة: أم مِيلاف (⭕)!** 🏆"
                else:
                    msg = "🤝 **تعادلت المعركة! لا يوجد فائز.**"
                    
                text = (
                    "╔═══════════════════════╗\n"
                    "     🏁 **انتهت الجولة!** 🏁     \n"
                    "╚═══════════════════════╝\n\n"
                    f"{msg}\n\n"
                    "👇 اضغط على (إعادة تشغيل المعركة) لجولة جديدة!"
                )
                next_turn_name = "انتهت الجولة"
            else:
                next_turn = "O" if current_turn == "X" else "X"
                next_turn_name = "أم مِيلاف (⭕)" if next_turn == "O" else "أبو مِيلاف (❌)"
                text = (
                    "╔═══════════════════════╗\n"
                    "     ⚔️ **معركة XO ARENA جارية** ⚔️     \n"
                    "╚═══════════════════════╝\n\n"
                    f"⚡ **الدور الحالي لـ:** {next_turn_name}\n"
                    "👇 تابعوا اللعب!"
                )
                
            new_keyboard = get_fancy_board(current_board, "أبو مِيلاف", "أم مِيلاف", next_turn_name, bool(winner))
            await query.edit_message_text(text=text, reply_markup=new_keyboard, parse_mode="Markdown")
        else:
            await query.answer("⚠️ هذا المربع محجوز يا بطل، اختر غيره!", show_alert=True)

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("خطأ: لم يتم العثور على توكن البوت!")
        return
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("XO Arena Inline Pro is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
