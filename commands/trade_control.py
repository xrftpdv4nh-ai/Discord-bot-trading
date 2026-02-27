import discord

OWNER_IDS = [1035345058561540127]  # ايديك


async def handle_trade_control(bot, message: discord.Message):

    if message.author.id not in OWNER_IDS:
        return

    args = message.content.split()
    if not args:
        return

    cmd = args[0].lower()

    # ================= تعديل النسبة العامة =================
    if cmd == "setwin" and len(args) == 2:

        try:
            new_rate = int(args[1])
            if new_rate < 0 or new_rate > 100:
                raise ValueError
        except:
            await message.channel.send("❌ النسبة لازم تكون بين 0 و 100")
            return

        old = await bot.db.settings.find_one({"type": "global_trade"})
        old_rate = old["win_rate"] if old else "افتراضي"

        await bot.db.settings.update_one(
            {"type": "global_trade"},
            {"$set": {"win_rate": new_rate}},
            upsert=True
        )

        await message.channel.send(
            f"📊 نسبة الربح كانت {old_rate}% وأصبحت {new_rate}%"
        )
        return

    # ================= رستر للنسبة العامة =================
    elif cmd == "resetwin":

        await bot.db.settings.delete_one({"type": "global_trade"})

        await message.channel.send(
            "♻️ تم إرجاع نسبة الربح للنظام الافتراضي (حسب الرول)."
        )
        return

    # ================= تعديل مستخدم معين =================
    elif cmd == "setuserwin" and len(args) == 3:

        if not message.mentions:
            await message.channel.send("❌ لازم تمنشن الشخص")
            return

        user = message.mentions[0]

        try:
            new_rate = int(args[2])
            if new_rate < 0 or new_rate > 100:
                raise ValueError
        except:
            await message.channel.send("❌ النسبة لازم تكون بين 0 و 100")
            return

        old = await bot.db.settings.find_one({
            "type": "user_trade",
            "user_id": user.id
        })

        old_rate = old["win_rate"] if old else "افتراضي"

        await bot.db.settings.update_one(
            {
                "type": "user_trade",
                "user_id": user.id
            },
            {"$set": {"win_rate": new_rate}},
            upsert=True
        )

        await message.channel.send(
            f"👤 نسبة ربح {user.mention} كانت {old_rate}% وأصبحت {new_rate}%"
        )
        return

    # ================= رستر لنسبة شخص =================
    elif cmd == "resetuserwin":

        if not message.mentions:
            await message.channel.send("❌ منشن المستخدم")
            return

        user = message.mentions[0]

        await bot.db.settings.delete_one({
            "type": "user_trade",
            "user_id": user.id
        })

        await message.channel.send(
            f"♻️ تم إلغاء النسبة الخاصة بـ {user.mention}"
        )
        return
