# ==========================================
# برآورد بتن سقف
# ==========================================

ROOF_TYPES = {
    "fa": [
        ("تیرچه یونولیتی", "roof_0"),
        ("تیرچه سفالی", "roof_1"),
        ("تیرچه دوبل", "roof_2"),
        ("کرومیت", "roof_3"),
        ("کامپوزیت", "roof_4"),
        ("عرشه فولادی", "roof_5"),
        ("دال بتنی", "roof_6"),
        ("وافل", "roof_7"),
    ],

    "en": [
        ("Block & Joist (EPS)", "roof_0"),
        ("Clay Block & Joist", "roof_1"),
        ("Double Joist", "roof_2"),
        ("Kromit", "roof_3"),
        ("Composite", "roof_4"),
        ("Steel Deck", "roof_5"),
        ("Concrete Slab", "roof_6"),
        ("Waffle", "roof_7"),
    ]
}


ROOF_COEFFICIENTS = {
    0: 0.18,
    1: 0.20,
    2: 0.23,
    3: 0.18,
    4: 0.15,
    5: 0.15,
    6: 0.20,
    7: 0.20,
}


async def start_concrete_estimate(update, context):

    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("language", "fa")

    keyboard = []

    for name, callback in ROOF_TYPES[lang]:
        keyboard.append([
            InlineKeyboardButton(
                name,
                callback_data=callback
            )
        ])

    await query.edit_message_text(
        "🏗️ نوع سقف را انتخاب کنید:" if lang == "fa"
        else "🏗️ Select the roof type:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def roof_selected(update, context):

    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("language", "fa")

    roof_number = int(query.data.split("_")[1])

    context.user_data["roof_number"] = roof_number
    context.user_data["step"] = "roof_area"

    await query.edit_message_text(
        "📐 مساحت سقف را وارد کنید (m²):"
        if lang == "fa"
        else
        "📐 Enter the roof area (m²):"
    )


async def concrete_area_received(update, context):

    if context.user_data.get("step") != "roof_area":
        return

    lang = context.user_data.get("language", "fa")

    try:
        area = float(update.message.text.strip())

        if area <= 0:
            raise ValueError

    except ValueError:

        await update.message.reply_text(
            "❌ لطفاً یک عدد معتبر وارد کنید."
            if lang == "fa"
            else
            "❌ Please enter a valid number."
        )

        return

    roof_number = context.user_data["roof_number"]

    coefficient = ROOF_COEFFICIENTS[roof_number]

    concrete_volume = area * coefficient

    context.user_data["roof_area"] = area
    context.user_data["roof_concrete"] = concrete_volume
    context.user_data["step"] = None

    if lang == "fa":

        text = (
            "🧱 برآورد بتن سقف\n\n"
            f"مساحت سقف: {area:,.2f} m²\n"
            f"ضریب بتن: {coefficient:.2f} m³/m²\n\n"
            f"🔹 حجم بتن سقف: {concrete_volume:,.2f} m³"
        )

    else:

        text = (
            "🧱 Roof Concrete Estimate\n\n"
            f"Roof area: {area:,.2f} m²\n"
            f"Concrete coefficient: {coefficient:.2f} m³/m²\n\n"
            f"🔹 Roof concrete: {concrete_volume:,.2f} m³"
        )

    await update.message.reply_text(text)
