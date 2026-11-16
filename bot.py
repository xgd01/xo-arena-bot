import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler

# تفعيل نظام التنبيهات
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# تخزين حالات الألعاب النشطة
games_state = {}

def get_fancy_board(board, player_x_name, player_o_name, turn):
    """إنشاء لوحة تفاعلية بتصميم أنيق وفخم جداً"""
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
            
            row.append(InlineKeyboardButton(text, callback_data=f"cell_{r}_{c}"))
        keyboard.append(row)
    
    # أزرار تحكم إضافية بتصميم راقي
    keyboard.append([InlineKeyboardButton("🔄 إعادة تشغيل المعركة", callback_data="action_reset")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء اللوحة ودعوة الصديق للانضمام"""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    games_state[chat_id] = {
        "board": [[" " for _ in range(3)] for _ in range(3)],
        "turn": "X",
        "player_x": {"id": user.id, "name": user.first_name},
        "player_o": None,
        "status": "waiting_for_opponent"
    }
    
    game = games_state[chat_id]
    
    text = (
        "╔═══════════════════════╗\n"
        "     🔥 **XO ARENA - ساحة التحدي** 🔥     \n"
        "╚═══════════════════════╝\n\n"
        f"👑 **اللاعب الأول (X):** {game['player_x']['name']} (أبو مِيلاف)\n"
        "⏳ **اللاعب الثاني (O):** في انتظار انضمام الخصم...\n\n"
        "👇 **اضغط على الزر أدناه لتدخل كـ (أم مِيلاف) وتلعب مع صديقك مباشرة!**"
    )
    
    keyboard = [
        [InlineKeyboardButton("🎮 انضم الآن كـ (أم مِيلاف ⭕)", callback_data="action_join")],
        [InlineKeyboardButton("🔄 بدء جلسة جديدة", callback_data="action_reset")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدارة تفاعل الأزرار بالكامل بين اللاعبين"""
    query = update.callback_query
    await query.answer()
    
    chat_id = query.message.chat.id
    user = query.from_user
    data = query.data
    
    if chat_id not in games_state:
        # إذا لم تكن اللعبة مسجلة، نقوم بتهئيتها تلقائياً
        games_state[chat_id] = {
            "board": [[" " for _ in range(3)] for _ in range(3)],
            "turn": "X",
            "player_x": {"id": user.id, "name": user.first_name},
            "player_o": None,
            "status": "playing"
        }
    
    game = games_state[chat_id]
    
    # 1. زر الانضمام كلاعب ثانٍ
    if data == "action_join":
        if game["player_o"] is None:
            if user.id == game["player_x"]["id"]:
                await query.answer("⚠️ لا يمكنك اللعب ضد نفسك يا بطل! اعطِ الرابط لصديقك لينضم.", show_alert=True)
                return
            game["player_o"] = {"id": user.id, "name": user.first_name}
            game["status"] = "playing"
            
            text = (
                "╔═══════════════════════╗\n"
                "     🔥 **معركة XO ARENA بدأت!** 🔥     \n"
                "╚═══════════════════════╝\n\n"
                f"❌ **أبو مِيلاف:** {game['player_x']['name']}\n"
                f"⭕ **أم مِيلاف:** {game['player_o']['name']}\n\n"
                "⚡ **الدور الحالي لـ:** أبو مِيلاف (❌)"
            )
            keyboard = get_fancy_board(game["board"], game["player_x"]["name"], game["player_o"]["name"], game["turn"])
            await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await query.answer(f"✅ المقعد محجوز مسبقاً لـ {game['player_o']['name']}", show_alert=True)
        return

    # 2. زر إعادة التعيين
    if data == "action_reset":
        game["board"] = [[" " for _ in range(3)] for _ in range(3)]
        game["turn"] = "X"
        game["player_x"] = {"id": user.id, "name": user.first_name}
        game["player_o"] = None
        game["status"] = "waiting_for_opponent"
        
        text = (
            "╔═══════════════════════╗\n"
            "     🔄 **تم إعادة تعيين الساحة** 🔄     \n"
            "╚═══════════════════════╝\n\n"
            f"👑 **اللاعب الأول (X):** {game['player_x']['name']} (أبو مِيلاف)\n"
            "⏳ **اللاعب الثاني (O):** في انتظار انضمام الخصم...\n\n"
            "👇 **اضغط على الزر أدناه للانضمام!**"
        )
        keyboard = [
            [InlineKeyboardButton("🎮 انضم الآن كـ (أم مِيلاف ⭕)", callback_data="action_join")],
            [InlineKeyboardButton("🔄 بدء جلسة جديدة", callback_data="action_reset")]
        ]
        await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    # 3. مربعات اللعب داخل الشبكة
    if data.startswith("cell_"):
        if game["status"] == "waiting_for_opponent":
            await query.answer("⏳ يجب أن ينضم صديقك أولاً كـ (أم مِيلاف) لتبدأ المعركة!", show_alert=True)
            return
            
        # التحقق من دور اللاعب الصحيح
        is_x_player = game["player_x"] and user.id == game["player_x"]["id"]
        is_o_player = game["player_o"] and user.id == game["player_o"]["id"]
        
        if not is_x_player and not is_o_player:
            # إذا دخل شخص ثالث متفرج
            await query.answer("👀 أنت متفرج في هذه المعركة، انتظر انتهاء الجولة أو ابدأ لعبتك الخاصة بـ /start!", show_alert=True)
            return
            
        if game["turn"] == "X" and not is_x_player:
            await query.answer("⏳ ليس دورك الآن، انتظر دور (أبو مِيلاف)!", show_alert=True)
            return
            
        if game["turn"] == "O" and not is_o_player:
            await query.answer("⏳ ليس دورك الآن، انتظر دور (أم مِيلاف)!", show_alert=True)
            return

        _, r, c = data.split("_")
        r, c = int(r), int(c)
        board = game["board"]
        
        if board[r][c] == " ":
            board[r][c] = game["turn"]
            
            # تبديل الدور
            if game["turn"] == "X":
                game["turn"] = "O"
                next_name = f"{game['player_o']['name']} (أم مِيلاف ⭕)"
            else:
                game["turn"] = "X"
                next_name = f"{game['player_x']['name']} (أبو مِيلاف ❌)"
                
            text = (
                "╔═══════════════════════╗\n"
                "     ⚔️ **معركة XO ARENA جارية** ⚔️     \n"
                "╚═══════════════════════╝\n\n"
                f"❌ **أبو مِيلاف:** {game['player_x']['name']}\n"
                f"⭕ **أم مِيلاف:** {game['player_o']['name']}\n\n"
                f"⚡ **دور اللاعب:** {next_name}"
            )
            
            keyboard = get_fancy_board(board, game['player_x']['name'], game['player_o']['name'], game["turn"])
            await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await query.answer("⚠️ هذا المربع محجوز مسبقاً يا بطل، اختر غيره!", show_alert=True)

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("خطأ: لم يتم العثور على توكن البوت في متغيرات البيئة!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("XO ARENA - Pro Multiplayer Mode Running...")
    app.run_polling()

if __name__ == '__main__':
    main()
