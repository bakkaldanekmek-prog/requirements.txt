import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio
import random
import json
import os
from datetime import datetime, timedelta
import aiohttp
import yt_dlp

# ====================== BOT ======================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

data = {
    "mesaj_sayisi": {},
    "reklamengel": False,
    "admin_access": {},
    "warnings": {},
    "muted": {},
    "sicil": {},
    "queue": {},
    "voice_clients": {}
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

# ====================== TİCKET SİSTEMİ ======================
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ticket Aç", style=discord.ButtonStyle.green, custom_id="ticket_open")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        user = interaction.user
        
        # Kategori bul
        category = discord.utils.get(guild.categories, id=1490207817745825892)
        if not category:
            return await interaction.response.send_message("❌ Ticket kategorisi bulunamadı!", ephemeral=True)
        
        # Zaten açık ticket var mı kontrol et
        for channel in category.channels:
            if channel.name.startswith(f"ticket-{user.id}"):
                return await interaction.response.send_message(f"❌ Zaten açık bir ticketiniz var: {channel.mention}", ephemeral=True)
        
        # Yeni ticket kanalı oluştur
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{user.id}",
            category=category,
            overwrites=overwrites
        )
        
        embed = create_embed("🎫 Ticket Açıldı", f"Merhaba {user.mention}! Destek ekibimiz sana yardımcı olacak.", 0x00FF00)
        embed.add_field(name="📝 Sorununu Açıkla", value="Lütfen sorununu detaylı bir şekilde anlat.", inline=False)
        
        close_view = TicketCloseView()
        await ticket_channel.send(embed=embed, view=close_view)
        
        await interaction.response.send_message(f"✅ Ticket açıldı: {ticket_channel.mention}", ephemeral=True)

class TicketCloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="❌ Kapat", style=discord.ButtonStyle.red, custom_id="ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        await interaction.channel.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def tpanel(ctx):
    """Ticket paneli gönder"""
    embed = create_embed("🎫 Destek Sistemi", "Aşağıdaki butona tıklayarak bir ticket açabilirsin.", 0x7289DA)
    embed.add_field(name="📋 Nasıl Çalışır?", value="1. Butona tıkla\n2. Sorununu anlat\n3. Destek ekibi sana yardımcı olacak", inline=False)
    view = TicketView()
    await ctx.send(embed=embed, view=view)
    await ctx.message.delete()

# ====================== MÜZİK SİSTEMİ ======================
class MusicPlayer:
    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.queue = []
        self.current = None
        self.volume = 0.5

async def get_youtube_url(query):
    """Spotify/YouTube'dan şarkı bul"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'socket_timeout': 30
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                return info['entries'][0]['url'], info['entries'][0]['title']
            return info['url'], info['title']
    except:
        return None, None

async def play_audio(voice_client, url):
    """Ses çal"""
    try:
        audio_source = discord.FFmpegPCMAudio(url, options="-vn")
        voice_client.play(audio_source)
    except:
        pass

@bot.command()
async def gir(ctx):
    """Sese gir"""
    if not ctx.author.voice:
        return await ctx.send(embed=create_embed("❌ Hata", "Önce bir ses kanalına katıl!", 0xFF0000))
    
    channel = ctx.author.voice.channel
    try:
        voice_client = await channel.connect()
        data["voice_clients"][ctx.guild.id] = voice_client
        data["queue"][ctx.guild.id] = MusicPlayer(ctx.guild.id)
        await ctx.send(embed=create_embed("✅ Bağlandı", f"{channel.mention} ses kanalına bağlandım!", 0x00FF00))
    except:
        await ctx.send(embed=create_embed("❌ Hata", "Ses kanalına bağlanamadım!", 0xFF0000))

@bot.command()
async def çık(ctx):
    """Sesten çık"""
    if ctx.guild.id not in data["voice_clients"]:
        return await ctx.send(embed=create_embed("❌ Hata", "Hiçbir ses kanalında değilim!", 0xFF0000))
    
    voice_client = data["voice_clients"][ctx.guild.id]
    await voice_client.disconnect()
    del data["voice_clients"][ctx.guild.id]
    if ctx.guild.id in data["queue"]:
        del data["queue"][ctx.guild.id]
    await ctx.send(embed=create_embed("✅ Ayrıldı", "Ses kanalından ayrıldım!", 0x00FF00))

@bot.command()
async def oynat(ctx, *, sarki: str):
    """Şarkı çal"""
    if ctx.guild.id not in data["voice_clients"]:
        return await ctx.send(embed=create_embed("❌ Hata", "Önce `.gir` komutunu kullan!", 0xFF0000))
    
    bekle = await ctx.send(embed=create_embed("🔍 Aranıyor", f"**{sarki}** aranıyor...", 0x7289DA))
    
    url, title = await get_youtube_url(sarki)
    if not url:
        return await bekle.edit(embed=create_embed("❌ Hata", "Şarkı bulunamadı!", 0xFF0000))
    
    voice_client = data["voice_clients"][ctx.guild.id]
    player = data["queue"][ctx.guild.id]
    
    player.queue.append({"url": url, "title": title, "requester": ctx.author})
    
    if not voice_client.is_playing():
        song = player.queue.pop(0)
        player.current = song
        await play_audio(voice_client, song["url"])
        embed = create_embed("🎵 Çalıyor", f"**{song['title']}**\n👤 İsteyen: {song['requester'].mention}", 0x00FF00)
        await bekle.edit(embed=embed)
    else:
        embed = create_embed("➕ Kuyruğa Eklendi", f"**{title}**\n📍 Sıra: **{len(player.queue) + 1}**", 0x7289DA)
        await bekle.edit(embed=embed)

@bot.command()
async def sıra(ctx):
    """Müzik sırası"""
    if ctx.guild.id not in data["queue"]:
        return await ctx.send(embed=create_embed("❌ Hata", "Müzik çalmıyor!", 0xFF0000))
    
    player = data["queue"][ctx.guild.id]
    
    if not player.current and not player.queue:
        return await ctx.send(embed=create_embed("❌ Hata", "Kuyruk boş!", 0xFF0000))
    
    embed = create_embed("🎵 Müzik Sırası", color=0x7289DA)
    
    if player.current:
        embed.add_field(name="▶️ Şu Anda Çalıyor", value=f"**{player.current['title']}**\n👤 {player.current['requester'].mention}", inline=False)
    
    if player.queue:
        queue_text = "\n".join([f"`{i+1}.` **{song['title']}** - {song['requester'].mention}" for i, song in enumerate(player.queue[:10])])
        embed.add_field(name="📋 Kuyruk", value=queue_text, inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def ses(ctx, seviye: int):
    """Ses seviyesi ayarla (0-100)"""
    if ctx.guild.id not in data["queue"]:
        return await ctx.send(embed=create_embed("❌ Hata", "Müzik çalmıyor!", 0xFF0000))
    
    if seviye < 0 or seviye > 100:
        return await ctx.send(embed=create_embed("❌ Hata", "Ses seviyesi 0-100 arasında olmalı!", 0xFF0000))
    
    player = data["queue"][ctx.guild.id]
    player.volume = seviye / 100
    await ctx.send(embed=create_embed("🔊 Ses Ayarlandı", f"Ses seviyesi: **{seviye}%**", 0x00FF00))

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
    embed.add_field(name="🎵 Müzik", value="`gir` `çık` `oynat [şarkı]` `sıra` `ses [0-100]`", inline=False)
    embed.add_field(name="🤖 Yapay Zeka", value="`asistan [mesaj]` — AI sohbet\n`gorsel [açıklama]` — AI görsel", inline=False)
    embed.add_field(name="🎫 Ticket", value="`tpanel` — Ticket paneli gönder", inline=False)
    embed.add_field(name="📋 Kayıt", value="`ket @üye Nick` — Kayıt sistemi", inline=False)
    await ctx.send(embed=embed)

# ====================== GENEL KOMUTLAR ======================
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(embed=create_embed("🏓 Pong!", f"Gecikme: `{latency}ms`", 0x00FF00))

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
    
import discord
from discord.ext import commands
from discord.ui import Button, View
import asyncio
import random
import json
import os
from datetime import datetime, timedelta
import aiohttp
import yt_dlp

# ====================== BOT ======================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

data = {
    "mesaj_sayisi": {},
    "reklamengel": False,
    "admin_access": {},
    "warnings": {},
    "muted": {},
    "sicil": {},
    "queue": {},
    "voice_clients": {}
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

# ====================== TİCKET SİSTEMİ ======================
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ticket Aç", style=discord.ButtonStyle.green, custom_id="ticket_open")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        user = interaction.user
        
        # Kategori bul
        category = discord.utils.get(guild.categories, id=1490207817745825892)
        if not category:
            return await interaction.response.send_message("❌ Ticket kategorisi bulunamadı!", ephemeral=True)
        
        # Zaten açık ticket var mı kontrol et
        for channel in category.channels:
            if channel.name.startswith(f"ticket-{user.id}"):
                return await interaction.response.send_message(f"❌ Zaten açık bir ticketiniz var: {channel.mention}", ephemeral=True)
        
        # Yeni ticket kanalı oluştur
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{user.id}",
            category=category,
            overwrites=overwrites
        )
        
        embed = create_embed("🎫 Ticket Açıldı", f"Merhaba {user.mention}! Destek ekibimiz sana yardımcı olacak.", 0x00FF00)
        embed.add_field(name="📝 Sorununu Açıkla", value="Lütfen sorununu detaylı bir şekilde anlat.", inline=False)
        
        close_view = TicketCloseView()
        await ticket_channel.send(embed=embed, view=close_view)
        
        await interaction.response.send_message(f"✅ Ticket açıldı: {ticket_channel.mention}", ephemeral=True)

class TicketCloseView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="❌ Kapat", style=discord.ButtonStyle.red, custom_id="ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        await interaction.channel.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def tpanel(ctx):
    """Ticket paneli gönder"""
    embed = create_embed("🎫 Destek Sistemi", "Aşağıdaki butona tıklayarak bir ticket açabilirsin.", 0x7289DA)
    embed.add_field(name="📋 Nasıl Çalışır?", value="1. Butona tıkla\n2. Sorununu anlat\n3. Destek ekibi sana yardımcı olacak", inline=False)
    view = TicketView()
    await ctx.send(embed=embed, view=view)
    await ctx.message.delete()

# ====================== MÜZİK SİSTEMİ ======================
class MusicPlayer:
    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.queue = []
        self.current = None
        self.volume = 0.5

async def get_youtube_url(query):
    """Spotify/YouTube'dan şarkı bul"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'socket_timeout': 30
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                return info['entries'][0]['url'], info['entries'][0]['title']
            return info['url'], info['title']
    except:
        return None, None

async def play_audio(voice_client, url):
    """Ses çal"""
    try:
        audio_source = discord.FFmpegPCMAudio(url, options="-vn")
        voice_client.play(audio_source)
    except:
        pass

@bot.command()
async def gir(ctx):
    """Sese gir"""
    if not ctx.author.voice:
        return await ctx.send(embed=create_embed("❌ Hata", "Önce bir ses kanalına katıl!", 0xFF0000))
    
    channel = ctx.author.voice.channel
    try:
        voice_client = await channel.connect()
        data["voice_clients"][ctx.guild.id] = voice_client
        data["queue"][ctx.guild.id] = MusicPlayer(ctx.guild.id)
        await ctx.send(embed=create_embed("✅ Bağlandı", f"{channel.mention} ses kanalına bağlandım!", 0x00FF00))
    except:
        await ctx.send(embed=create_embed("❌ Hata", "Ses kanalına bağlanamadım!", 0xFF0000))

@bot.command()
async def çık(ctx):
    """Sesten çık"""
    if ctx.guild.id not in data["voice_clients"]:
        return await ctx.send(embed=create_embed("❌ Hata", "Hiçbir ses kanalında değilim!", 0xFF0000))
    
    voice_client = data["voice_clients"][ctx.guild.id]
    await voice_client.disconnect()
    del data["voice_clients"][ctx.guild.id]
    if ctx.guild.id in data["queue"]:
        del data["queue"][ctx.guild.id]
    await ctx.send(embed=create_embed("✅ Ayrıldı", "Ses kanalından ayrıldım!", 0x00FF00))

@bot.command()
async def oynat(ctx, *, sarki: str):
    """Şarkı çal"""
    if ctx.guild.id not in data["voice_clients"]:
        return await ctx.send(embed=create_embed("❌ Hata", "Önce `.gir` komutunu kullan!", 0xFF0000))
    
    bekle = await ctx.send(embed=create_embed("🔍 Aranıyor", f"**{sarki}** aranıyor...", 0x7289DA))
    
    url, title = await get_youtube_url(sarki)
    if not url:
        return await bekle.edit(embed=create_embed("❌ Hata", "Şarkı bulunamadı!", 0xFF0000))
    
    voice_client = data["voice_clients"][ctx.guild.id]
    player = data["queue"][ctx.guild.id]
    
    player.queue.append({"url": url, "title": title, "requester": ctx.author})
    
    if not voice_client.is_playing():
        song = player.queue.pop(0)
        player.current = song
        await play_audio(voice_client, song["url"])
        embed = create_embed("🎵 Çalıyor", f"**{song['title']}**\n👤 İsteyen: {song['requester'].mention}", 0x00FF00)
        await bekle.edit(embed=embed)
    else:
        embed = create_embed("➕ Kuyruğa Eklendi", f"**{title}**\n📍 Sıra: **{len(player.queue) + 1}**", 0x7289DA)
        await bekle.edit(embed=embed)

@bot.command()
async def sıra(ctx):
    """Müzik sırası"""
    if ctx.guild.id not in data["queue"]:
        return await ctx.send(embed=create_embed("❌ Hata", "Müzik çalmıyor!", 0xFF0000))
    
    player = data["queue"][ctx.guild.id]
    
    if not player.current and not player.queue:
        return await ctx.send(embed=create_embed("❌ Hata", "Kuyruk boş!", 0xFF0000))
    
    embed = create_embed("🎵 Müzik Sırası", color=0x7289DA)
    
    if player.current:
        embed.add_field(name="▶️ Şu Anda Çalıyor", value=f"**{player.current['title']}**\n👤 {player.current['requester'].mention}", inline=False)
    
    if player.queue:
        queue_text = "\n".join([f"`{i+1}.` **{song['title']}** - {song['requester'].mention}" for i, song in enumerate(player.queue[:10])])
        embed.add_field(name="📋 Kuyruk", value=queue_text, inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def ses(ctx, seviye: int):
    """Ses seviyesi ayarla (0-100)"""
    if ctx.guild.id not in data["queue"]:
        return await ctx.send(embed=create_embed("❌ Hata", "Müzik çalmıyor!", 0xFF0000))
    
    if seviye < 0 or seviye > 100:
        return await ctx.send(embed=create_embed("❌ Hata", "Ses seviyesi 0-100 arasında olmalı!", 0xFF0000))
    
    player = data["queue"][ctx.guild.id]
    player.volume = seviye / 100
    await ctx.send(embed=create_embed("🔊 Ses Ayarlandı", f"Ses seviyesi: **{seviye}%**", 0x00FF00))

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
    embed.add_field(name="🎵 Müzik", value="`gir` `çık` `oynat [şarkı]` `sıra` `ses [0-100]`", inline=False)
    embed.add_field(name="🤖 Yapay Zeka", value="`asistan [mesaj]` — AI sohbet\n`gorsel [açıklama]` — AI görsel", inline=False)
    embed.add_field(name="🎫 Ticket", value="`tpanel` — Ticket paneli gönder", inline=False)
    embed.add_field(name="📋 Kayıt", value="`ket @üye Nick` — Kayıt sistemi", inline=False)
    await ctx.send(embed=embed)

# ====================== GENEL KOMUTLAR ======================
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(embed=create_embed("🏓 Pong!", f"Gecikme: `{latency}ms`", 0x00FF00))

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

# ====================== YAPAY ZEKA - ASISTAN ======================
@bot.command()
async def asistan(ctx, *, mesaj: str):
    """Yapay zeka asistanı ile sohbet"""
    bekle = await ctx.send(embed=create_embed("🤖 Düşünüyor...", "Yapay zeka cevap hazırlıyor...", 0x7289DA))
    try:
        payload = {
            "model": "openai",
            "messages": [
                {"role": "system", "content": "Sen Vexis adlı bir Discord bot asistanısın. Türkçe konuşursun. Kısa, samimi ve yardımsever cevaplar verirsin. Kullanıcı ile dostça sohbet et."},
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
        embed = create_embed("🤖 Vexis Asistanı", cevap, 0x7289DA)
        embed.add_field(name="💬 Soru", value=mesaj, inline=False)
        embed.set_footer(text=f"Soran: {ctx.author} • Vexis Bot")
        await bekle.edit(embed=embed)
    except Exception as e:
        await bekle.edit(embed=create_embed("❌ Hata", f"Asistan şu an yanıt veremiyor. Tekrar dene!", 0xFF0000))

# ====================== YAPAY ZEKA - GÖRSEL ======================
@bot.command()
async def gorsel(ctx, *, aciklama: str):
    """Yapay zeka ile görsel oluştur"""
    bekle = await ctx.send(embed=create_embed("🎨 Görsel Oluşturuluyor...", f"**{aciklama}** için görsel oluşturuluyor...", 0x7289DA))
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://image.pollinations.ai/prompt/{aciklama}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status == 200:
                    image_url = str(resp.url)
                    embed = create_embed("🎨 Yapay Zeka Görseli", aciklama, 0x7289DA)
                    embed.set_image(url=image_url)
                    embed.set_footer(text=f"İsteyen: {ctx.author} • Vexis Bot")
                    await bekle.edit(embed=embed)
                else:
                    await bekle.edit(embed=create_embed("❌ Hata", "Görsel oluşturulamadı!", 0xFF0000))
    except Exception as e:
        await bekle.edit(embed=create_embed("❌ Hata", f"Görsel oluşturma başarısız oldu!", 0xFF0000))

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
            return await interaction.response.send_message(f"❌ `{rol_adi}` rolü bulunamadı!", ephemeral=True)
        
        # Kayıtsız rolünü al
        kayitsiz_rol = discord.utils.get(guild.roles, name="Kayıtsız")
        if kayitsiz_rol and kayitsiz_rol in self.member.roles:
            await self.member.remove_roles(kayitsiz_rol)
        
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
        return await ctx.send(embed=create_embed("⚠️ Zaten Kayıtlı", f"{member.mention} zaten kayıtlı!", 0xFFAA00))
    embed = create_embed("📋 Kayıt Paneli", f"**{member.mention}** için rol seçin:\n👤 Nick: **{nick or 'Belirtilmedi'}**", 0x7289DA)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="🆔 ID", value=member.id, inline=True)
    embed.add_field(name="📅 Hesap Açılış", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
    view = KayitView(member, nick, ctx.author)
    await ctx.send(embed=embed, view=view)

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

# ====================== HATA YÖNETİMİ ======================
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=create_embed("❌ Yetki Yok", "Bu komutu kullanmak için yetkiniz yok!", 0xFF0000))
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=create_embed("❌ Hata", f"Eksik argüman: {error.param}", 0xFF0000))
    elif isinstance(error, commands.BadArgument):
        await ctx.send(embed=create_embed("❌ Hata", "Geçersiz argüman!", 0xFF0000))
    else:
        print(f"Hata: {error}")

# ====================== BOT BAŞLAT ======================
token = os.getenv("MTQ4ODg5MDA1OTY4Mjg3NzYxMg.GmjnS1.ObYP0YlscmGeEF03700fhq8e-XciKdJb03gKis")
if not token:
    raise ValueError("DISCORD_TOKEN environment variable not set")
bot.run(MTQ4ODg5MDA1OTY4Mjg3NzYxMg.GmjnS1.ObYP0YlscmGeEF03700fhq8e-XciKdJb03gKis)

