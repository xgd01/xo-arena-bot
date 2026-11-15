def text(g):
    s = (
        "💕 XO ARENA 💕\n"
        "━━━━━━━━━━━━\n"
        "❌ X: أبو مِيلاف\n"
        "⭕ O: أم مِيلاف\n\n"
    )

    if not g["o"]:
        return s + "بانتظار أم مِيلاف للانضمام 🥰"

    if g["status"] == "playing":
        p = "أبو مِيلاف" if g["turn"] == "X" else "أم مِيلاف"
        return s + f"🎮 الدور الآن: {p}"

    if g["status"] == "draw":
        return s + "🤝 تعادل! الحب فاز ❤️"

    winner = "أبو مِيلاف" if g["status"] == "X" else "أم مِيلاف"
    return s + f"🏆 الفائز: {winner} ❤️"
