import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
import time
import threading

# Tus credenciales guardadas
TOKEN = "6540303676:AAFAbp7EX7rXSCzKad03NBblYea-dd9rJ00"
bot = telebot.TeleBot(TOKEN)

# Diccionario para guardar la configuración de cada usuario
configuraciones_usuario = {}

# Conjunto para guardar los ASIN (IDs) de productos ya notificados y no repetir
productos_ya_enviados = set()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9"
}

def obtener_o_crear_config(chat_id):
    if chat_id not in configuraciones_usuario:
        configuraciones_usuario[chat_id] = {
            "categoria": "Todas",
            "marca": "Todas",       
            "descuento": 20,       
            "precio_max": 500,
            "activo": False
        }
    return configuraciones_usuario[chat_id]

# 1. Comando /start o /menu
@bot.message_handler(commands=['start', 'menu'])
def enviar_menu(message):
    chat_id = message.chat.id
    conf = obtener_o_crear_config(chat_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_cat = types.InlineKeyboardButton("📁 Categoría", callback_data="config_cat")
    btn_marca = types.InlineKeyboardButton("🏷️ Marca", callback_data="config_marca")
    btn_desc = types.InlineKeyboardButton("📉 % Descuento Mín.", callback_data="config_desc")
    btn_precio = types.InlineKeyboardButton("💰 Precio Máximo", callback_data="config_precio")
    btn_iniciar = types.InlineKeyboardButton("🚀 Iniciar Búsqueda", callback_data="iniciar_busqueda")
    btn_parar = types.InlineKeyboardButton("⏹️ Parar Búsqueda", callback_data="parar_busqueda")
    
    markup.add(btn_cat, btn_marca, btn_desc, btn_precio, btn_iniciar, btn_parar)
    
    estado_texto = "🟢 ACTIVA" if conf["activo"] else "🔴 DETENIDA"
    
    texto = (
        f"🤖 **Tu Rastreador Inteligente de Amazon**\n\n"
        f"Configuración actual:\n"
        f"• Categoría: `{conf['categoria']}`\n"
        f"• Marca: `{conf['marca']}`\n"
        f"• Descuento mín: `{conf['descuento']}%`\n"
        f"• Precio máximo: `{conf['precio_max']} €`\n"
        f"• Estado: {estado_texto}\n\n"
        f"Elige una opción:"
    )
    
    bot.send_message(chat_id, texto, parse_mode="Markdown", reply_markup=markup)

# 2. Gestionar los clics de los botones
@bot.callback_query_handler(func=lambda call: True)
def manejar_botones(call):
    chat_id = call.message.chat.id
    conf = obtener_o_crear_config(chat_id)
    
    if call.data == "config_cat":
        bot.answer_callback_query(call.id, "Configurando categoría...")
        msg = bot.send_message(chat_id, "Escribe la categoría que quieres buscar (ej: Portátiles, Televisores, o 'Todas'):")
        bot.register_next_step_handler(msg, guardar_categoria)
        
    elif call.data == "config_marca":
        bot.answer_callback_query(call.id, "Configurando marca...")
        msg = bot.send_message(chat_id, "Escribe la marca que buscas (ej: Sony, Xiaomi) o pon 'Todas':")
        bot.register_next_step_handler(msg, guardar_marca)
        
    elif call.data == "config_desc":
        bot.answer_callback_query(call.id, "Configurando descuento...")
        msg = bot.send_message(chat_id, "Escribe el porcentaje mínimo de descuento en número (ej: 30):")
        bot.register_next_step_handler(msg, guardar_descuento)
        
    elif call.data == "config_precio":
        bot.answer_callback_query(call.id, "Configurando precio máximo...")
        msg = bot.send_message(chat_id, "Escribe el precio máximo en euros (ej: 300):")
        bot.register_next_step_handler(msg, guardar_precio)
        
    elif call.data == "iniciar_busqueda":
        conf["activo"] = True
        bot.answer_callback_query(call.id, "¡Búsqueda iniciada!")
        bot.send_message(chat_id, f"🚀 **¡Búsqueda iniciada!** Vigilando cada 15 min | Categoría: *{conf['categoria']}* | Marca: *{conf['marca']}*.")
        
    elif call.data == "parar_busqueda":
        conf["activo"] = False
        bot.answer_callback_query(call.id, "Búsqueda detenida")
        bot.send_message(chat_id, "⏹️ **Búsqueda detenida.** El bot ha pausado la vigilancia.")

# 3. Funciones para guardar lo que escribes
def guardar_categoria(message):
    chat_id = message.chat.id
    conf = obtener_o_crear_config(chat_id)
    conf["categoria"] = message.text
    bot.send_message(chat_id, f"✅ Categoría actualizada a: **{message.text}**", parse_mode="Markdown")
    enviar_menu(message)

def guardar_marca(message):
    chat_id = message.chat.id
    conf = obtener_o_crear_config(chat_id)
    conf["marca"] = message.text
    bot.send_message(chat_id, f"✅ Marca actualizada a: **{message.text}**", parse_mode="Markdown")
    enviar_menu(message)

def guardar_descuento(message):
    chat_id = message.chat.id
    try:
        desc = int(message.text.replace("%", "").strip())
        conf = obtener_o_crear_config(chat_id)
        conf["descuento"] = desc
        bot.send_message(chat_id, f"✅ Descuento mínimo actualizado a: **{desc}%**", parse_mode="Markdown")
    except ValueError:
        bot.send_message(chat_id, "⚠️ Por favor, introduce un número válido (ej: 30).")
    enviar_menu(message)

def guardar_precio(message):
    chat_id = message.chat.id
    try:
        precio = float(message.text.replace("€", "").replace(",", ".").strip())
        conf = obtener_o_crear_config(chat_id)
        conf["precio_max"] = precio
        bot.send_message(chat_id, f"✅ Precio máximo actualizado a: **{precio} €**", parse_mode="Markdown")
    except ValueError:
        bot.send_message(chat_id, "⚠️ Por favor, introduce un precio válido (ej: 300).")
    enviar_menu(message)

# 4. Función para extraer enlaces
def obtener_productos_categoria(categoria, marca):
    partes_query = []
    if categoria.lower() != "todas":
        partes_query.append(categoria)
    if marca.lower() != "todas":
        partes_query.append(marca)
        
    query = "ofertas" if not partes_query else " ".join(partes_query)
    url_busqueda = f"https://www.amazon.es/s?k={query.replace(' ', '+')}"
    print(f"\n[Buscador] Consultando Amazon: {url_busqueda}")
    
    try:
        respuesta = requests.get(url_busqueda, headers=HEADERS)
        if respuesta.status_code == 200:
            soup = BeautifulSoup(respuesta.text, 'html.parser')
            lista_productos = []
            for item in soup.find_all("div", {"data-asin": True}):
                asin = item.get("data-asin")
                if asin and len(asin) == 10:
                    url_producto = f"https://www.amazon.es/dp/{asin}"
                    if {"asin": asin, "url": url_producto} not in lista_productos:
                        lista_productos.append({"asin": asin, "url": url_producto})
            return lista_productos[:5]
    except Exception as e:
        print(f"❌ Error al buscar en Amazon: {e}")
    return []

# 5. Lógica de comprobación periódica (cada 15 minutos = 900 segundos)
def verificar_ofertas_amazon():
    while True:
        time.sleep(5) 
        for chat_id, conf in list(configuraciones_usuario.items()):
            if conf.get("activo", False):
                print(f"\n--- [Rastreador] Cat: '{conf['categoria']}' | Marca: '{conf['marca']}' (Usuario {chat_id}) ---")
                
                productos = obtener_productos_categoria(conf["categoria"], conf["marca"])
                print(f"Se han encontrado {len(productos)} productos para revisar.")
                
                for prod in productos:
                    asin = prod["asin"]
                    url_prod = prod["url"]
                    
                    if asin in productos_ya_enviados:
                        print(f"-> Producto {asin} ya notificado anteriormente. Omitiendo...")
                        continue
                    
                    try:
                        resp = requests.get(url_prod, headers=HEADERS)
                        if resp.status_code == 200:
                            s = BeautifulSoup(resp.text, 'html.parser')
                            
                            p_entero = s.find("span", class_="a-price-whole")
                            p_decimal = s.find("span", class_="a-price-fraction")
                            
                            if p_entero:
                                ent = p_entero.text.replace(".", "").replace(",", "").strip()
                                dec = p_decimal.text.strip() if p_decimal else "00"
                                precio_actual = float(f"{ent}.{dec}")
                                
                                precio_original = None
                                elem_orig = s.find("span", class_="a-text-price")
                                if elem_orig:
                                    span_off = elem_orig.find("span", class_="a-offscreen")
                                    if span_off:
                                        t_orig = span_off.text.replace("€", "").replace(".", "").replace(",", ".").strip()
                                        try:
                                            precio_original = float(t_orig)
                                        except ValueError:
                                            pass
                                
                                if precio_actual <= conf["precio_max"]:
                                    if precio_original and precio_original > precio_actual:
                                        descuento = 100 - (precio_actual * 100 / precio_original)
                                        
                                        if descuento >= conf["descuento"]:
                                            mensaje = (
                                                f"🚨 ¡CHOLLO NUEVO ENCONTRADO! 🚨\n\n"
                                                f"• Categoría: {conf['categoria']}\n"
                                                f"• Marca: {conf['marca']}\n"
                                                f"• Descuento: **{descuento:.1f}%**\n"
                                                f"• Precio actual: **{precio_actual} €**\n"
                                                f"• Precio original: {precio_original} €\n\n"
                                                f"👉 [Ver chollo en Amazon]({url_prod})"
                                            )
                                            bot.send_message(chat_id, mensaje, parse_mode="Markdown")
                                            print(f"¡Alerta enviada a Telegram y registrado como ya notificado ({asin})!")
                                            
                                            productos_ya_enviados.add(asin)
                                            
                        time.sleep(2)
                    except Exception as e:
                        print(f"Error analizando producto individual: {e}")
                        
        # 900 segundos = 15 minutos exactos
        time.sleep(900)

# Arrancar el hilo en segundo plano
hilo_rastreo = threading.Thread(target=verificar_ofertas_amazon, daemon=True)
hilo_rastreo.start()

# Arrancar el bot con protección
if __name__ == "__main__":
    try:
        print("Bot configurado para buscar cada 15 min en marcha...")
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ El bot se ha detenido por un error: {e}")
        input("Pulsa Intro para salir...")