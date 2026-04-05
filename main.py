import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio
import random
import json
import os
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

# ====================== KEEP ALIVE ======================
app = Flask(__name__)

@app.route('/')
def home():
    return "Vexis Bot 7/24 Aktif ✅"

def run():
    app.run(host='0.0.0.0', port=5000)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

keep_alive()

# ====================== BOT ======================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

data = {
    "mesaj_sayisi": {},
    "reklamengel": False,
    "admin_access": {},
    "warnings": {},
    "muted": {},
    "sicil": {}
}

# ====================== EMBED ======================
def create_embed(title, description=None, color=0x2b2d31):
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.utcnow())
    embed.set_footer(text="Vexis • plutoxstar", icon_url="https://i.imgur.com/AfFp7pu.png")
    return embed

# ====================== ADMIN BYPASS SİSTEMİ ======================
def admin_or_perm(**perms):
    async def predicate(ctx):
        if data["admin_access"].get(str(ctx.author.id)):
            return True
        resolved = ctx.channel.permissions_for(ctx.author)
        return all(getattr(resolved, perm, None) == value for perm, value in perms.items())
    return commands.check(predicate)

# ====================== ONAY SİSTEMİ ======================
class ConfirmView(View):
    def __init__(self, ctx, action, target):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.result = False

    @discord.ui.button(label="✅ Onayla", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id: return
        self.result = True
        await interaction.response.edit_message(embed=create_embed("✅ Onaylandı", color=0x00FF00), view=None)
        self.stop()

    @discord.ui.button(label="❌ İptal", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id: return
        self.result = False
        await interaction.response.edit_message(embed=create_embed("❌ İptal Edildi", color=0xFF0000), view=None)
        self.stop()

async def confirmation(ctx, action: str, target):
    embed = create_embed("⚠️ Onay Gerekli", f"**{action}** işlemini **{target}** üzerinde yapmak istediğine emin misin?", 0xFF0000)
    view = ConfirmView(ctx, action, target)
    await ctx.send(embed=embed, view=view)
    await view.wait()
    return view.result

# ====================== ON_READY ======================
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="discord.gg/vexisleague"))
    try:
        with open("avatar.png", "rb") as f:
            await bot.user.edit(avatar=f.read())
        print("✅ Avatar güncellendi!")
    except Exception as e:
        print(f"⚠️ Avatar güncellenemedi: {e}")
    print(f"✅ {bot.user} 7/24 AKTİF!")

# ====================== YARDIM ======================
@bot.command(aliases=['help', 'komutlar'])
async def yardım(ctx):
    embed = create_embed("⚡ Vexis Bot - Tüm Komutlar", "Prefix: `.`", 0xFF0000)
    embed.add_field(name="📌 Genel", value="`ping` `avatar` `bilgi` `ulke` `dcsv` `söv` `dm` `yaz` `dmall`", inline=False)
    embed.add_field(name="🛠 Rol", value="`rolver` `rolal` `terfi` `tenzil` `rolbilgi`", inline=False)
    embed.add_field(name="🔨 Moderasyon", value="`ban` `unban` `kick` `clear` `warn` `timeout` `untimeout`", inline=False)
    embed.add_field(name="📊 İstatistik", value="`mesajsayı` `istatistik` `mesajtop` `stattop`", inline=False)
    embed.add_field(name="⚠️ Geçmiş", value="`warns @üye` — uyarı geçmişi\n`sicil @üye` — mute/ban/kick geçmişi", inline=False)
    embed.add_field(name="🔧 Kanal Yönetimi", value="`duyuru` `yavaşmod` `kilit` `kilitsiz` `nick` `kanal` `kanalsil` `embed`", inline=False)
    embed.add_field(name="⚡ Gelişmiş Mod", value="`timeout` `untimeout` `clearwarn` `hackban` `banlist` `purgeuser` `massrole` `lockdown` `unlockdown` `nuke`", inline=False)
    embed.add_field(name="📊 Bilgi", value="`userinfo` `roleinfo` `sunucu` `botbilgi`", inline=False)
    embed.add_field(name="🎉 Diğer", value="`anket` `çekiliş` `hatırlatıcı` `afk` `rololuştur` `rolsil`", inline=False)
    embed.add_field(name="🤖 Yapay Zeka", value="`yapayzeka [mesaj]` — AI ile sohbet", inline=False)
    embed.add_field(name="📋 Kayıt", value="`ket @üye Nick`\n→ Sadece **Kayıt Yetkilisi** kullanabilir\n→ Üye / V I P / Futbolcu / Teknik Direktör butonları", inline=False)
    embed.add_field(name="🔒 Diğer", value="`reklamengel` `admingiris`", inline=False)
    await ctx.send(embed=embed)

# ====================== GENEL KOMUTLAR ======================
@bot.command()
async def ping(ctx):
    await ctx.send(embed=create_embed("🏓 Pong!", f"Gecikme: `{round(bot.latency*1000)}ms`", 0x00FF00))

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = create_embed(f"🖼 {member.name} Avatarı", color=0x7289DA)
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def bilgi(ctx, member: discord.Member = None):
    member = member or ctx.author
    roles = [r.mention for r in member.roles if r.name != "@everyone"]
    embed = create_embed(f"👤 {member.name} Bilgisi", color=0x7289DA)
    embed.add_field(name="🆔 ID", value=member.id, inline=True)
    embed.add_field(name="📛 Kullanıcı Adı", value=str(member), inline=True)
    embed.add_field(name="🤖 Bot mu?", value="Evet" if member.bot else "Hayır", inline=True)
    embed.add_field(name="📅 Hesap Açılış", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="📥 Sunucuya Katılış", value=member.joined_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="🎭 Roller", value=", ".join(roles) if roles else "Yok", inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def ulke(ctx):
    embed = create_embed("🌍 Sunucu Bölgesi", color=0x00FFFF)
    embed.add_field(name="Sunucu", value=ctx.guild.name, inline=True)
    embed.add_field(name="Bölge", value="Avrupa / Global", inline=True)
    embed.add_field(name="Üye Sayısı", value=ctx.guild.member_count, inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def dcsv(ctx):
    guild = ctx.guild
    embed = create_embed(f"🏠 {guild.name} Sunucu Bilgisi", color=0x7289DA)
    embed.add_field(name="👑 Sahip", value=guild.owner.mention, inline=True)
    embed.add_field(name="🆔 Sunucu ID", value=guild.id, inline=True)
    embed.add_field(name="👥 Üye Sayısı", value=guild.member_count, inline=True)
    embed.add_field(name="💬 Kanal Sayısı", value=len(guild.channels), inline=True)
    embed.add_field(name="🎭 Rol Sayısı", value=len(guild.roles), inline=True)
    embed.add_field(name="📅 Oluşturulma", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await ctx.send(embed=embed)

@bot.command()
async def yaz(ctx, *, mesaj: str):
    await ctx.message.delete()
    await ctx.send(mesaj)

@bot.command()
async def dm(ctx, member: discord.Member, *, mesaj):
    try:
        embed = create_embed("📨 Vexis Bot'tan Mesaj", mesaj, 0x00FF00)
        embed.set_footer(text=f"Gönderen: {ctx.author}")
        await member.send(embed=embed)
        await ctx.send(embed=create_embed("✅ DM Gönderildi", f"{member.mention} adlı kişiye mesaj gönderildi.", 0x00FF00))
    except:
        await ctx.send(embed=create_embed("❌ Hata", "Kullanıcının DM'i kapalı veya hata oluştu.", 0xFF0000))

@bot.command()
@commands.has_permissions(administrator=True)
async def dmall(ctx, *, mesaj: str):
    basarili = 0
    basarisiz = 0
    embed_mesaj = create_embed("📨 Vexis Bot'tan Toplu Mesaj", mesaj, 0x00FF00)
    embed_mesaj.set_footer(text=f"Gönderen: {ctx.guild.name}")
    durum = await ctx.send(embed=create_embed("📤 Gönderiliyor...", "Tüm üyelere mesaj gönderiliyor, lütfen bekle...", 0xFFD700))
    for member in ctx.guild.members:
        if member.bot:
            continue
        try:
            await member.send(embed=embed_mesaj)
            basarili += 1
        except:
            basarisiz += 1
    await durum.edit(embed=create_embed("✅ Toplu DM Tamamlandı", f"✅ Başarılı: **{basarili}**\n❌ Başarısız: **{basarisiz}**", 0x00FF00))

@bot.command()
async def söv(ctx, member: discord.Member):
    küfürler = [
        "Senin ananı dağ başında sikeyim orospu türemesi seni",
        "Amına koduğumun evladı siktir git lan",
        "Ananı sikerim babanı sikerim aileni sikerim piç"
    ] * 10
    await ctx.send(f"{member.mention} {random.choice(küfürler)}")

# ====================== ROL KOMUTLARI ======================
@bot.command()
@commands.has_permissions(manage_roles=True)
async def rolver(ctx, member: discord.Member, *, rol_adi: str):
    rol = discord.utils.get(ctx.guild.roles, name=rol_adi)
    if not rol:
        return await ctx.send(embed=create_embed("❌ Hata", f"`{rol_adi}` adında bir rol bulunamadı.", 0xFF0000))
    await member.add_roles(rol)
    await ctx.send(embed=create_embed("✅ Rol Verildi", f"{member.mention} kullanıcısına **{rol.name}** rolü verildi.", 0x00FF00))

@bot.command()
@commands.has_permissions(manage_roles=True)
async def rolal(ctx, member: discord.Member, *, rol_adi: str):
    rol = discord.utils.get(ctx.guild.roles, name=rol_adi)
    if not rol:
        return await ctx.send(embed=create_embed("❌ Hata", f"`{rol_adi}` adında bir rol bulunamadı.", 0xFF0000))
    await member.remove_roles(rol)
    await ctx.send(embed=create_embed("✅ Rol Alındı", f"{member.mention} kullanıcısından **{rol.name}** rolü alındı.", 0x00FF00))

@bot.command()
@commands.has_permissions(manage_roles=True)
async def terfi(ctx, member: discord.Member, *, rol_adi: str):
    rol = discord.utils.get(ctx.guild.roles, name=rol_adi)
    if not rol:
        return await ctx.send(embed=create_embed("❌ Hata", f"`{rol_adi}` adında bir rol bulunamadı.", 0xFF0000))
    await member.add_roles(rol)
    embed = create_embed("⬆️ Terfi!", f"{member.mention} → **{rol.name}** rolüne terfi ettirildi! 🎉", 0xFFD700)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def tenzil(ctx, member: discord.Member, *, rol_adi: str):
    rol = discord.utils.get(ctx.guild.roles, name=rol_adi)
    if not rol:
        return await ctx.send(embed=create_embed("❌ Hata", f"`{rol_adi}` adında bir rol bulunamadı.", 0xFF0000))
    await member.remove_roles(rol)
    embed = create_embed("⬇️ Tenzil!", f"{member.mention} → **{rol.name}** rolünden tenzil edildi.", 0xFF6600)
    await ctx.send(embed=embed)

@bot.command()
async def rolbilgi(ctx, *, rol_adi: str):
    rol = discord.utils.get(ctx.guild.roles, name=rol_adi)
    if not rol:
        return await ctx.send(embed=create_embed("❌ Hata", f"`{rol_adi}` adında bir rol bulunamadı.", 0xFF0000))
    embed = create_embed(f"🎭 {rol.name} Rol Bilgisi", color=rol.color.value or 0x7289DA)
    embed.add_field(name="🆔 Rol ID", value=rol.id, inline=True)
    embed.add_field(name="🎨 Renk", value=str(rol.color), inline=True)
    embed.add_field(name="👥 Üye Sayısı", value=len(rol.members), inline=True)
    embed.add_field(name="📌 Hoist", value="Evet" if rol.hoist else "Hayır", inline=True)
    embed.add_field(name="🔧 Yönetici", value="Evet" if rol.permissions.administrator else "Hayır", inline=True)
    embed.add_field(name="📅 Oluşturulma", value=rol.created_at.strftime("%d/%m/%Y"), inline=True)
    await ctx.send(embed=embed)

# ====================== MODERASYON KOMUTLARI ======================
def sicil_ekle(uid, islem, sebep, yetkili):
    if uid not in data["sicil"]:
        data["sicil"][uid] = []
    data["sicil"][uid].append({
        "islem": islem,
        "sebep": sebep,
        "tarih": datetime.utcnow().strftime("%d/%m/%Y %H:%M"),
        "yetkili": str(yetkili)
    })

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, sebep: str = "Sebep belirtilmedi"):
    if await confirmation(ctx, "ban", member.name):
        await member.ban(reason=sebep)
        sicil_ekle(str(member.id), "🔨 Ban", sebep, ctx.author)
        await ctx.send(embed=create_embed("🔨 Banned", f"{member.mention} → **{sebep}** sebebiyle banlandı.", 0xFF0000))

@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, kullanici_id: int):
    try:
        user = await bot.fetch_user(kullanici_id)
        await ctx.guild.unban(user)
        await ctx.send(embed=create_embed("✅ Unban", f"**{user}** banı kaldırıldı.", 0x00FF00))
    except:
        await ctx.send(embed=create_embed("❌ Hata", "Kullanıcı bulunamadı veya banlı değil.", 0xFF0000))

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, sebep: str = "Sebep belirtilmedi"):
    if await confirmation(ctx, "kick", member.name):
        await member.kick(reason=sebep)
        sicil_ekle(str(member.id), "👢 Kick", sebep, ctx.author)
        await ctx.send(embed=create_embed("👢 Kicked", f"{member.mention} → **{sebep}** sebebiyle atıldı.", 0xFF6600))


@bot.command(aliases=['sil', 'purge'])
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    if await confirmation(ctx, f"{amount} mesaj silme", "bu kanal"):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(embed=create_embed("🧹 Temizlendi", f"{amount} mesaj silindi.", 0x00FF00), delete_after=5)

@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member, *, sebep: str = "Sebep belirtilmedi"):
    uid = str(member.id)
    if uid not in data["warnings"]:
        data["warnings"][uid] = []
    data["warnings"][uid].append({"sebep": sebep, "tarih": datetime.utcnow().strftime("%d/%m/%Y %H:%M"), "yetkili": str(ctx.author)})
    sayi = len(data["warnings"][uid])
    embed = create_embed("⚠️ Uyarı Verildi", f"{member.mention} → **{sebep}**\nToplam Uyarı: **{sayi}**", 0xFFD700)
    await ctx.send(embed=embed)
    try:
        await member.send(embed=create_embed("⚠️ Uyarıldın!", f"**{ctx.guild.name}** sunucusunda uyarıldın!\nSebep: **{sebep}**\nToplam uyarı: **{sayi}**", 0xFFD700))
    except:
        pass

# ====================== İSTATİSTİK KOMUTLARI ======================
@bot.command()
async def mesajsayı(ctx, member: discord.Member = None):
    member = member or ctx.author
    sayi = data["mesaj_sayisi"].get(str(member.id), 0)
    await ctx.send(embed=create_embed("💬 Mesaj Sayısı", f"{member.mention} → **{sayi}** mesaj", 0x00FFFF))

@bot.command()
async def istatistik(ctx, member: discord.Member = None):
    member = member or ctx.author
    uid = str(member.id)
    mesaj = data["mesaj_sayisi"].get(uid, 0)
    uyari = len(data["warnings"].get(uid, []))
    embed = create_embed(f"📊 {member.name} İstatistikleri", color=0x7289DA)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="💬 Mesaj Sayısı", value=mesaj, inline=True)
    embed.add_field(name="⚠️ Uyarı Sayısı", value=uyari, inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def mesajtop(ctx):
    top = sorted(data["mesaj_sayisi"].items(), key=lambda x: x[1], reverse=True)[:10]
    txt = "\n".join([f"`{i+1}.` <@{uid}> → **{count}** mesaj" for i, (uid, count) in enumerate(top)])
    await ctx.send(embed=create_embed("🏆 Mesaj Sıralaması", txt or "Henüz veri yok", 0xFFD700))

@bot.command()
async def stattop(ctx):
    top = sorted(data["mesaj_sayisi"].items(), key=lambda x: x[1], reverse=True)[:10]
    lines = []
    for i, (uid, count) in enumerate(top):
        uyari = len(data["warnings"].get(uid, []))
        lines.append(f"`{i+1}.` <@{uid}> — 💬 **{count}** mesaj | ⚠️ **{uyari}** uyarı")
    txt = "\n".join(lines)
    await ctx.send(embed=create_embed("📊 Genel Sıralama", txt or "Henüz veri yok", 0x7289DA))

# ====================== WARNS & SİCİL ======================
@bot.command()
async def warns(ctx, member: discord.Member = None):
    member = member or ctx.author
    uid = str(member.id)
    uyarilar = data["warnings"].get(uid, [])
    if not uyarilar:
        return await ctx.send(embed=create_embed("✅ Temiz Sicil", f"{member.mention} hiç uyarı almamış.", 0x00FF00))
    embed = create_embed(f"⚠️ {member.name} — Uyarı Geçmişi", color=0xFFD700)
    embed.set_thumbnail(url=member.display_avatar.url)
    for i, u in enumerate(uyarilar[-10:], 1):
        embed.add_field(
            name=f"#{i} — {u['tarih']}",
            value=f"📝 **Sebep:** {u['sebep']}\n👮 **Yetkili:** {u['yetkili']}",
            inline=False
        )
    embed.set_footer(text=f"Toplam {len(uyarilar)} uyarı • Vexis Bot • TreyZ9")
    await ctx.send(embed=embed)

@bot.command()
async def sicil(ctx, member: discord.Member = None):
    member = member or ctx.author
    uid = str(member.id)
    kayitlar = data["sicil"].get(uid, [])
    if not kayitlar:
        return await ctx.send(embed=create_embed("✅ Temiz Sicil", f"{member.mention} hiç ceza almamış.", 0x00FF00))
    embed = create_embed(f"📋 {member.name} — Disiplin Sicili", color=0xFF4444)
    embed.set_thumbnail(url=member.display_avatar.url)
    for i, k in enumerate(kayitlar[-10:], 1):
        embed.add_field(
            name=f"#{i} {k['islem']} — {k['tarih']}",
            value=f"📝 **Sebep:** {k['sebep']}\n👮 **Yetkili:** {k['yetkili']}",
            inline=False
        )
    embed.set_footer(text=f"Toplam {len(kayitlar)} işlem • Vexis Bot • TreyZ9")
    await ctx.send(embed=embed)

# ====================== YAPAY ZEKA ======================
import aiohttp

@bot.command()
async def yapayzeka(ctx, *, mesaj: str):
    bekle = await ctx.send(embed=create_embed("🤖 Düşünüyor...", "Yapay zeka cevap hazırlıyor...", 0x7289DA))
    try:
        payload = {
            "model": "openai",
            "messages": [
                {"role": "system", "content": "Sen Vexis adlı bir Discord bot asistanısın. Türkçe konuşursun. Kısa, samimi ve yardımsever cevaplar verirsin."},
                {"role": "user", "content": mesaj}
            ]
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://text.pollinations.ai/openai",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                data_resp = await resp.json()
                cevap = data_resp["choices"][0]["message"]["content"]
        embed = create_embed("🤖 Vexis AI", cevap, 0x7289DA)
        embed.add_field(name="💬 Soru", value=mesaj, inline=False)
        embed.set_footer(text=f"Soran: {ctx.author} • Vexis Bot")
        await bekle.edit(embed=embed)
    except Exception as e:
        await bekle.edit(embed=create_embed("❌ Hata", f"Yapay zeka şu an yanıt veremiyor. Tekrar dene!\n`{e}`", 0xFF0000))

# ====================== DİĞER KOMUTLAR ======================
@bot.command()
@commands.has_permissions(administrator=True)
async def testjoin(ctx, member: discord.Member = None):
    member = member or ctx.author
    kayit_kanal = bot.get_channel(1479997187810394313)
    if not kayit_kanal:
        return await ctx.send(embed=create_embed("❌ Hata", "Kayıt kanalı bulunamadı!", 0xFF0000))
    kayit_rol = discord.utils.get(ctx.guild.roles, name="Kayıt Yetkilisi")
    rol_mention = kayit_rol.mention if kayit_rol else "@Kayıt Yetkilisi"
    embed = create_embed("📥 Yeni Üye!", f"{member.mention} sunucumuza katıldı!", 0x00FF00)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="🆔 ID", value=member.id, inline=True)
    embed.add_field(name="📅 Hesap Açılış", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
    await kayit_kanal.send(
        content=f"{rol_mention} Yeni Bir Üye Sunucumuza Katıldı Göreviniz Bu Üyeyi Kayıt Etmektir",
        embed=embed
    )
    await ctx.send(embed=create_embed("✅ Test Gönderildi", f"Kayıt kanalına test mesajı gönderildi.", 0x00FF00))

@bot.command()
@commands.has_permissions(administrator=True)
async def reklamengel(ctx):
    data["reklamengel"] = not data["reklamengel"]
    durum = "✅ Aktif" if data["reklamengel"] else "❌ Devre Dışı"
    await ctx.send(embed=create_embed("🔒 Reklam Engel", f"Reklam engeli: **{durum}**", 0xFF0000 if data["reklamengel"] else 0x00FF00))

# ====================== KAYIT SİSTEMİ ======================
class KayitView(View):
    def __init__(self, member: discord.Member, nick: str, yetkili: discord.Member):
        super().__init__(timeout=60)
        self.member = member
        self.nick = nick
        self.yetkili = yetkili

    async def rol_ver(self, interaction: discord.Interaction, rol_adi: str):
        if interaction.user.id != self.yetkili.id:
            return await interaction.response.send_message("❌ Bu butonu sadece komutu kullanan yetkili kullanabilir!", ephemeral=True)
        guild = interaction.guild
        rol = discord.utils.get(guild.roles, name=rol_adi)
        if not rol:
            return await interaction.response.send_message(f"❌ `{rol_adi}` rolü bulunamadı! Sunucuda bu isimde bir rol oluştur.", ephemeral=True)
        try:
            await self.member.add_roles(rol)
            if self.nick:
                try:
                    await self.member.edit(nick=self.nick)
                except:
                    pass
            embed = create_embed("✅ Kayıt Tamamlandı", f"{self.member.mention} kayıt edildi!\n👤 Nick: **{self.nick or self.member.name}**\n🎭 Rol: **{rol.name}**", 0x00FF00)
            embed.set_thumbnail(url=self.member.display_avatar.url)
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {e}", ephemeral=True)

    @discord.ui.button(label="Üye", style=discord.ButtonStyle.green, emoji="👤")
    async def uye(self, interaction: discord.Interaction, button: Button):
        await self.rol_ver(interaction, "Üye")

    @discord.ui.button(label="V I P", style=discord.ButtonStyle.blurple, emoji="⭐")
    async def vip(self, interaction: discord.Interaction, button: Button):
        await self.rol_ver(interaction, "V I P")

    @discord.ui.button(label="Futbolcu", style=discord.ButtonStyle.green, emoji="⚽")
    async def futbolcu(self, interaction: discord.Interaction, button: Button):
        await self.rol_ver(interaction, "Futbolcu")

    @discord.ui.button(label="Teknik Direktör", style=discord.ButtonStyle.red, emoji="📋")
    async def teknik_direktor(self, interaction: discord.Interaction, button: Button):
        await self.rol_ver(interaction, "Teknik Direktör")

@bot.command()
async def ket(ctx, member: discord.Member, *, nick: str = None):
    kayit_rol = discord.utils.get(ctx.guild.roles, name="Kayıt Yetkilisi")
    if not kayit_rol or kayit_rol not in ctx.author.roles:
        return await ctx.send(embed=create_embed("❌ Yetki Yok", "Bu komutu sadece **Kayıt Yetkilisi** rolüne sahip kişiler kullanabilir!", 0xFF0000))
    kayitsiz_rol = discord.utils.get(ctx.guild.roles, name="Kayıtsız")
    if kayitsiz_rol and kayitsiz_rol not in member.roles:
        return await ctx.send(embed=create_embed("⚠️ Zaten Kayıtlı", f"{member.mention} zaten kayıtlı! **Kayıtsız** rolü bu kullanıcıda bulunmuyor.", 0xFFAA00))
    embed = create_embed("📋 Kayıt Paneli", f"**{member.mention}** için rol seçin:\n👤 Nick: **{nick or 'Belirtilmedi'}**", 0x7289DA)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="🆔 ID", value=member.id, inline=True)
    embed.add_field(name="📅 Hesap Açılış", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
    view = KayitView(member, nick, ctx.author)
    await ctx.send(embed=embed, view=view)

@bot.command()
async def admingiris(ctx, *, sifre: str):
    await ctx.message.delete()
    admin_sifre = os.getenv("ADMIN_SIFRE", "vexis2024")
    if sifre == admin_sifre:
        data["admin_access"][str(ctx.author.id)] = True
        await ctx.author.send(embed=create_embed("✅ Admin Girişi", "Admin paneline erişim sağlandı!", 0x00FF00))
        await ctx.send(embed=create_embed("✅ Giriş Başarılı", f"{ctx.author.mention} admin girişi yaptı.", 0x00FF00), delete_after=5)
    else:
        await ctx.send(embed=create_embed("❌ Hatalı Şifre", "Şifre yanlış!", 0xFF0000), delete_after=5)

# ====================== YÖNETİM KOMUTLARI ======================
@bot.command()
@commands.has_permissions(administrator=True)
async def duyuru(ctx, *, mesaj: str):
    await ctx.message.delete()
    embed = create_embed("📢 DUYURU", mesaj, 0xFF0000)
    embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def yavaşmod(ctx, saniye: int = 0):
    await ctx.channel.edit(slowmode_delay=saniye)
    if saniye == 0:
        await ctx.send(embed=create_embed("🔓 Yavaş Mod Kapatıldı", f"{ctx.channel.mention} kanalında yavaş mod kaldırıldı.", 0x00FF00))
    else:
        await ctx.send(embed=create_embed("🐢 Yavaş Mod Açıldı", f"{ctx.channel.mention} kanalında **{saniye} saniyelik** yavaş mod aktif.", 0xFFAA00))

@bot.command()
@commands.has_permissions(manage_channels=True)
async def kilit(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send(embed=create_embed("🔒 Kanal Kilitlendi", f"{ctx.channel.mention} kanalı kilitlendi. Kimse mesaj atamaz.", 0xFF0000))

@bot.command()
@commands.has_permissions(manage_channels=True)
async def kilitsiz(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = True
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send(embed=create_embed("🔓 Kanal Açıldı", f"{ctx.channel.mention} kanalının kilidi açıldı.", 0x00FF00))

@bot.command()
@commands.has_permissions(manage_nicknames=True)
async def nick(ctx, member: discord.Member, *, yeni_nick: str):
    eski_nick = member.display_name
    try:
        await member.edit(nick=yeni_nick)
        embed = create_embed("✏️ Nick Değiştirildi", color=0x00FF00)
        embed.add_field(name="👤 Kullanıcı", value=member.mention, inline=True)
        embed.add_field(name="Eski Nick", value=eski_nick, inline=True)
        embed.add_field(name="Yeni Nick", value=yeni_nick, inline=True)
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send(embed=create_embed("❌ Hata", "Bu kişinin nickini değiştirme yetkim yok!", 0xFF0000))

# ====================== GELİŞMİŞ KOMUTLAR ======================
class AnketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.oylar = {"evet": set(), "hayir": set()}

    @discord.ui.button(label="✅ Evet  (0)", style=discord.ButtonStyle.green, custom_id="anket_evet")
    async def evet(self, interaction: discord.Interaction, button: Button):
        uid = interaction.user.id
        self.oylar["hayir"].discard(uid)
        if uid in self.oylar["evet"]:
            self.oylar["evet"].discard(uid)
        else:
            self.oylar["evet"].add(uid)
        button.label = f"✅ Evet  ({len(self.oylar['evet'])})"
        self.children[1].label = f"❌ Hayır  ({len(self.oylar['hayir'])})"
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="❌ Hayır  (0)", style=discord.ButtonStyle.red, custom_id="anket_hayir")
    async def hayir(self, interaction: discord.Interaction, button: Button):
        uid = interaction.user.id
        self.oylar["evet"].discard(uid)
        if uid in self.oylar["hayir"]:
            self.oylar["hayir"].discard(uid)
        else:
            self.oylar["hayir"].add(uid)
        self.children[0].label = f"✅ Evet  ({len(self.oylar['evet'])})"
        button.label = f"❌ Hayır  ({len(self.oylar['hayir'])})"
        await interaction.response.edit_message(view=self)

@bot.command()
@commands.has_permissions(administrator=True)
async def anket(ctx, *, soru: str):
    await ctx.message.delete()
    embed = create_embed("📊 ANKET", soru, 0x7289DA)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed, view=AnketView())

class CekilisView(View):
    def __init__(self, ctx, odul, sure):
        super().__init__(timeout=sure)
        self.ctx = ctx
        self.odul = odul
        self.katilimcilar = set()

    @discord.ui.button(label="🎉 Katıl!", style=discord.ButtonStyle.green)
    async def katil(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id in self.katilimcilar:
            self.katilimcilar.discard(interaction.user.id)
            await interaction.response.send_message("❌ Çekilişten ayrıldın.", ephemeral=True)
        else:
            self.katilimcilar.add(interaction.user.id)
            await interaction.response.send_message("✅ Çekilişe katıldın!", ephemeral=True)
        button.label = f"🎉 Katıl! ({len(self.katilimcilar)})"
        await interaction.message.edit(view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if not self.katilimcilar:
            embed = create_embed("🎉 Çekiliş Bitti", f"**{self.odul}**\n\n😢 Hiç katılımcı olmadı!", 0xFF0000)
        else:
            kazanan_id = random.choice(list(self.katilimcilar))
            embed = create_embed("🎉 Çekiliş Bitti!", f"**Ödül:** {self.odul}\n🏆 **Kazanan:** <@{kazanan_id}>\n👥 Katılımcı sayısı: {len(self.katilimcilar)}", 0xFFD700)
        try:
            await self.message.edit(embed=embed, view=self)
        except:
            pass

@bot.command()
@commands.has_permissions(administrator=True)
async def çekiliş(ctx, sure: int = 60, *, odul: str = "Sürpriz Ödül"):
    embed = create_embed("🎉 ÇEKİLİŞ BAŞLADI!", f"**Ödül:** {odul}\n⏱️ Süre: **{sure} saniye**\n\nKatılmak için aşağıdaki butona tıkla!", 0xFFD700)
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
    view = CekilisView(ctx, odul, sure)
    msg = await ctx.send(embed=embed, view=view)
    view.message = msg

@bot.command()
async def hatırlatıcı(ctx, sure: int, *, mesaj: str):
    await ctx.send(embed=create_embed("⏰ Hatırlatıcı Ayarlandı", f"**{sure} dakika** sonra sana hatırlatacağım!\n📝 {mesaj}", 0x00FF00))
    await asyncio.sleep(sure * 60)
    try:
        await ctx.author.send(embed=create_embed("⏰ Hatırlatıcı!", f"📝 {mesaj}", 0x00FF00))
    except:
        await ctx.send(f"{ctx.author.mention} ⏰ Hatırlatıcı: **{mesaj}**")

# ====================== MODERASyon + SUNUCU YÖNETİMİ ======================

# AFK takibi
afk_listesi = {}

# 1. Timeout (Discord native susturma)
@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, üye: discord.Member, dakika: int = 10, *, sebep: str = "Belirtilmedi"):
    bitis = datetime.utcnow() + timedelta(minutes=dakika)
    await üye.timeout(bitis, reason=sebep)
    embed = create_embed("⏱️ TIMEOUT", color=0xFF8800)
    embed.add_field(name="👤 Üye", value=üye.mention, inline=True)
    embed.add_field(name="⏳ Süre", value=f"{dakika} dakika", inline=True)
    embed.add_field(name="📋 Sebep", value=sebep, inline=False)
    await ctx.send(embed=embed)

# 2. Timeout kaldır
@bot.command()
@commands.has_permissions(moderate_members=True)
async def untimeout(ctx, üye: discord.Member):
    await üye.timeout(None)
    await ctx.send(embed=create_embed("✅ Timeout Kaldırıldı", f"{üye.mention} artık serbestçe yazabilir.", 0x00FF00))

# 3. Tüm uyarıları temizle
@bot.command()
@commands.has_permissions(administrator=True)
async def clearwarn(ctx, üye: discord.Member):
    data["uyarılar"].pop(str(üye.id), None)
    await ctx.send(embed=create_embed("🧹 Uyarılar Temizlendi", f"{üye.mention} adlı üyenin tüm uyarıları silindi.", 0x00FF00))

# 4. Detaylı kullanıcı bilgisi
@bot.command()
async def userinfo(ctx, üye: discord.Member = None):
    üye = üye or ctx.author
    roller = [r.mention for r in üye.roles if r.name != "@everyone"]
    embed = create_embed(f"👤 {üye.display_name}", color=0x7289DA)
    embed.add_field(name="🆔 ID", value=üye.id, inline=True)
    embed.add_field(name="📛 Tag", value=str(üye), inline=True)
    embed.add_field(name="🤖 Bot mu?", value="Evet" if üye.bot else "Hayır", inline=True)
    embed.add_field(name="📅 Hesap Açılış", value=üye.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="📥 Sunucuya Giriş", value=üye.joined_at.strftime("%d/%m/%Y") if üye.joined_at else "?", inline=True)
    embed.add_field(name="🎭 Roller", value=" ".join(roller) if roller else "Yok", inline=False)
    embed.set_thumbnail(url=üye.display_avatar.url)
    await ctx.send(embed=embed)

# 5. Rol bilgisi
@bot.command()
async def roleinfo(ctx, *, rol: discord.Role):
    embed = create_embed(f"🎭 {rol.name}", color=rol.color.value)
    embed.add_field(name="🆔 ID", value=rol.id, inline=True)
    embed.add_field(name="👥 Üye Sayısı", value=len(rol.members), inline=True)
    embed.add_field(name="📅 Oluşturulma", value=rol.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="🔺 Pozisyon", value=rol.position, inline=True)
    embed.add_field(name="🎨 Renk", value=str(rol.color), inline=True)
    embed.add_field(name="📌 Mention", value=rol.mention, inline=True)
    await ctx.send(embed=embed)

# 6. Sunucuyu kilitle (tüm kanallar)
@bot.command()
@commands.has_permissions(administrator=True)
async def lockdown(ctx, *, sebep: str = "Yönetici kararı"):
    sayi = 0
    for kanal in ctx.guild.text_channels:
        overwrite = kanal.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await kanal.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        sayi += 1
    embed = create_embed("🔒 SUNUCU KİLİTLENDİ", f"**{sayi} kanal** kilitlendi.\n📋 Sebep: {sebep}", 0xFF0000)
    embed.add_field(name="👮 Yetkili", value=ctx.author.mention, inline=True)
    await ctx.send(embed=embed)

# 7. Sunucu kilidini aç (tüm kanallar)
@bot.command()
@commands.has_permissions(administrator=True)
async def unlockdown(ctx):
    sayi = 0
    for kanal in ctx.guild.text_channels:
        overwrite = kanal.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await kanal.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        sayi += 1
    await ctx.send(embed=create_embed("🔓 SUNUCU AÇILDI", f"**{sayi} kanal** kilidi açıldı.", 0x00FF00))

# 8. Nuke (kanalı sil ve yeniden oluştur)
@bot.command()
@commands.has_permissions(administrator=True)
async def nuke(ctx):
    kanal = ctx.channel
    pozisyon = kanal.position
    yeni = await kanal.clone(reason=f"Nuke: {ctx.author}")
    await kanal.delete()
    await yeni.edit(position=pozisyon)
    embed = create_embed("💥 NUKE!", "Bu kanal temizlendi ve yeniden oluşturuldu.", 0xFF0000)
    await yeni.send(embed=embed)

# 9. ID ile ban (sunucuda olmayan kişi)
@bot.command()
@commands.has_permissions(ban_members=True)
async def hackban(ctx, kullanici_id: int, *, sebep: str = "Belirtilmedi"):
    try:
        kullanici = await bot.fetch_user(kullanici_id)
        await ctx.guild.ban(kullanici, reason=sebep)
        await ctx.send(embed=create_embed("🔨 HACKBAN", f"**{kullanici}** (ID: {kullanici_id}) banlandı.\n📋 Sebep: {sebep}", 0xFF0000))
    except:
        await ctx.send(embed=create_embed("❌ Hata", "Kullanıcı bulunamadı veya banlanamadı.", 0xFF0000))

# 10. Ban listesi
@bot.command()
@commands.has_permissions(ban_members=True)
async def banlist(ctx):
    banlar = [entry async for entry in ctx.guild.bans()]
    if not banlar:
        return await ctx.send(embed=create_embed("📋 Ban Listesi", "Hiç banlı kullanıcı yok.", 0x00FF00))
    liste = "\n".join([f"• **{e.user}** — {e.reason or 'Sebep yok'}" for e in banlar[:20]])
    embed = create_embed(f"📋 Ban Listesi ({len(banlar)} kişi)", liste, 0xFF0000)
    await ctx.send(embed=embed)

# 11. Belirli kullanıcının mesajlarını sil
@bot.command()
@commands.has_permissions(manage_messages=True)
async def purgeuser(ctx, üye: discord.Member, sayi: int = 10):
    silindi = 0
    async for msg in ctx.channel.history(limit=200):
        if msg.author == üye and silindi < sayi:
            await msg.delete()
            silindi += 1
    await ctx.send(embed=create_embed("🗑️ Mesajlar Silindi", f"{üye.mention} adlı üyenin **{silindi}** mesajı silindi.", 0x00FF00), delete_after=5)

# 12. Tüm üyelere rol ver
@bot.command()
@commands.has_permissions(administrator=True)
async def massrole(ctx, *, rol: discord.Role):
    sayi = 0
    async with ctx.typing():
        for üye in ctx.guild.members:
            if not üye.bot and rol not in üye.roles:
                try:
                    await üye.add_roles(rol)
                    sayi += 1
                except:
                    pass
    await ctx.send(embed=create_embed("✅ Mass Rol Verildi", f"**{sayi} üyeye** {rol.mention} rolü verildi.", 0x00FF00))

# 13. Yeni metin kanalı oluştur
@bot.command()
@commands.has_permissions(manage_channels=True)
async def kanal(ctx, *, isim: str):
    yeni = await ctx.guild.create_text_channel(isim)
    await ctx.send(embed=create_embed("✅ Kanal Oluşturuldu", f"{yeni.mention} kanalı oluşturuldu.", 0x00FF00))

# 14. Kanal sil
@bot.command()
@commands.has_permissions(manage_channels=True)
async def kanalsil(ctx, hedef: discord.TextChannel = None):
    hedef = hedef or ctx.channel
    isim = hedef.name
    await hedef.delete()
    if hedef != ctx.channel:
        await ctx.send(embed=create_embed("🗑️ Kanal Silindi", f"**#{isim}** kanalı silindi.", 0xFF0000))

# 15. Yeni rol oluştur
@bot.command()
@commands.has_permissions(manage_roles=True)
async def rololuştur(ctx, isim: str, *, renk: str = "0x99aab5"):
    try:
        renk_obj = discord.Color(int(renk.replace("#", "0x"), 16))
    except:
        renk_obj = discord.Color.default()
    yeni_rol = await ctx.guild.create_role(name=isim, color=renk_obj)
    await ctx.send(embed=create_embed("✅ Rol Oluşturuldu", f"{yeni_rol.mention} rolü oluşturuldu.", 0x00FF00))

# 16. Rol sil
@bot.command()
@commands.has_permissions(manage_roles=True)
async def rolsil(ctx, *, rol: discord.Role):
    isim = rol.name
    await rol.delete()
    await ctx.send(embed=create_embed("🗑️ Rol Silindi", f"**{isim}** rolü silindi.", 0xFF0000))

# 17. AFK sistemi
@bot.command()
async def afk(ctx, *, mesaj: str = "AFK"):
    afk_listesi[ctx.author.id] = mesaj
    await ctx.send(embed=create_embed("💤 AFK Modu Aktif", f"{ctx.author.mention} AFK olarak işaretlendi.\n📝 Mesaj: *{mesaj}*", 0x7289DA))


# 18. Özel embed gönder
@bot.command(name="embed")
@commands.has_permissions(administrator=True)
async def ozel_embed(ctx, *, icerik: str):
    if "|" in icerik:
        baslik, aciklama = icerik.split("|", 1)
        embed = create_embed(baslik.strip(), aciklama.strip(), 0xFF0000)
    else:
        embed = create_embed("📢 Duyuru", icerik.strip(), 0xFF0000)
    await ctx.message.delete()
    await ctx.send(embed=embed)

# 19. Sunucu bilgisi
@bot.command()
async def sunucu(ctx):
    guild = ctx.guild
    embed = create_embed(f"🏠 {guild.name}", color=0x7289DA)
    embed.add_field(name="👑 Sahip", value=guild.owner.mention if guild.owner else "?", inline=True)
    embed.add_field(name="👥 Üye", value=guild.member_count, inline=True)
    embed.add_field(name="💬 Kanal", value=len(guild.channels), inline=True)
    embed.add_field(name="🎭 Rol", value=len(guild.roles), inline=True)
    embed.add_field(name="😎 Emoji", value=len(guild.emojis), inline=True)
    embed.add_field(name="📅 Kuruluş", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await ctx.send(embed=embed)

# 20. Bot istatistikleri
@bot.command()
async def botbilgi(ctx):
    embed = create_embed("🤖 VEXIS BOT", color=0xFF0000)
    embed.add_field(name="🏓 Ping", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="👥 Sunucu", value=len(bot.guilds), inline=True)
    embed.add_field(name="👤 Toplam Üye", value=sum(g.member_count for g in bot.guilds), inline=True)
    embed.add_field(name="📌 Prefix", value="`.`", inline=True)
    embed.add_field(name="🔧 Geliştirici", value="plutoxstar", inline=True)
    embed.add_field(name="📚 Kütüphane", value="discord.py", inline=True)
    if bot.user.avatar:
        embed.set_thumbnail(url=bot.user.avatar.url)
    await ctx.send(embed=embed)

# ====================== LOG SİSTEMİ ======================
LOG_KANAL_ID = 1489845976645763132

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    kanal = bot.get_channel(LOG_KANAL_ID)
    if not kanal:
        return
    embed = create_embed("🗑️ Mesaj Silindi", color=0xFF4444)
    embed.add_field(name="👤 Kullanıcı", value=f"{message.author.mention} (`{message.author}`)", inline=True)
    embed.add_field(name="💬 Kanal", value=message.channel.mention, inline=True)
    embed.add_field(name="📝 Silinen Mesaj", value=message.content or "*[İçerik yok / Dosya]*", inline=False)
    embed.set_thumbnail(url=message.author.display_avatar.url)
    await kanal.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    if before.content == after.content:
        return
    kanal = bot.get_channel(LOG_KANAL_ID)
    if not kanal:
        return
    embed = create_embed("✏️ Mesaj Düzenlendi", color=0xFFAA00)
    embed.add_field(name="👤 Kullanıcı", value=f"{before.author.mention} (`{before.author}`)", inline=True)
    embed.add_field(name="💬 Kanal", value=before.channel.mention, inline=True)
    embed.add_field(name="📝 Eski Mesaj", value=before.content or "*[boş]*", inline=False)
    embed.add_field(name="✅ Yeni Mesaj", value=after.content or "*[boş]*", inline=False)
    embed.add_field(name="🔗 Mesaja Git", value=f"[Tıkla]({after.jump_url})", inline=False)
    embed.set_thumbnail(url=before.author.display_avatar.url)
    await kanal.send(embed=embed)

@bot.event
async def on_member_join(member):
    # LOG kanalına bildir
    kanal = bot.get_channel(LOG_KANAL_ID)
    if kanal:
        embed = create_embed("📥 Üye Katıldı", color=0x00FF00)
        embed.add_field(name="👤 Kullanıcı", value=f"{member.mention} (`{member}`)", inline=True)
        embed.add_field(name="🆔 ID", value=member.id, inline=True)
        embed.add_field(name="📅 Hesap Açılış", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        await kanal.send(embed=embed)

    # Kayıt kanalına bildir
    kayit_kanal = bot.get_channel(1479997187810394313)
    if kayit_kanal:
        kayit_rol = discord.utils.get(member.guild.roles, name="Kayıt Yetkilisi")
        rol_mention = kayit_rol.mention if kayit_rol else "@Kayıt Yetkilisi"
        embed = create_embed("📥 Yeni Üye!", f"{member.mention} sunucumuza katıldı!", 0x00FF00)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="🆔 ID", value=member.id, inline=True)
        embed.add_field(name="📅 Hesap Açılış", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
        await kayit_kanal.send(
            content=f"{rol_mention} Yeni Bir Üye Sunucumuza Katıldı Göreviniz Bu Üyeyi Kayıt Etmektir",
            embed=embed
        )

@bot.event
async def on_member_remove(member):
    kanal = bot.get_channel(LOG_KANAL_ID)
    if not kanal:
        return
    embed = create_embed("📤 Üye Ayrıldı", color=0xFF4444)
    embed.add_field(name="👤 Kullanıcı", value=f"`{member}`", inline=True)
    embed.add_field(name="🆔 ID", value=member.id, inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    await kanal.send(embed=embed)

@bot.event
async def on_member_ban(guild, user):
    kanal = bot.get_channel(LOG_KANAL_ID)
    if not kanal:
        return
    embed = create_embed("🔨 Üye Banlandı", color=0xFF0000)
    embed.add_field(name="👤 Kullanıcı", value=f"`{user}`", inline=True)
    embed.add_field(name="🆔 ID", value=user.id, inline=True)
    embed.set_thumbnail(url=user.display_avatar.url)
    await kanal.send(embed=embed)

@bot.event
async def on_member_unban(guild, user):
    kanal = bot.get_channel(LOG_KANAL_ID)
    if not kanal:
        return
    embed = create_embed("✅ Ban Kaldırıldı", color=0x00FF00)
    embed.add_field(name="👤 Kullanıcı", value=f"`{user}`", inline=True)
    embed.add_field(name="🆔 ID", value=user.id, inline=True)
    embed.set_thumbnail(url=user.display_avatar.url)
    await kanal.send(embed=embed)

@bot.event
async def on_member_update(before, after):
    kanal = bot.get_channel(LOG_KANAL_ID)
    if not kanal:
        return
    if before.roles != after.roles:
        eklenen = [r for r in after.roles if r not in before.roles]
        alinan = [r for r in before.roles if r not in after.roles]
        if eklenen or alinan:
            embed = create_embed("🎭 Rol Güncellendi", color=0x7289DA)
            embed.add_field(name="👤 Kullanıcı", value=f"{after.mention} (`{after}`)", inline=False)
            if eklenen:
                embed.add_field(name="➕ Eklenen Rol", value=", ".join(r.mention for r in eklenen), inline=True)
            if alinan:
                embed.add_field(name="➖ Alınan Rol", value=", ".join(r.mention for r in alinan), inline=True)
            embed.set_thumbnail(url=after.display_avatar.url)
            await kanal.send(embed=embed)
    if before.nick != after.nick:
        embed = create_embed("📝 Nickname Değişti", color=0xFFAA00)
        embed.add_field(name="👤 Kullanıcı", value=f"{after.mention} (`{after}`)", inline=False)
        embed.add_field(name="Eski Nick", value=before.nick or "*Yok*", inline=True)
        embed.add_field(name="Yeni Nick", value=after.nick or "*Yok*", inline=True)
        embed.set_thumbnail(url=after.display_avatar.url)
        await kanal.send(embed=embed)

@bot.event
async def on_guild_channel_create(channel):
    kanal = bot.get_channel(LOG_KANAL_ID)
    if not kanal:
        return
    embed = create_embed("📢 Kanal Oluşturuldu", color=0x00FF00)
    embed.add_field(name="Kanal", value=f"{channel.mention} (`{channel.name}`)", inline=True)
    embed.add_field(name="Tür", value=str(channel.type).capitalize(), inline=True)
    await kanal.send(embed=embed)

@bot.event
async def on_guild_channel_delete(channel):
    kanal = bot.get_channel(LOG_KANAL_ID)
    if not kanal:
        return
    embed = create_embed("🗑️ Kanal Silindi", color=0xFF4444)
    embed.add_field(name="Kanal Adı", value=f"`{channel.name}`", inline=True)
    embed.add_field(name="Tür", value=str(channel.type).capitalize(), inline=True)
    await kanal.send(embed=embed)

# ====================== REKLAM ENGELİ ======================
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    uid = str(message.author.id)
    data["mesaj_sayisi"][uid] = data["mesaj_sayisi"].get(uid, 0) + 1
    if data["reklamengel"] and not message.author.guild_permissions.administrator:
        if "discord.gg/" in message.content.lower() or "discord.com/invite/" in message.content.lower():
            await message.delete()
            await message.channel.send(embed=create_embed("🚫 Reklam Engellendi", f"{message.author.mention} reklam paylaşamazsın!", 0xFF0000), delete_after=5)
            return
    if message.author.id in afk_listesi:
        afk_listesi.pop(message.author.id)
        await message.channel.send(embed=create_embed("👋 Hoş Geldin!", f"{message.author.mention} AFK modundan çıktı.", 0x00FF00), delete_after=5)
    for mention in message.mentions:
        if mention.id in afk_listesi:
            await message.channel.send(embed=create_embed(f"💤 {mention.display_name} AFK", f"📝 {afk_listesi[mention.id]}", 0xFFAA00), delete_after=10)
    await bot.process_commands(message)

# ====================== HATA YÖNETİMİ ======================
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=create_embed("❌ Yetki Yok", "Bu komutu kullanmak için yetkin yok!", 0xFF0000))
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send(embed=create_embed("❌ Kullanıcı Bulunamadı", "Belirtilen kullanıcı bulunamadı.", 0xFF0000))
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=create_embed("❌ Eksik Argüman", f"Kullanım: `.{ctx.command.name} {ctx.command.signature}`", 0xFF0000))
    elif isinstance(error, commands.BadArgument):
        await ctx.send(embed=create_embed("❌ Hatalı Argüman", "Lütfen geçerli bir değer gir.", 0xFF0000))

# ====================== TOKEN ======================
bot.run(os.getenv("TOKEN"))
