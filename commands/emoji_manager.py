import discord
import aiohttp
import re


async def handle_emoji_message(bot, message: discord.Message):

    if message.author.bot or not message.guild:
        return

    # الأمر بدون برفكس
    if not message.content.lower().startswith("addemoji"):
        return

    # تحقق من الصلاحيات
    if not message.author.guild_permissions.manage_emojis_and_stickers:
        await message.channel.send("❌ تحتاج صلاحية Manage Emojis.")
        return

    args = message.content.split()

    if len(args) != 2:
        await message.channel.send("❌ الاستخدام الصحيح:\n`addemoji <:name:id>`")
        return

    emoji_input = args[1]

    match = re.match(r"<(a?):(\w+):(\d+)>", emoji_input)

    if not match:
        await message.channel.send("❌ لازم تحط إيموجي مخصص (Custom Emoji).")
        return

    animated = match.group(1) == "a"
    name = match.group(2)
    emoji_id = match.group(3)

    extension = "gif" if animated else "png"
    url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{extension}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await message.channel.send("❌ فشل تحميل الإيموجي.")
                    return

                data = await resp.read()

        new_emoji = await message.guild.create_custom_emoji(
            name=name,
            image=data
        )

        await message.channel.send(f"✅ تم إضافة الإيموجي: {new_emoji}")

    except discord.HTTPException:
        await message.channel.send("❌ السيرفر مليان إيموجي أو حصل خطأ.")
