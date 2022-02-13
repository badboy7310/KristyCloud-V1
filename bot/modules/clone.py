import random
import string

from telegram.ext import CommandHandler
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.telegram_helper.message_utils import sendMessage, sendMarkup, deleteMessage, delete_all_messages, update_all_messages, sendStatusMessage, sendLog, sendPrivate, sendtextlog, auto_delete
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.mirror_utils.status_utils.clone_status import CloneStatus
from bot import dispatcher, LOGGER, CLONE_LIMIT, STOP_DUPLICATE, download_dict, download_dict_lock, Interval, BOT_PM, bot
from bot.helper.ext_utils.bot_utils import get_readable_file_size, is_gdrive_link, is_gdtot_link, new_thread, is_appdrive_link
from bot.helper.ext_utils.parser import appdrive, gdtot
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException
from bot.helper.telegram_helper.button_build import ButtonMaker

@new_thread
def cloneNode(update, context):
    if BOT_PM:
      try:
        msg1 = f'Added your Requested Link to Downloads'
        send = bot.sendMessage(update.message.from_user.id, text=msg1, )
        send.delete()
      except Exception as e:
        LOGGER.warning(e)
        bot_d = bot.get_me()
        b_uname = bot_d.username
        uname = f'<a href="tg://user?id={update.message.from_user.id}">{update.message.from_user.first_name}</a>'
        buttons = ButtonMaker()
        buttons.buildbutton("Start Me", f"http://t.me/{b_uname}")
        buttons.buildbutton("Updates Channel", "http://t.me/BaashaXclouD")
        reply_markup = InlineKeyboardMarkup(buttons.build_menu(2))
        message = sendMarkup(f"Hey Bro {uname}👋,\n\n<b>I Found That You Haven't Started Me In PM Yet 😶</b>\n\nFrom Now on i Will links in PM Only 😇", bot, update, reply_markup=reply_markup)     
        return
    try:
        user = bot.get_chat_member("-1001237102795", update.message.from_user.id)
        LOGGER.error(user.status)
        if user.status not in ('member','creator','administrator'):
            buttons = ButtonMaker()
            buttons.buildbutton("Join Updates Channel", "https://t.me/KaipullaBots")
            reply_markup = InlineKeyboardMarkup(buttons.build_menu(1))
            sendMarkup(f"<b>⚠️You Have Not Joined My Updates Channel</b>\n\n<b>Join Immediately to use the Bot.</b>", bot, update, reply_markup)
            return
    except:
        pass
    args = update.message.text.split(" ", maxsplit=1)
    reply_to = update.message.reply_to_message
    uname = f'<a href="tg://user?id={update.message.from_user.id}">{update.message.from_user.first_name}</a>'
    uid= f"<a>{update.message.from_user.id}</a>"
    if len(args) > 1:
        link = args[1]
        if update.message.from_user.username:
            tag = f"@{update.message.from_user.username}"
        else:
            tag = update.message.from_user.mention_html(update.message.from_user.first_name)
    elif reply_to is not None:
        link = reply_to.text
        if reply_to.from_user.username:
            tag = f"@{reply_to.from_user.username}"
        else:
            tag = reply_to.from_user.mention_html(reply_to.from_user.first_name)
    else:
        link = ''
    try:
        is_gdtot = is_gdtot_link(link)
        if is_gdtot:
            msg = sendMessage(f"💤 Connecting To GDTOT : <code>{link}</code>", context.bot, update)
            LOGGER.info(f"Processing: {link}")
            link = gdtot(link)
            deleteMessage(context.bot, msg)
        is_appdrive = True if "appdrive.in" in link else False
        if is_appdrive:
            msg = sendMessage(f"💤 Connecting To AppDrive : <code>{link}</code>", context.bot, update)
            LOGGER.info(f"Processing: {link}")
            apdict = appdrive(link)
            link = apdict.get('gdrive_link')
            deleteMessage(context.bot, msg)
        is_driveapp = True if "driveapp.in" in link else False
        if is_driveapp:
            msg = sendMessage(f"💤 Connecting To Drive App : <code>{link}</code>", context.bot, update)
            LOGGER.info(f"Processing: {link}")
            apdict = appdrive(link)
            link = apdict.get('gdrive_link')
            deleteMessage(context.bot, msg)
    except DirectDownloadLinkException as e:
        deleteMessage(context.bot, msg)
        LOGGER.error(e)
        return sendMessage(str(e), context.bot, update)
    if is_gdrive_link(link):
        gd = GoogleDriveHelper()
        res, size, name, files = gd.helper(link)
        if res != "":
            return sendMessage(res, context.bot, update)
        if STOP_DUPLICATE:
            LOGGER.info('Checking File/Folder if already in Drive...')
            smsg, button = gd.drive_list(name, True, True)
            if smsg:
                msg3 = "File/Folder is already available in Drive.\nHere are the search results:"
                sendMarkup(msg3, context.bot, update, button)
                if is_gdtot_link:
                    LOGGER.info(f"Deleting: {link}")
                    gd.deletefile(link)
                elif is_appdrive:
                    if apdict.get('link_type') == 'login':
                        LOGGER.info(f"Deleting: {link}")
                        gd.deletefile(link)
                return
        if CLONE_LIMIT is not None:
            LOGGER.info('Checking File/Folder Size...')
            if size > CLONE_LIMIT * 1024**3:
                msg2 = f'Failed, Clone limit is {CLONE_LIMIT}GB.\nYour File/Folder size is {get_readable_file_size(size)}.'
                return sendMessage(msg2, context.bot, update)
        if files <= 10:
            sendtextlog(f"<b>User: {uname}</b>\n<b>User ID:</b> <code>/warn {uid}</code>\n\n<b>Link Sended:</b>\n<code>{link}</code>\n\n#GDrive", context.bot, update)
            msg = sendMessage(f"♻️ Cloning: <code>{link}</code>", context.bot, update)
            result, button = gd.clone(link)
            deleteMessage(context.bot, msg)
        else:
            sendtextlog(f"<b>User: {uname}</b>\n<b>User ID:</b> <code>/warn {uid}</code>\n\n<b>Link Sended:</b>\n<code>{link}</code>\n\n#GDrive", context.bot, update)
            drive = GoogleDriveHelper(name)
            gid = ''.join(random.SystemRandom().choices(string.ascii_letters + string.digits, k=12))
            clone_status = CloneStatus(drive, size, update, gid)
            with download_dict_lock:
                download_dict[update.message.message_id] = clone_status
            sendStatusMessage(update, context.bot)
            result, button = drive.clone(link)
            with download_dict_lock:
                del download_dict[update.message.message_id]
                count = len(download_dict)
            try:
                if count == 0:
                    Interval[0].cancel()
                    del Interval[0]
                    delete_all_messages()
                else:
                    update_all_messages()
            except IndexError:
                pass
        if update.message.from_user.username:
            uname = f'@{update.message.from_user.username}'
        else:
            uname = f'<a href="tg://user?id={update.message.from_user.id}">{update.message.from_user.first_name}</a>'
        if uname is not None:
            cc = f'\n\n<b>-> Requested By : {uname}</b>'
            men = f'{uname}'
            msg_g = f"\n\n - Don't Share Index Link 🖇️"
            fwdpm = f"\n\n<b>I've Send Your Links To Your PM & Log Channel</b>"
        if button == "cancelled" or button == "":
            sendMessage(men + result, context.bot, update)
        else:
            sendLog(result + cc + msg_g, context.bot, update, button)
            auto = sendMessage(result + cc + fwdpm, context.bot, update)
            Thread(target=auto_delete, args=(context.bot, update.message, auto)).start()
            sendPrivate(result + cc + msg_g, context.bot, update, button)
        if is_gdtot:
            LOGGER.info(f"Deleting: {link}")
            gd.deletefile(link)
        elif is_appdrive:
            if apdict.get('link_type') == 'login':
                LOGGER.info(f"Deleting: {link}")
                gd.deletefile(link)
    else:
        sendMessage('Send GDrive , AppDrive , GDTOT Link Along With Command Or By Replying To The Link By Command', context.bot, update)

clone_handler = CommandHandler(BotCommands.CloneCommand, cloneNode, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
dispatcher.add_handler(clone_handler)
