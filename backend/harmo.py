import mysql.connector
import os
from dotenv import load_dotenv
import datetime
import discord
import firebase_admin
from firebase_admin import credentials, messaging
import json

load_dotenv()
cred = credentials.Certificate("firebase.json")
# SQL data
DATABASE = os.getenv('DB')
HOST = "localhost"
USER = "python"
PASSWORD = os.getenv('PASS')
TOKEN = os.getenv("DISCORD")
current = datetime.datetime.now()

# Baza
mydb = mysql.connector.connect(
    host=HOST,
    port=3306,
    user=USER,
    password=PASSWORD,
    database=DATABASE)

mycursor = mydb.cursor()

# Przetwarzanie danych z harmonogramu tylko o 3 rano
if current.strftime("%H")=='03':
    mycursor.execute("SELECT * FROM harmonogram;")
    harmoData = mycursor.fetchall()
    for row in harmoData:
        name = row[1]
        dni = json.loads(row[2])
        user = row[3]
        id = row[0]
        lastAdded = f"{row[5]:%Y-%m-%d}"
        if (dni["type"]=="daily"):
            timeStart = datetime.datetime.strptime(dni["date"], "%Y-%m-%d")
            if current>timeStart:
                lastAdded = datetime.datetime.strptime(lastAdded, "%Y-%m-%d")
                interval = int(dni["interval"])
                if (current >=  lastAdded +  datetime.timedelta(days=interval) or (f"{current:%Y-%m-%d}"==f"{timeStart:%Y-%m-%d}")):
                    date = f"{current:%Y-%m-%d} {dni["time"]}"
                    nazwa = f"{name} - {date}"
                    sql = f"INSERT INTO zadania (status, data, nazwa, parentID, uzytkownik) VALUES (0, '{date}', '{nazwa}', 0, {user});"
                    mycursor.execute(sql)
                    sql = f"UPDATE harmonogram SET lastAdded='{date}' WHERE ID={id};"
                    mycursor.execute(sql)
        else:
            days = dni["days"]
            lastAdded = datetime.datetime.strptime(lastAdded, "%Y-%m-%d")
            if len(days)>0:
                interval = int(dni["interval"])
                if current < lastAdded-datetime.timedelta(days=lastAdded.weekday())+ datetime.timedelta(days=7) or current >= lastAdded-datetime.timedelta(days=lastAdded.weekday())+ datetime.timedelta(days=7*interval):
                    dayID = current.weekday()
                    print(current, lastAdded-datetime.timedelta(days=lastAdded.weekday())+ datetime.timedelta(days=7))
                    for day in days:
                        if (dayID == day["id"]):
                            godzina = f"{day["hour"]:02d}:{day["minute"]:02d}"
                            date = f"{current:%Y-%m-%d} {godzina}"
                            nazwa = f"{name} - {date}"
                            sql = f"INSERT INTO zadania (status, data, nazwa, parentID, uzytkownik) VALUES (0, '{date}', '{nazwa}', 0, {user});"
                            mycursor.execute(sql)
                    if dayID == days[0]:
                        date = current-datetime.timedelta(days=current.weekday())
                        date = f"{date:%Y-%m-%d} 00:00:00"
                        sql = f"UPDATE harmonogram SET lastAdded='{date}' WHERE ID={id};"
                        mycursor.execute(sql)

    mydb.commit()

mycursor.execute("SELECT ID, ilePowiadomien, discord, androidToken FROM uzytkownicy;")
userData = mycursor.fetchall()
firebase_admin.initialize_app(cred)

messageMap = {}
for user in userData:
    if int(user[1])!=0 and (int(user[2]!=0) or user[3]!=""):
        # Generowanie godzin wysylania na bazie podanych ilosci powiadomien
        lst = []
        for j in range(int(user[1])):
            temp = 7+int(j*(16/user[1]))
            if temp>9:
                lst.append(f"{temp}")
            else:
                lst.append(f"0{temp}")
        if current.strftime("%H") in lst:
            toSend = []
            mycursor.execute(f"SELECT zadania.nazwa, TIME(zadania.data), discord, prnt.nazwa, uzytkownicy.androidToken FROM zadania JOIN uzytkownicy ON uzytkownicy.ID=zadania.uzytkownik LEFT JOIN zadania AS prnt ON prnt.ID=zadania.parentID WHERE zadania.status!=100 AND DATE(zadania.data)='{current.strftime("%Y-%m-%d")}' AND uzytkownicy.ID={user[0]};")
            zadData = mycursor.fetchall()
            for zadanie in zadData:
                # To bedzie zmieniane u kazdego uzytkownika
                discordID = zadanie[2]
                androidToken = zadanie[4]
                if discordID!=0 or androidToken!="":
                    parent = ""
                    if zadanie[3]!=None:
                        parent = f" o rodzicu {zadanie[3]}"
                    msg = f"Pamiętaj o wykonaniu swojego zadania {zadanie[0]} o godzinie {zadanie[1]}{parent}!"
                    if not user[0] in messageMap.keys():
                        messageMap[user[0]] = [discordID, msg, androidToken]
                    else:
                        messageMap[user[0]][1] += f"\n{msg}"

            # Nie chcialem sie meczyc z porownywaniem daty w pythonie bo latwiej to zrobic po prostu w SQL
            mycursor.execute(f"SELECT zadania.nazwa, DATE(zadania.data), discord, prnt.nazwa, uzytkownicy.androidToken FROM zadania JOIN uzytkownicy ON uzytkownicy.ID=zadania.uzytkownik LEFT JOIN zadania AS prnt ON zadania.parentID=prnt.ID WHERE zadania.status!=100 AND DATE(zadania.data)<'{current.strftime("%Y-%m-%d")}' AND uzytkownicy.ID={user[0]};")
            zadData = mycursor.fetchall()
            for zadanie in zadData:
                # To bedzie zmieniane u kazdego uzytkownika
                parent = ""
                if zadanie[3]!=None:
                    parent = f" o rodzicu {zadanie[3]}"
                discordID = zadanie[2]
                androidToken = zadanie[4]
                if discordID!=0 or androidToken!="":
                    msg = f"Pamiętaj o wykonaniu swojego zaległego zadania {zadanie[0]} z dnia {zadanie[1]}{parent}!"
                    if not user[0] in messageMap.keys():
                        messageMap[user[0]] = [discordID, msg, androidToken]
                    else:
                        messageMap[user[0]][1] += f"\n{msg}"



for key, val in messageMap.items():
    # Wysylanie zapisanych wiadomosci przez bota
    if val[0]!=0:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        client = discord.Client(intents=intents)
        @client.event
        async def on_ready():
            print(f"Logged in as {client.user}")
            try:
                user = await client.fetch_user(val[0])
                await user.send(val[1])
                print("DM sent successfully!")
            except Exception as e:
                print(f"Failed to send DM: {e}")

            await client.close()
                
        client.run(TOKEN)
    # Wysylanie przez Firebase
    if val[2]!= "":
        message = messaging.Message(
            notification=messaging.Notification(
                title="Rogal Tasks",
                body=val[1]
            ),
            token=val[2]
        )
        response = messaging.send(message)
        print("Android sent:", response)
