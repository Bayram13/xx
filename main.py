from telethon import TelegramClient, events
import re
import json
import os

# === Fill these ===
api_id = 22495552
api_hash = 'acfb3602ca2174e966f5995eaf05ba31'
channel_a = 'https://t.me/sol_scan'  # Sənin öz kanalın (paylaşdığın coinlər)
channel_b = 'https://t.me/solgng'

MY_TOKENS_FILE = 'my_tokens.json'

# === Telethon client ===
client = TelegramClient('session_name', api_id, api_hash)


# === Köməkçi: CA çıxartmaq ===
def extract_ca(text):
    m = re.search(r"\b([1-9A-HJ-NP-Za-km-z]{32,44})\b", text)  # Solana CA
    if not m:
        m = re.search(r"\b(0x[a-fA-F0-9]{35,45})\b", text)      # Ethereum CA
    return m.group(1) if m else None


# === Mənim token siyahım ===
def load_my_tokens():
    if os.path.exists(MY_TOKENS_FILE):
        with open(MY_TOKENS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_my_tokens(tokens):
    with open(MY_TOKENS_FILE, 'w') as f:
        json.dump(tokens, f)

my_tokens = load_my_tokens()


# === Şərt filterləri ===
def message_matches_conditions(text: str) -> bool:
    if not text:
        return False

    mc = re.search(r"MC:\s*\$?(\d+(\.\d+)?)", text, re.IGNORECASE)
    if mc and float(mc.group(1)) > 15:
        return True

    dev = re.search(r"Dev hold:\s*(\d+(\.\d+)?)", text, re.IGNORECASE)
    if dev and float(dev.group(1)) < 3:
        return True

    holders = re.search(r"Holders:\s*(\d+(\.\d+)?)", text, re.IGNORECASE)
    if holders and float(holders.group(1)) > 30:
        return True

    top10 = re.search(r"Top 10 Holders:\s*(\d+(\.\d+)?)", text, re.IGNORECASE)
    if top10 and float(top10.group(1)) < 20:
        return True

    return False


# === 1️⃣ Öz kanalından paylaşdığın tokenləri yadda saxla ===
@client.on(events.NewMessage(chats=channel_a))
async def save_my_token(event):
    text = event.raw_text
    ca = extract_ca(text)
    if ca and ca not in my_tokens:
        my_tokens.append(ca)
        save_my_tokens(my_tokens)
        print(f"💾 Yeni token yadda saxlandı: {ca}")


# === 2️⃣ 2x+, filter keçən və mənim tokenlərim olan mesajları göndər ===
@client.on(events.NewMessage)
async def forward_filtered_messages(event):
    text = event.raw_text
    if not text:
        return

    # 2x, 3x, 4x varsa
    has_x = re.search(r'\b\d+x\b', text.lower())
    if not has_x:
        return

    # CA tap
    ca = extract_ca(text)
    if not ca:
        return

    # Mənim tokenlərimdədirsə və filterlərdən keçibsə
    if ca in my_tokens and message_matches_conditions(text):
        # "Follow" sətirlərini sil
        cleaned_text = "\n".join(
            [line for line in text.splitlines() if "follow" not in line.lower()]
        ).strip()

        # LINK əlavə et
        cleaned_text += f"\n\nLINK: https://pump.fun/coin/{ca}"

        try:
            await client.send_message(channel_b, cleaned_text)
            print(f"🚀 Forwarded filtered 2x+ message for your token: {ca}")
        except Exception as e:
            print("❌ Error forwarding:", e)


print("👀 Dinlənilir... Öz tokenlər və 2x+ filterli mesajlar üçün aktivdir.")
with client:
    client.run_until_disconnected()
