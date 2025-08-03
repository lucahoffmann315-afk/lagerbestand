import os
import discord
from discord.ext import commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from keep_alive import keep_alive

keep_alive()

# Google Sheets Verbindung
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(
    "10XJ0Ur6gEkqABMVh9xbDVvL3AvLLfQA4de5AwpDXei8").sheet1

# Discord Bot Setup mit benötigtem Intent für Nachrichteninhalte
intents = discord.Intents.default()
intents.message_content = True  # Sehr wichtig, damit Commands funktionieren!
bot = commands.Bot(command_prefix="!", intents=intents)

# Speichert die letzte Bot-Nachricht pro Channel, um sie zu löschen
last_bot_messages = {}

# 🔧 Neue Bestands-Logik ohne Zwischenwert
def get_bestands_emoji(bestand):
    try:
        bestand = int(bestand)

        if bestand <= 50:
            return "🔴 Nicht mehr auf Lager"
        elif bestand <= 150:
            return "🟡 Begrenzte Mengen"
        elif bestand < 2000:
            return "⚪ Normale Mengen"
        else:
            return "🟢 Große Mengen"
    except Exception:
        return "❓ Fehlerhafte Zahl"


@bot.event
async def on_ready():
    print(f"✅ Bot ist online als {bot.user}")


@bot.command(name="bestand")
async def bestand(ctx):
    try:
        # Alte Bot-Nachricht löschen, falls vorhanden
        last_message = last_bot_messages.get(ctx.channel.id)
        if last_message:
            try:
                await last_message.delete()
            except discord.NotFound:
                pass
            except discord.Forbidden:
                await ctx.send("❌ Ich habe keine Berechtigung, Nachrichten zu löschen.")
                return

        daten = sheet.get_all_records()
        embed = discord.Embed(title="📦 Lagerbestand Übersicht", color=0x1ABC9C)

        for eintrag in daten:
            name = eintrag.get("Produktname", "Unbekannt")
            menge = eintrag.get("Bestand", "0")
            preis = eintrag.get("Preis", "Unbekannt")
            status = get_bestands_emoji(menge)
            embed.add_field(name=name,
                            value=f"{menge} Stück – {status}\n💰 Preis: {preis} $",
                            inline=False)

        new_message = await ctx.send(embed=embed)
        last_bot_messages[ctx.channel.id] = new_message

    except Exception as e:
        print(f"Fehler beim Abrufen: {e}")
        await ctx.send("❌ Es ist ein unerwarteter Fehler aufgetreten beim Abrufen der Daten.")


if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ Kein Discord-Token gefunden. Bitte Umgebungsvariable DISCORD_TOKEN setzen.")
        exit(1)
    bot.run(token)
