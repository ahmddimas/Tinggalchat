from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from database import Database
from config import *

# Database instance
db = Database()

# Conversation states
NAME, AGE, GENDER, BIO, PHOTO, PREF_GENDER, PREF_AGE = range(7)

# ===== HELPER FUNCTIONS =====
def format_profile(user_data):
    """Format user profile untuk ditampilkan"""
    return f"""
👤 **{user_data[2]}**, {user_data[3]} tahun
{'👨' if user_data[4] == GENDER_MALE else '👩'} {user_data[4]}

📝 {user_data[5]}
"""

def get_gender_keyboard():
    """Keyboard untuk pilih gender"""
    keyboard = [
        [InlineKeyboardButton("👨 Pria", callback_data="gender_male")],
        [InlineKeyboardButton("👩 Wanita", callback_data="gender_female")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_browse_keyboard():
    """Keyboard untuk browse profil"""
    keyboard = [
        [
            InlineKeyboardButton("❌ Pass", callback_data="pass"),
            InlineKeyboardButton("💚 Like", callback_data="like")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== COMMAND HANDLERS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /start"""
    user_id = update.effective_user.id
    
    if db.user_exists(user_id):
        await update.message.reply_text(
            "💘 Selamat datang kembali!\n\n"
            "Gunakan:\n"
            "/browse - Cari pasangan\n"
            "/profile - Lihat profil kamu\n"
            "/matches - Lihat match kamu\n"
            "/help - Bantuan"
        )
    else:
        await update.message.reply_text(
            "💘 **Selamat datang di Dating Bot!**\n\n"
            "Bot ini akan membantu kamu menemukan pasangan 💑\n\n"
            "Yuk mulai dengan /register"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /help"""
    help_text = """
📱 **PANDUAN PENGGUNAAN**

🆕 **Untuk User Baru:**
/register - Daftar akun baru

👤 **Profile:**
/profile - Lihat profil kamu
/edit - Edit profil (coming soon)

💑 **Cari Pasangan:**
/browse - Mulai swipe profil
/matches - Lihat daftar match

❓ **Lainnya:**
/help - Panduan ini
/cancel - Batalkan proses

💡 **Cara Pakai:**
1. Register dan isi profil
2. Browse profil orang lain
3. Like yang kamu suka
4. Kalau dia juga like kamu = MATCH! 💕
5. Chat langsung di Telegram
"""
    await update.message.reply_text(help_text)

# ===== REGISTRATION =====
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mulai proses registrasi"""
    user_id = update.effective_user.id
    
    if db.user_exists(user_id):
        await update.message.reply_text("Kamu sudah terdaftar! Gunakan /profile")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "✨ **REGISTRASI AKUN**\n\n"
        "Siapa nama kamu?"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Terima input nama"""
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Berapa umur kamu? (18-60)")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Terima input umur"""
    try:
        age = int(update.message.text)
        if age < MIN_AGE or age > MAX_AGE:
            await update.message.reply_text(f"Umur harus antara {MIN_AGE}-{MAX_AGE} tahun!")
            return AGE
        
        context.user_data['age'] = age
        await update.message.reply_text(
            "Jenis kelamin kamu?",
            reply_markup=get_gender_keyboard()
        )
        return GENDER
    except:
        await update.message.reply_text("Tolong masukkan angka yang valid!")
        return AGE

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Terima pilihan gender"""
    query = update.callback_query
    await query.answer()
    
    gender = GENDER_MALE if query.data == "gender_male" else GENDER_FEMALE
    context.user_data['gender'] = gender
    
    await query.edit_message_text(
        f"✅ {gender}\n\n"
        "Ceritakan sedikit tentang kamu (bio/deskripsi):"
    )
    return BIO

async def get_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Terima bio"""
    bio = update.message.text
    
    if len(bio) > MAX_BIO_LENGTH:
        await update.message.reply_text(f"Bio maksimal {MAX_BIO_LENGTH} karakter!")
        return BIO
    
    context.user_data['bio'] = bio
    await update.message.reply_text(
        "📸 Kirim 1 foto kamu!\n"
        "(Foto profil yang bagus ya 😊)"
    )
    return PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Terima foto"""
    if not update.message.photo:
        await update.message.reply_text("Tolong kirim foto!")
        return PHOTO
    
    photo_id = update.message.photo[-1].file_id
    context.user_data['photo_id'] = photo_id
    
    await update.message.reply_text(
        "Kamu mau cari siapa?",
        reply_markup=get_gender_keyboard()
    )
    return PREF_GENDER

async def get_pref_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Terima preferensi gender"""
    query = update.callback_query
    await query.answer()
    
    pref_gender = GENDER_MALE if query.data == "gender_male" else GENDER_FEMALE
    context.user_data['pref_gender'] = pref_gender
    
    await query.edit_message_text(
        f"✅ Cari: {pref_gender}\n\n"
        "Umur minimal yang kamu cari? (18-60)"
    )
    return PREF_AGE

async def get_pref_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Terima preferensi umur dan selesaikan registrasi"""
    try:
        age_min = int(update.message.text)
        if age_min < MIN_AGE or age_min > MAX_AGE:
            await update.message.reply_text(f"Umur harus antara {MIN_AGE}-{MAX_AGE}!")
            return PREF_AGE
        
        await update.message.reply_text("Umur maksimal? (18-60)")
        context.user_data['pref_age_min'] = age_min
        
        # Next message will be max age
        return await finalize_pref_age(update, context)
        
    except:
        await update.message.reply_text("Tolong masukkan angka yang valid!")
        return PREF_AGE

async def finalize_pref_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finalisasi dan simpan ke database"""
    # Skip this, we'll handle it differently
    pass

# Simplified version - get both min and max in one go
async def get_pref_age_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get age preference"""
    try:
        age_min = int(update.message.text)
        if age_min < MIN_AGE or age_min > MAX_AGE:
            await update.message.reply_text(f"Umur harus antara {MIN_AGE}-{MAX_AGE}!")
            return PREF_AGE
        
        # Set min and max (simplified: max = min + 10)
        context.user_data['pref_age_min'] = age_min
        context.user_data['pref_age_max'] = min(age_min + 15, MAX_AGE)
        
        # Save to database
        user_id = update.effective_user.id
        username = update.effective_user.username or "unknown"
        
        success = db.add_user(
            user_id=user_id,
            username=username,
            name=context.user_data['name'],
            age=context.user_data['age'],
            gender=context.user_data['gender'],
            bio=context.user_data['bio'],
            photo_id=context.user_data['photo_id'],
            pref_gender=context.user_data['pref_gender'],
            pref_age_min=context.user_data['pref_age_min'],
            pref_age_max=context.user_data['pref_age_max']
        )
        
        if success:
            await update.message.reply_text(
                "🎉 **REGISTRASI BERHASIL!**\n\n"
                "Akun kamu sudah aktif!\n\n"
                "Gunakan /browse untuk mulai cari pasangan 💑"
            )
        else:
            await update.message.reply_text("Error menyimpan data. Coba lagi!")
        
        return ConversationHandler.END
        
    except:
        await update.message.reply_text("Tolong masukkan angka yang valid!")
        return PREF_AGE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    await update.message.reply_text("❌ Proses dibatalkan.")
    return ConversationHandler.END

# ===== PROFILE =====
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan profil user"""
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    if not user_data:
        await update.message.reply_text("Kamu belum register! Gunakan /register")
        return
    
    stats = db.get_stats(user_id)
    
    profile_text = f"""
👤 **PROFIL KAMU**

{format_profile(user_data)}

🎯 **Preferensi:**
Mencari: {user_data[7]}
Umur: {user_data[8]}-{user_data[9]} tahun

📊 **Statistik:**
💚 Like diberikan: {stats['likes_given']}
💖 Like diterima: {stats['likes_received']}
💑 Total match: {stats['matches']}
"""
    
    await update.message.reply_photo(
        photo=user_data[6],
        caption=profile_text
    )

# ===== BROWSE =====
async def browse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mulai browse profil"""
    user_id = update.effective_user.id
    
    if not db.user_exists(user_id):
        await update.message.reply_text("Kamu belum register! Gunakan /register")
        return
    
    next_profile = db.get_next_profile(user_id)
    
    if not next_profile:
        await update.message.reply_text(
            "😔 Tidak ada profil baru saat ini.\n\n"
            "Coba lagi nanti atau ubah preferensi kamu!"
        )
        return
    
    # Save current viewing profile
    context.user_data['viewing_profile'] = next_profile[0]
    
    await update.message.reply_photo(
        photo=next_profile[6],
        caption=format_profile(next_profile),
        reply_markup=get_browse_keyboard()
    )

async def handle_swipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle like/pass"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    action = query.data
    target_user = context.user_data.get('viewing_profile')
    
    if not target_user:
        await query.edit_message_caption("Error! Gunakan /browse lagi.")
        return
    
    if action == "like":
        is_match = db.add_like(user_id, target_user)
        
        if is_match:
            # IT'S A MATCH!
            target_data = db.get_user(target_user)
            await query.edit_message_caption(
                f"💕 **IT'S A MATCH!**\n\n"
                f"Kamu dan {target_data[2]} saling menyukai!\n\n"
                f"Mulai chat: @{target_data[1] or 'user'}\n\n"
                "Gunakan /browse untuk lanjut"
            )
        else:
            await query.edit_message_caption(
                "💚 Liked!\n\n"
                "Gunakan /browse untuk profil berikutnya"
            )
    
    elif action == "pass":
        db.add_pass(user_id, target_user)
        await query.edit_message_caption(
            "➡️ Skipped!\n\n"
            "Gunakan /browse untuk profil berikutnya"
        )

# ===== MATCHES =====
async def matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan daftar match"""
    user_id = update.effective_user.id
    
    if not db.user_exists(user_id):
        await update.message.reply_text("Kamu belum register! Gunakan /register")
        return
    
    matches_list = db.get_matches(user_id)
    
    if not matches_list:
        await update.message.reply_text(
            "😔 Belum ada match.\n\n"
            "Gunakan /browse untuk cari pasangan!"
        )
        return
    
    text = "💑 **DAFTAR MATCH KAMU**\n\n"
    for match in matches_list:
        text += f"👤 {match[2]}, {match[3]} tahun - @{match[1] or 'user'}\n"
    
    text += f"\n📊 Total: {len(matches_list)} match"
    
    await update.message.reply_text(text)

# ===== MAIN =====
def main():
    """Start the bot"""
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Conversation handler untuk registration
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('register', register)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            GENDER: [CallbackQueryHandler(get_gender)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bio)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
            PREF_GENDER: [CallbackQueryHandler(get_pref_gender)],
            PREF_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pref_age_range)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Add handlers
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('profile', profile))
    app.add_handler(CommandHandler('browse', browse))
    app.add_handler(CommandHandler('matches', matches))
    app.add_handler(CallbackQueryHandler(handle_swipe, pattern='^(like|pass)$'))
    
    # Start bot
    print("🤖 Bot started! Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == '__main__':
    main()
