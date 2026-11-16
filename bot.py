import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

# تفعيل نظام التنبيهات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# تخزين حالات الألعاب والنقاط لكل محادثة
games_state = {}

def check_winner(board):
    """التحقق التلقائي من الفائز (صفوف، أعمدة، أقطار)"""
    # فحص الصفوف والأعمدة
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] and board[i][0] != " ":
            return board[i][0]
        if board[0][i] == board[1][i] == board[2][i] and board[0][i] != " ":
            return board[0][i]
            
    # فحص الأقطار
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != " ":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != " ":
        return board[0][2]
        
    # فحص التعادل (إذا امتلأت اللوحة ولم ينجح أحد)
    if all(cell != " " for row in board for cell in row):
        return "Tie"
        
    return None

def get_fancy_board(board, is_game_over):
    """إنشاء لوحة تفاعلية بتصميم أنيق ومميز"""
    keyboard = []
    for r in range(3):
        row = []
        for c in range(3):
            cell = board[r][c]
            if cell == "X":
                text = "❌ ( أبو مِيلاف )"
            elif cell == "O":
                text = "⭕ ( أم مِيلاف )"
            else:
                text = "⬛ 🞲 فارغ 🞲"
            
            # إذا انتهت اللعبة، نجعل الأزرار غير قابلة للضغط أو نغير شكلها
            row.append(InlineKeyboardButton(text, callback_data=f"cell_{r}_{c}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔄 جولة جديدة", callback_data="action_reset")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء اللعبة وإنشاء لوحة النقاط لأول مرة"""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # إذا لم تكن النتائج موجودة لهذه المحادثة، نبدأها من الصفر
    if chat_id not in games_state:
        games_state[chat_id] = {
            "scores": {"X": 0, "O": 0, "ties": 0}
        }
        
    games_state[chat_id].update({
        "board": [[" " for _ in range(3)] for _ in range(3)],
        "turn": "X",
        "player_x": {"id": user.id, "name": user.first_name},
        "player_o": None,
        "status": "waiting_for_opponent",
        "game_over": False
    })
    
    game = games_state[chat_id]
    scores = game["scores"]
    
    text = (
        "╔═══════════════════════╗\n"
        "     🔥 **XO ARENA - لوحة الصدارة** 🔥     \n"
        "╚═══════════════════════╝\n\n"
        f"🏆 **النقاط الإجمالية:**\n"
        f"❌ أبو مِيلاف: `{scores['X']}` | ⭕ أم مِيلاف: `{scores['O']}` | 🤝 تعادل: `{scores['ties']}`\n\n"
        f"👑 **اللاعب الأول (X):** {game['player_x']['name']} (أبو مِيلاف)\n"
        "⏳ **اللاعب الثاني (O):** في انتظار انضمام الخصم...\n\n"
        "👇 **اضغط على الزر أدناه للانضمام كـ (أم مِيلاف)!**"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎮 انضم الآن كـ (أم مِيلاف ⭕)", callback_data="action_join")],
        [InlineKeyboardButton("🔄 إعادة ضبط", callback_data="action_reset")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدارة اللعبة وكشف الفائز وتحديث النقاط تلقائياً"""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat.id
    user = query.from_user
    data = query.data
    
    if chat_id not in games_state:
        return
        
    game = games_state[chat_id]
    scores = game["scores"]
    
    # 1. الانضمام كلاعب ثانٍ
    if data == "action_join":
        if game["player_o"] is None:
            if user.id == game["player_x"]["id"]:
                await query.answer("⚠️ لا يمكنك اللعب ضد نفسك يا بطل!", show_alert=True)
                return
            game["player_o"] = {"id": user.id, "name": user.first_name}
            game["status"] = "playing"
            
            text = (
                "╔═══════════════════════╗\n"
                "     ⚔️ **بدأت المعركة الرسمية!** ⚔️     \n"
                "╚═══════════════════════╝\n\n"
                f"🏆 **لوحة الصدارة:** أبو مِيلاف ({scores['X']}) - أم مِيلاف ({scores['O']})\n\n"
                f"❌ **أبو مِيلاف:** {game['player_x']['name']}\n"
                f"⭕ **أم مِيلاف:** {game['player_o']['name']}\n\n"
                "⚡ **الدور الحالي لـ:** أبو مِيلاف (❌)"
            )
            keyboard = get_fancy_board(game["board"], game["game_over"])
            await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await query.answer(f"✅ المقعد محجوز لـ {game['player_o']['name']}", show_alert=True)
        return

    # 2. إعادة تعيين اللعبة لجولة جديدة مع الاحتفاظ بالنقاط
    if data == "action_reset":
        game["board"] = [[" " for _ in range(3)] for _ in range(3)]
        game["turn"] = "X"
        game["game_over"] = False
        
        # التبديل التلقائي لأسماء اللاعبين للجولة الجديدة إذا رغبوا، أو البقاء كما هم
        text = (
            "╔═══════════════════════╗\n"
            "     🔄 **جولة جديدة بدأت!** 🔄     \n"
            "╚═══════════════════════╝\n\n"
            f"🏆 **النقاط:** أبو مِيلاف (`{scores['X']}`) | أم مِيلاف (`{scores['O']}`)\n\n"
            "⚡ **الدور الحالي لـ:** أبو مِيلاف (❌)"
        )
        keyboard = get_fancy_board(game["board"], game["game_over"])
        await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
        return

    # 3. مربعات اللعب وكشف الفائز تلقائياً
    if data.startswith("cell_"):
        if game["status"] == "waiting_for_opponent":
            await query.answer("⏳ انتظر انضمام أم مِيلاف لتبدأ المعركة!", show_alert=True)
            return
            
        if game["game_over"]:
            await query.answer("⚠️ انتهت هذه الجولة، اضغط على زر (جولة جديدة) للعب مجدداً!", show_alert=True)
            return
            
        is_x_player = game["player_x"] and user.id == game["player_x']['id']
        is_o_player = game["player_o"] and user.id == game["player_o']['id']
        
        if not is_x_player and not is_o_player:
            await query.answer("👀 أنت متفرج في هذه المباراة!", show_alert=True)
            return
            
        if game["turn"] == "X" and not is_x_player:
            await query.answer("⏳ ليس دورك، انتظر دور أبو مِيلاف!", show_alert=True)
            return
            
        if game["turn"] == "O" and not is_o_player:
            await query.answer("⏳ ليس دورك، انتظر دور أم مِيلاف!", show_alert=True)
            return

        _, r, c = data.split("_")
        r, c = int(r), int(c)
        board = game["board"]
        
        if board[r][c] == " ":
            board[r][c] = game["turn"]
            
            # فحص الفائز بعد النقلة
            winner = check_winner(board)
            
            if winner:
                game["game_over"] = True
                if winner == "X":
                    scores["X"] += 1
                    win_msg = f"🎉 **فاز في هذه الجولة: أبو مِيلاف (❌)!** 🏆"
                elif winner == "O":
                    scores["O"] += 1
                    win_msg = f"🎉 **فاز في هذه الجولة: أم مِيلاف (⭕)!** 🏆"
                else:
                    scores["ties"] += 1
                    win_msg = f"🤝 **تعادلت المعركة! لا توجد فائز.**"
                    
                text = (
                    "╔═══════════════════════╗\n"
                    "     🏁 **انتهت الجولة!** 🏁     \n"
                    "╚═══════════════════════╝\n\n"
                    f"{win_msg}\n\n"
                    f"🏆 **لوحة الصدارة المحدثة:**\n"
                    f"❌ أبو مِيلاف: `{scores['X']}` | ⭕ أم مِيلاف: `{scores['O']}` | 🤝 تعادل: `{scores['ties']}`\n\n"
                    "👇 اضغط على زر (جولة جديدة) للبدء من جديد!"
                )
            else:
                # تبديل الدور إذا لم تنته اللعبة
                if game["turn"] == "X":
                    game["turn"] = "O"
                    next_name = f"{game['player_o']['name']} (أم مِيلاف ⭕)"
                else:
                    game["turn"] = "X"
                    next_name = f"{game['player_x']['name']} (أبو مِيلاف ❌)"
                    
                text = (
                    "╔═══════════════════════╗\n"
                    "     ⚔️ **المعركة مستمرة** ⚔️     \n"
                    "╚═══════════════════════╝\n\n"
                    f"🏆 **النقاط الحالية:** أبو مِيلاف (`{scores['X']}`) | أم مِيلاف (`{scores['O']}`)\n\n"
                    f"⚡ **دور اللاعب:** {next_name}"
                )
                
            keyboard = get_fancy_board(board, game["game_over"])
            await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await query.answer("⚠️ هذا المربع محجوز، اختر غيره!", show_alert=True)

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("خطأ: لم يتم العثور على توكن البوت في متغيرات البيئة!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("XO ARENA - Scoreboard & Auto-Win Mode Running...")
    app.run_polling()

if __name__ == '__main__':
    main()
