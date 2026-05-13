# bot.py - Main Telegram bot for Daily Bible Reader
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)
from telegram.error import Conflict

from config import READING_PLANS, BIBLE_TRANSLATIONS, MESSAGES
from database import db
from reading_plans import reading_plans
from bible_api import bible_api
from menu import Menu

from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

CHOOSING_LANGUAGE, CHOOSING_PLAN, CHOOSING_TRANSLATION, CHOOSING_TIMES = range(4)


def _get_chat_id(update: Update):
    if update.effective_chat:
        return update.effective_chat.id
    return None


async def _send_daily_reading_messages(
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    user_data: dict,
    include_header: bool = False,
    forced_plan_day: int | None = None,
    forced_passages: list | None = None,
):
    """Send today's reading and attach share + chapter checkbox buttons."""
    user_id = user_data['user_id']
    lang = user_data['language']
    plan_day = forced_plan_day if forced_plan_day is not None else user_data['current_day']

    if forced_passages is None:
        reading = reading_plans.get_todays_reading(user_data['plan_name'], plan_day)
        logger.info('Reading for %s (day %s): %s', user_id, plan_day, reading)

        if not reading:
            msg = (
                "Congratulations! You've finished your reading plan."
                if lang == 'en'
                else "Congratulations! You've finished your reading plan."
            )
            await context.bot.send_message(chat_id=chat_id, text=msg)
            return {'sent': False, 'plan_day': plan_day, 'summary': {'completed': 0, 'total': 0}}
        passages = reading.get('passages', [])
    else:
        passages = forced_passages

    if include_header:
        header = ('Daily reminder\n\n' if lang == 'en' else 'Reminder\n\n')
        await context.bot.send_message(chat_id=chat_id, text=header)

    share_label = 'Share'
    favorite_label = 'Favorite'
    mark_label = 'Mark Read'
    done_label = 'Marked'

    for passage in passages:
        book = passage['book']
        chapters = passage['chapters']
        for chapter in chapters:
            db.upsert_daily_chapter(user_id, plan_day, book, chapter)
            db.increment_daily_chapter_send(user_id, plan_day, book, chapter)
            chapter_state = db.get_daily_chapter(user_id, plan_day, book, chapter)

            text = bible_api.get_text(book, chapter, user_data['translation'])
            chapter_btn = done_label if chapter_state and chapter_state['completed'] else mark_label
            chapter_id = chapter_state['id'] if chapter_state else 0

            keyboard = [[
                InlineKeyboardButton(share_label, callback_data=f'share_{book}_{chapter}'),
                InlineKeyboardButton(favorite_label, callback_data=f'fav_{book}_{chapter}'),
                InlineKeyboardButton(chapter_btn, callback_data=f'done_{chapter_id}'),
            ]]

            await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

    summary = db.get_day_completion_summary(user_id, plan_day)
    return {'sent': True, 'plan_day': plan_day, 'summary': summary}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Keep /start idempotent: clear transient settings/onboarding flags.
    context.user_data.pop('settings_action', None)
    context.user_data.pop('notification_times', None)
    existing_user = db.get_user(user.id)

    if existing_user:
        lang = existing_user.get('language', 'en')
        welcome_back = "Welcome back!" if lang == 'en' else "Welcome back!"
        await update.message.reply_text(welcome_back, reply_markup=Menu.get_main_menu(lang))
        return ConversationHandler.END

    keyboard = [["English", "Amharic"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(MESSAGES['choose_language']['en'], reply_markup=reply_markup)
    return CHOOSING_LANGUAGE


async def language_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    lang = 'am' if ('amharic' in choice.lower()) else 'en'
    context.user_data['language'] = lang

    if context.user_data.get('settings_action') == 'set_lang':
        user_id = update.effective_user.id
        db.update_user_language(user_id, lang)
        context.user_data.pop('settings_action', None)
        msg = 'Language updated.'
        await update.message.reply_text(msg, reply_markup=Menu.get_main_menu(lang))
        return ConversationHandler.END

    await update.message.reply_text(
        MESSAGES['welcome'][lang].format(name=update.effective_user.first_name),
        reply_markup=Menu.get_plan_menu(lang),
    )
    return CHOOSING_PLAN


async def plan_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plan_choice = update.message.text
    lang = context.user_data.get('language', 'en')

    plan_key = 'bible_in_one_year'
    for key, val in READING_PLANS.items():
        if val['name'][lang] in plan_choice:
            plan_key = key
            break

    context.user_data['plan'] = plan_key

    if context.user_data.get('settings_action') == 'set_plan':
        user_id = update.effective_user.id
        db.update_user_plan(user_id, plan_key)
        context.user_data.pop('settings_action', None)
        await update.message.reply_text(
            'Plan updated. Your progress day was kept.',
            reply_markup=Menu.get_main_menu(lang),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        MESSAGES['choose_translation'][lang],
        reply_markup=Menu.get_translation_menu(lang),
    )
    return CHOOSING_TRANSLATION


async def translation_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    translation = 'ESV'

    if 'AMH' in choice or 'Amharic' in choice:
        translation = 'AMH'
    elif 'KJV' in choice:
        translation = 'KJV'
    elif 'NIV' in choice:
        translation = 'NIV'

    context.user_data['translation'] = translation
    lang = context.user_data.get('language', 'en')

    if context.user_data.get('settings_action') == 'set_trans':
        user_id = update.effective_user.id
        db.update_user_translation(user_id, translation)
        context.user_data.pop('settings_action', None)
        await update.message.reply_text(
            'Translation updated.',
            reply_markup=Menu.get_main_menu(lang),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        MESSAGES['choose_times_1'][lang],
        reply_markup=Menu.get_time_selection_menu(),
    )
    return CHOOSING_TIMES


async def times_chosen_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    time_selected = query.data.split('_', 1)[1]
    user_times = context.user_data.get('notification_times', [])

    if len(user_times) == 0:
        user_times.append(time_selected)
        context.user_data['notification_times'] = user_times
        lang = context.user_data.get('language', 'en')

        await query.message.reply_text(
            MESSAGES['choose_times_2'][lang],
            reply_markup=Menu.get_time_selection_menu(selected_times=user_times),
        )
        return CHOOSING_TIMES

    if time_selected in user_times:
        lang = context.user_data.get('language', 'en')
        msg = 'Please choose a different second time.' if lang == 'en' else 'Please choose a different second time.'
        await query.message.reply_text(
            msg,
            reply_markup=Menu.get_time_selection_menu(selected_times=user_times),
        )
        return CHOOSING_TIMES

    user_times.append(time_selected)

    user = update.effective_user
    lang = context.user_data.get('language', 'en')
    times_str = ','.join(user_times)
    is_settings_times = context.user_data.get('settings_action') == 'set_times'

    existing = db.get_user(user.id)
    if existing:
        db.update_notification_times(user.id, times_str)
    else:
        db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            plan_name=context.user_data['plan'],
            translation=context.user_data['translation'],
            language=lang,
        )
        db.update_notification_times(user.id, times_str)

    user_after = db.get_user(user.id)
    if not user_after:
        await query.message.reply_text('Could not load updated settings right now.')
        return ConversationHandler.END

    plan_name = READING_PLANS[user_after['plan_name']]['name'][user_after['language']]
    trans_name = BIBLE_TRANSLATIONS.get(user_after['translation'], user_after['translation'])

    await query.message.reply_text(
        (
            f'Notification times updated.\n\nPlan: {plan_name}\nTranslation: {trans_name}'
            if is_settings_times else
            MESSAGES['registration_complete'][user_after['language']].format(plan=plan_name, translation=trans_name)
        ),
        reply_markup=Menu.get_main_menu(user_after['language']),
    )

    context.user_data.pop('settings_action', None)

    if not is_settings_times and user_after:
        await show_todays_reading(update, context, user_after)

    return ConversationHandler.END


async def handle_menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if not user_data:
        await start(update, context)
        return

    lang = user_data['language']

    text_l = text.lower()

    if text.startswith("📖") or "today" in text_l or "reading" in text_l:
        await show_todays_reading(update, context, user_data)
    elif text.startswith("👤") or "profile" in text_l:
        await show_profile(update, context, user_data)
    elif text.startswith("📊") or "progress" in text_l:
        await show_progress(update, context, user_data)
    elif "favorite" in text_l:
        await favorites_command(update, context)
    elif "history" in text_l:
        await history_command(update, context)
    elif text.startswith("⚙️") or "settings" in text_l:
        await update.message.reply_text(
            "Settings",
            reply_markup=Menu.get_settings_menu(lang),
        )
    elif text.startswith("🔄") or "restart" in text_l:
        msg = (
            'Are you sure you want to restart your plan from Day 1? This cannot be undone.'
            if lang == 'en' else
            'Are you sure you want to restart your plan from Day 1? This cannot be undone.'
        )
        await update.message.reply_text(msg, reply_markup=Menu.get_yes_no_menu(lang, 'restart'))
    elif text.startswith("📤") or "share bot" in text_l:
        bot_link = f'https://t.me/{context.bot.username}'
        await update.message.reply_text(bot_link)
    elif text.startswith("❓") or "help" in text_l:
        await update.message.reply_text(Menu.get_help_text(lang), parse_mode='Markdown')


async def show_todays_reading(update: Update, context: ContextTypes.DEFAULT_TYPE, user_data):
    user_id = user_data['user_id']
    lang = user_data['language']
    chat_id = _get_chat_id(update)

    if not chat_id:
        return

    if db.get_todays_reading(user_id):
        msg = "You've already completed today's reading! Keep it up!"
        await context.bot.send_message(chat_id=chat_id, text=msg)
        return

    try:
        result = await _send_daily_reading_messages(context, chat_id, user_data, include_header=False)
        if result['sent']:
            s = result['summary']
            msg = (
                f'Mark each chapter as read to count progress.\nCompleted: {s["completed"]}/{s["total"]}'
                if lang == 'en' else
                f'Mark each chapter as read to count progress.\nCompleted: {s["completed"]}/{s["total"]}'
            )
            await context.bot.send_message(chat_id=chat_id, text=msg)
    except Exception as e:
        logger.error('Error in show_todays_reading for user %s: %s', user_id, e)
        err = (
            'Sorry, an error occurred while fetching your reading. Please try again or /start.'
            if lang == 'en' else
            'Sorry, an error occurred while fetching your reading. Please try again or /start.'
        )
        await context.bot.send_message(chat_id=chat_id, text=err)


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, user_data):
    lang = user_data['language']
    user_id = user_data['user_id']

    achievements = db.get_achievements(user_id)
    stats = db.get_user_stats(user_id)
    ach_list = ''
    if not achievements:
        ach_list = 'No achievements yet.'
    else:
        for ach in achievements:
            ach_list += f'- {ach[0]} ({ach[1]})\n'

    text = (
        f"**Profile: {user_data['first_name']}**\n\n"
        f"Current Streak: {user_data['streak']} days\n"
        f"Longest Streak: {user_data['max_streak']} days\n"
        f"Plan: {READING_PLANS[user_data['plan_name']]['name'][lang]}\n"
        f"Translation: {BIBLE_TRANSLATIONS.get(user_data['translation'], user_data['translation'])}\n"
        f"Completed Days: {stats['completed_days']}\n"
        f"Favorite Readings: {stats['favorites_count']}\n\n"
        f"**Achievements:**\n{ach_list}"
    )

    await update.message.reply_text(text, parse_mode='Markdown')


async def show_progress(update: Update, context: ContextTypes.DEFAULT_TYPE, user_data):
    lang = user_data['language']
    total_days = READING_PLANS[user_data['plan_name']]['total_days']
    stats = db.get_user_stats(user_data['user_id'])
    completed_days = stats['completed_days']
    percentage = (completed_days / total_days) * 100

    bars = 15
    filled = int((completed_days / total_days) * bars)
    bar = '#' * filled + '-' * (bars - filled)

    text = (
        f"**Reading Progress**\n\n"
        f"Plan: {READING_PLANS[user_data['plan_name']]['name'][lang]}\n"
        f"Completed Days: {completed_days} of {total_days}\n"
        f"Next Reading Day: {min(user_data['current_day'], total_days)} of {total_days}\n"
        f"Current Streak: {user_data['streak']} days\n"
        f"Longest Streak: {user_data['max_streak']} days\n"
        f"Most Read Book: {stats['most_read_book']}\n"
        f"Achievements: {stats['achievements_count']}\n"
        f"Completion: {percentage:.1f}%\n\n"
        f"{bar}"
    )

    await update.message.reply_text(text, parse_mode='Markdown')


async def favorites_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show saved favorite chapter readings."""
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if not user_data:
        await start(update, context)
        return

    favorites = db.get_favorites(user_id)
    if not favorites:
        await update.message.reply_text(
            "No favorites saved yet. Use the Favorite button under a reading to save one.",
            reply_markup=Menu.get_main_menu(user_data['language']),
        )
        return

    lines = ["**Favorite Readings**\n"]
    for index, favorite in enumerate(favorites[:10], 1):
        book, chapter, verse, text = favorite
        reference = f"{book} {chapter}" if not verse else f"{book} {chapter}:{verse}"
        preview = (text or '').replace('\n', ' ')
        if len(preview) > 120:
            preview = preview[:117] + '...'
        lines.append(f"{index}. **{reference}**\n{preview}")

    await update.message.reply_text(
        "\n\n".join(lines),
        parse_mode='Markdown',
        reply_markup=Menu.get_main_menu(user_data['language']),
    )


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show recent completed reading days."""
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if not user_data:
        await start(update, context)
        return

    history = db.get_reading_history(user_id)
    if not history:
        await update.message.reply_text(
            "No completed readings yet. Use Today's Reading and mark the chapters read.",
            reply_markup=Menu.get_main_menu(user_data['language']),
        )
        return

    lines = ["**Reading History**\n"]
    for index, row in enumerate(history, 1):
        lines.append(f"{index}. {row['date']} - {row['book']} {row['chapter']}")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode='Markdown',
        reply_markup=Menu.get_main_menu(user_data['language']),
    )


async def achievements_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show earned achievements."""
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if not user_data:
        await start(update, context)
        return

    achievements = db.get_achievements(user_id)
    if not achievements:
        await update.message.reply_text(
            "No achievements yet. Complete readings to unlock them.",
            reply_markup=Menu.get_main_menu(user_data['language']),
        )
        return

    lines = ["**Achievements**\n"]
    for index, achievement in enumerate(achievements, 1):
        lines.append(f"{index}. {achievement['achievement_id']} - {achievement['date_earned']}")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode='Markdown',
        reply_markup=Menu.get_main_menu(user_data['language']),
    )


async def check_achievements(update, context, user_id, streak, total_reads, lang):
    awards = []

    if streak == 7:
        awards.append('7-Day Flame')
    elif streak == 30:
        awards.append('Monthly Star')

    if total_reads == 1:
        awards.append('First Step')
    elif total_reads == 100:
        awards.append('Century Club')

    chat_id = _get_chat_id(update)
    if not chat_id:
        return

    for award in awards:
        db.add_achievement(user_id, award)
        celebration = 'New achievement unlocked!\n\n'
        await context.bot.send_message(chat_id=chat_id, text=celebration + award)


async def handle_chapter_done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    lang = user_data['language'] if user_data else 'en'

    try:
        chapter_id = int(query.data.split('_', 1)[1])
    except Exception:
        return

    chapter_data, changed = db.mark_chapter_completed(chapter_id, user_id)
    if not chapter_data:
        return

    share_label = 'Share'
    favorite_label = 'Favorite'
    done_label = 'Marked'

    keyboard = [[
        InlineKeyboardButton(share_label, callback_data=f"share_{chapter_data['book']}_{chapter_data['chapter']}"),
        InlineKeyboardButton(favorite_label, callback_data=f"fav_{chapter_data['book']}_{chapter_data['chapter']}"),
        InlineKeyboardButton(done_label, callback_data=f'done_{chapter_id}'),
    ]]
    try:
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        pass

    summary = db.get_day_completion_summary(user_id, chapter_data['plan_day'])

    if changed:
        completed = db.complete_day_if_ready(user_id, chapter_data['plan_day'])
        if completed.get('completed'):
            streak = completed['streak']
            await check_achievements(update, context, user_id, streak, chapter_data['plan_day'], lang)
            done_msg = (
                f'Day complete. Streak: {streak} days'
                if lang == 'en'
                else f'Day complete. Streak: {streak} days'
            )
            await context.bot.send_message(chat_id=update.effective_chat.id, text=done_msg)
            return

    status_msg = (
        f"Today's completion: {summary['completed']}/{summary['total']}"
        if lang == 'en'
        else f"Today's completion: {summary['completed']}/{summary['total']}"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=status_msg)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Cancelled.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def reset_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    lang = user_data['language'] if user_data else 'en'

    db.delete_user(user_id)

    msg = (
        'Your account has been completely deleted.\n\nSend /start to register again.'
        if lang == 'en'
        else 'Your account has been completely deleted.\n\nSend /start to register again.'
    )
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())


async def settings_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    lang = user_data['language'] if user_data else 'en'

    context.user_data['language'] = lang
    if user_data:
        context.user_data['plan'] = user_data.get('plan_name', 'bible_in_one_year')

    if data == 'set_lang':
        context.user_data['settings_action'] = 'set_lang'
        keyboard = [["English", "Amharic"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await query.message.reply_text(MESSAGES['choose_language'][lang], reply_markup=reply_markup)
        return CHOOSING_LANGUAGE

    if data == 'set_plan':
        context.user_data['settings_action'] = 'set_plan'
        await query.message.reply_text(
            MESSAGES['welcome'][lang].format(name=update.effective_user.first_name),
            reply_markup=Menu.get_plan_menu(lang),
        )
        return CHOOSING_PLAN

    if data == 'set_trans':
        context.user_data['settings_action'] = 'set_trans'
        if 'plan' not in context.user_data:
            context.user_data['plan'] = 'bible_in_one_year'
        await query.message.reply_text(
            MESSAGES['choose_translation'][lang],
            reply_markup=Menu.get_translation_menu(lang),
        )
        return CHOOSING_TRANSLATION

    if data == 'set_times':
        context.user_data['settings_action'] = 'set_times'
        context.user_data['notification_times'] = []
        await query.message.reply_text(
            MESSAGES['choose_times_1'][lang],
            reply_markup=Menu.get_time_selection_menu(),
        )
        return CHOOSING_TIMES


async def handle_share_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        _, book, chapter = query.data.split('_', 2)
        user = db.get_user(update.effective_user.id)
        lang = user['language'] if user else 'en'
        translation = user['translation'] if user else 'ESV'

        chapter_text = bible_api.get_text(book, chapter, translation)
        bot_link = f'https://t.me/{context.bot.username}'
        share_message = (
            f'{chapter_text}\n\nRead with Daily Bible Bot: {bot_link}'
            )
        # Send directly in chat so user can forward/share without extra URL button.
        await query.message.reply_text(share_message[:4000])
    except Exception as e:
        logger.error('Share callback error: %s', e)


async def handle_favorite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        _, book, chapter = query.data.split('_', 2)
        user_id = update.effective_user.id
        user = db.get_user(user_id)
        translation = user['translation'] if user else 'ESV'
        chapter_text = bible_api.get_text(book, chapter, translation)

        db.add_favorite(user_id, book, int(chapter), 0, chapter_text)
        await query.message.reply_text(f"Saved favorite: {book} {chapter}")
    except Exception as e:
        logger.error('Favorite callback error: %s', e)
        await query.message.reply_text("Sorry, I couldn't save that favorite.")


async def handle_restart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    lang = user_data['language'] if user_data else 'en'

    if data == 'restart_yes':
        db.reset_user_progress(user_id)
        msg = 'Plan restarted from Day 1.' if lang == 'en' else 'Plan restarted from Day 1.'
        await query.message.edit_text(msg)
    else:
        msg = 'Restart cancelled.' if lang == 'en' else 'Restart cancelled.'
        await query.message.edit_text(msg)


async def check_notifications(context: ContextTypes.DEFAULT_TYPE):
    """Send reminders at configured times (EAT timezone)."""
    import pytz

    eat_tz = pytz.timezone('Africa/Addis_Ababa')
    now_eat = datetime.now(eat_tz)
    now_str = now_eat.strftime('%H:00')
    logger.info('Checking notifications for %s EAT (%s)', now_str, now_eat)

    users_to_notify = db.get_users_with_notification_time(now_str)

    for user in users_to_notify:
        try:
            full_user = db.get_user(user['user_id'])
            if not full_user:
                continue

            todays = db.get_todays_passages(full_user['user_id'])
            if todays:
                # Always resend the same day's word at each scheduled time.
                await _send_daily_reading_messages(
                    context,
                    chat_id=full_user['user_id'],
                    user_data=full_user,
                    include_header=True,
                    forced_plan_day=todays['plan_day'],
                    forced_passages=todays['passages'],
                )
                continue

            await _send_daily_reading_messages(
                context,
                chat_id=full_user['user_id'],
                user_data=full_user,
                include_header=True,
            )
        except Exception as e:
            logger.error('Error sending notification to %s: %s', user['user_id'], e)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = db.get_user(update.effective_user.id)
    lang = user['language'] if user else 'en'
    await update.message.reply_text(Menu.get_help_text(lang), parse_mode='Markdown')


async def post_init(application: Application):
    """Ensure polling mode is cleanly initialized on Telegram side."""
    use_webhook = os.getenv('USE_WEBHOOK', 'false').lower() == 'true'
    if use_webhook:
        return
    try:
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info('Webhook cleared and pending updates dropped before polling start.')
    except Exception as e:
        logger.warning('Could not clear webhook before polling: %s', e)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle known runtime errors more gracefully."""
    if isinstance(context.error, Conflict):
        logger.error(
            'Telegram Conflict: another bot instance is using getUpdates. '
            'Ensure only one polling instance is running.'
        )
        return
    logger.exception('Unhandled exception in bot update loop', exc_info=context.error)


def enable_webhook_health_routes():
    """Patch PTB webhook app to expose root health endpoints for Render checks."""
    try:
        import tornado.web
        import telegram.ext._utils.webhookhandler as wh

        class HealthHandler(tornado.web.RequestHandler):
            def get(self):
                self.set_status(200)
                self.write("Bot is active")

            def head(self):
                self.set_status(200)

        original_cls = wh.WebhookAppClass

        class PatchedWebhookAppClass(original_cls):
            def __init__(self, webhook_path, bot, update_queue, secret_token=None):
                super().__init__(webhook_path, bot, update_queue, secret_token)
                self.add_handlers(
                    r".*$",
                    [
                        (r"/", HealthHandler),
                        (r"/health/?", HealthHandler),
                    ],
                )

        wh.WebhookAppClass = PatchedWebhookAppClass
        logger.info("Webhook health routes enabled for / and /health")
    except Exception as e:
        logger.warning("Failed to patch webhook health routes: %s", e)


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is active')

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def start_dummy_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info('dummy server listening on port %s', port)
    server.serve_forever()


def main():
    token = os.getenv('BOT_TOKEN')
    if not token:
        print('BOT_TOKEN missing!')
        return

    application = (
        Application.builder()
        .token(token)
        .connect_timeout(60)
        .read_timeout(60)
        .post_init(post_init)
        .build()
    )

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CallbackQueryHandler(settings_entry, pattern='^set_'),
        ],
        states={
            CHOOSING_LANGUAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, language_chosen),
                CallbackQueryHandler(settings_entry, pattern='^set_'),
            ],
            CHOOSING_PLAN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, plan_chosen),
                CallbackQueryHandler(settings_entry, pattern='^set_'),
            ],
            CHOOSING_TRANSLATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, translation_chosen),
                CallbackQueryHandler(settings_entry, pattern='^set_'),
            ],
            CHOOSING_TIMES: [
                CallbackQueryHandler(times_chosen_callback, pattern='^time_'),
                CallbackQueryHandler(settings_entry, pattern='^set_'),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)
    # Redundant global route so settings callbacks still work if conversation state is lost.
    application.add_handler(CallbackQueryHandler(settings_entry, pattern='^set_'))
    application.add_handler(CallbackQueryHandler(handle_share_callback, pattern='^share_'))
    application.add_handler(CallbackQueryHandler(handle_favorite_callback, pattern='^fav_'))
    application.add_handler(CallbackQueryHandler(handle_chapter_done_callback, pattern='^done_'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_click))
    application.add_handler(CallbackQueryHandler(handle_restart_callback, pattern='^restart_'))

    job_queue = application.job_queue
    job_queue.run_repeating(check_notifications, interval=3600, first=10)

    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('reset', reset_user))
    application.add_handler(CommandHandler('favorites', favorites_command))
    application.add_handler(CommandHandler('history', history_command))
    application.add_handler(CommandHandler('achievements', achievements_command))
    application.add_error_handler(error_handler)

    port = int(os.getenv('PORT', 8080))
    render_url = (os.getenv('RENDER_EXTERNAL_URL') or '').strip()
    webhook_base = (os.getenv('WEBHOOK_BASE_URL') or render_url).strip()
    use_webhook = (
        (os.getenv('USE_WEBHOOK', 'false').lower() == 'true')
        and bool(webhook_base)
    )

    if use_webhook:
        enable_webhook_health_routes()
        webhook_path = (os.getenv('WEBHOOK_PATH') or token).strip('/')
        webhook_url = f"{webhook_base.rstrip('/')}/{webhook_path}"
        print('Bible Bot is running in webhook mode...')
        application.run_webhook(
            listen='0.0.0.0',
            port=port,
            url_path=webhook_path,
            webhook_url=webhook_url,
            drop_pending_updates=True,
        )
    else:
        allow_polling = os.getenv('ALLOW_POLLING', 'false').lower() == 'true'
        if not allow_polling:
            raise RuntimeError(
                'Polling is disabled. Set USE_WEBHOOK=true or ALLOW_POLLING=true to run.'
            )
        logger.info(
            'Starting in polling mode with dummy HTTP health server. '
            'Set USE_WEBHOOK=true to enable webhook mode.'
        )
        print('Bible Bot is running in polling mode...')
        threading.Thread(target=start_dummy_server, daemon=True).start()
        application.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()
