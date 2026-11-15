import telebot
from telebot import types

TOKEN = '9269612259:AAEXjbQ6mr0T3kIQn0648ot0_d3xMoMoM98'
bot = telebot.TeleBot(TOKEN)

games = {}

def init_board():
    return [[' ' for _ in range(3)] for _ in range(3)]

def get_keyboard(board, game_active=True):
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    for r in range(3):
        row_buttons = []
        for c in range(3):
            cell = board[r][c]
            if cell == ' ':
                text = '▫️'
            elif cell == 'X':
                text = '❌'
            else:
                text = '⭕'
            
            cb_data = f"cell_{r}_{c}" if game_active else "none"
            row_buttons.append(types.InlineKeyboardButton(text, callback_data=cb_data))
        keyboard.add(*row_buttons)
    
    if not game_active:
        keyboard.add(types.InlineKeyboardButton("🔄 جولة جديدة", callback_data="restart_game"))
        
    return keyboard

def get_score_text(scores, turn_name):
    abu_score = scores['ابو ميلاف']
    um_score = scores['ام ميلاف']
    draws = scores['draws']
    
    return (
        "🎮 **لوحة التحدي الكبرى (X-O)**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📊 ** لوحة النتيجة الحالية:**\n"
        f"👑 أبو مِيلاف: **{abu_score}**  |  🎯 أم مِيلاف: **{um_score}**  |  🤝 تعادل: **{draws}**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"دور اللاعب الحالي: **{turn_name}**"
    )

@bot.message_handler(commands=['start', 'play', 'xo'])
def start_game(message):
    chat_id = message.chat.id
    
    # إذا كانت المحادثة جديدة، ننشئ سجلاً للنقاط، وإذا كانت موجودة نحافظ على النقاط السابقة!
    if chat_id not in games:
        games[chat_id] = {
            'scores': {'ابو ميلاف': 0, 'ام ميلاف': 0, 'draws': 0}
        }
    
    games[chat_id]['board'] = init_board()
    games[chat_id]['turn'] = 'ابو ميلاف'
    games[chat_id]['status'] = 'playing'
    
    bot.send_message(
        chat_id, 
        get_score_text(games[chat_id]['scores'], "أبو مِيلاف 👑 (❌)"),
        reply_markup=get_keyboard(games[chat_id]['board'], True),
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    data = call.data
    
    if chat_id not in games and data != "restart_game":
        bot.answer_callback_query(call.id, "انتهت الجولة، اكتب /xo لبدء تحدٍ جديد.")
        return

    game = games[chat_id]

    if data == "restart_game":
        game['board'] = init_board()
        game['turn'] = 'ابو ميلاف'
        game['status'] = 'playing'
        
        bot.edit_message_text(
            get_score_text(game['scores'], "أبو مِيلاف 👑 (❌)"),
            chat_id,
            call.message.message_id,
            reply_markup=get_keyboard(game['board'], True),
            parse_mode="Markdown"
        )
        return

    if data.startswith("cell_") and game['status'] == 'playing':
        _, r, c = data.split('_')
        r, c = int(r), int(c)
        
        current_turn = game['turn']

        if game['board'][r][c] == ' ':
            symbol = 'X' if current_turn == 'ابو ميلاف' else 'O'
            game['board'][r][c] = symbol
            
            winner = check_winner(game['board'])
            if winner:
                game['status'] = 'ended'
                if current_turn == 'ابو ميلاف':
                    game['scores']['ابو ميلاف'] += 1
                    winner_display = "أبو مِيلاف 👑"
                else:
                    game['scores']['ام ميلاف'] += 1
                    winner_display = "أم مِيلاف 🎯"
                
                abu_s = game['scores']['ابو ميلاف']
                um_s = game['scores']['ام ميلاف']
                draw_s = game['scores']['draws']

                bot.edit_message_text(
                    f"🏆 **انتهت الجولة بفوز: {winner_display}!** 🎉\n\n"
                    "📊 **النتيجة الكلية حتى الآن:**\n"
                    f"👑 أبو مِيلاف: **{abu_s}**  |  🎯 أم مِيلاف: **{um_s}**  |  🤝 تعادل: **{draw_s}**\n\n"
                    "اضغط أدناه للجولة التالية:",
                    chat_id,
                    call.message.message_id,
                    reply_markup=get_keyboard(game['board'], False),
                    parse_mode="Markdown"
                )
                return
            
            if all(cell != ' ' for row in game['board'] for cell in row):
                game['status'] = 'ended'
                game['scores']['draws'] += 1
                
                abu_s = game['scores']['ابو ميلاف']
                um_s = game['scores']['ام ميلاف']
                draw_s = game['scores']['draws']

                bot.edit_message_text(
                    f"🤝 **تعادل بطولي في هذه الجولة!**\n\n"
                    "📊 **النتيجة الكلية حتى الآن:**\n"
                    f"👑 أبو مِيلاف: **{abu_s}**  |  🎯 أم مِيلاف: **{um_s}**  |  🤝 تعادل: **{draw_s}**\n\n"
                    "اضغط أدناه للجولة التالية:",
                    chat_id,
                    call.message.message_id,
                    reply_markup=get_keyboard(game['board'], False),
                    parse_mode="Markdown"
                )
                return

            # تبديل الدور
            game['turn'] = 'ام ميلاف' if current_turn == 'ابو ميلاف' else 'ابو ميلاف'
            next_name_display = "أبو مِيلاف 👑 (❌)" if game['turn'] == 'ابو ميلاف' else "أم مِيلاف 🎯 (⭕)"
            
            bot.edit_message_text(
                get_score_text(game['scores'], next_name_display),
                chat_id,
                call.message.message_id,
                reply_markup=get_keyboard(game['board'], True),
                parse_mode="Markdown"
            )
        else:
            bot.answer_callback_query(call.id, "هذا المربع محجوز، اختر مكاناً آخر ⚠️")

def check_winner(board):
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] and board[i][0] != ' ':
            return board[i][0]
        if board[0][i] == board[1][i] == board[2][i] and board[0][i] != ' ':
            return board[0][i]
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != ' ':
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != ' ':
        return board[0][2]
    return None

print("البوت يعمل مع نظام النقاط...")
bot.polling()
