import mysql.connector
import os
from dotenv import load_dotenv
import datetime
import discord
import firebase_admin
from firebase_admin import credentials, messaging

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
    dayDict = {"Monday" : "a", "Tuesday": "b", "Wednesday" : "c", "Thursday" : "d", "Friday" : "e"}
    for row in harmoData:
        name = row[1]
        times = row[2].split(",")
        user = row[3]

        unpack = []
        dayName = current.strftime("%A")
        let = dayDict[dayName]
        for code in times:
            letter = code[0]
            if letter == let:
                unpack.append(int(code[1:]))
        unpack.sort()
        unpack.append(0)

        new = []
        lent = len(unpack)
        first = unpack[0]
        # Zamiana danych na format XX:00-YY:00
        for i in range (lent):
            if i>0:
                if unpack[i] != unpack[i-1]+1:
                    if unpack[i-1] !=first:
                        new.append(f"{first+9}:00-{unpack[i-1]+10}:00")
                    else:
                        new.append(f"{first+9}:00-{first+10}:00")
                    first = unpack[i]
        for hours in new:
            date = f"{current.strftime("%Y-%m-%d")} {hours[:5]}"
            nazwa = f"{name} - {hours}"
            sql = f"INSERT INTO zadania (status, data, nazwa, parentID, uzytkownik) VALUES (0, '{date}', '{nazwa}', 0, {user});"
            mycursor.execute(sql)
        mydb.commit()

mycursor.execute("SELECT ID, ilePowiadomien, discord FROM uzytkownicy;")
userData = mycursor.fetchall()
firebase_admin.initialize_app(cred)

messageMap = {}
for user in userData:
    if int(user[1])!=0 and int(user[2]!=0):
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
                if discordID!=0:
                    parent = ""
                    if zadanie[3]!=None:
                        parent = f" o rodzicu {zadanie[3]}"
                    msg = f"Pamiętaj o wykonaniu swojego zadania {zadanie[0]} o godzinie {zadanie[1]}{parent}!"
                    if not user[0] in messageMap.keys():
                        messageMap[user[0]] = [discordID, msg, androidToken]
                    else:
                        messageMap[user[0]][1] += f"\n{msg}"

            # Nie chcialem sie meczyc z porownywaniem daty w pythonie bo latwiej to zrobic po prostu w SQL
            mycursor.execute(f"SELECT zadania.nazwa, DATE(zadania.data), discord, prnt.nazwa FROM zadania JOIN uzytkownicy ON uzytkownicy.ID=zadania.uzytkownik LEFT JOIN zadania AS prnt ON zadania.parentID=prnt.ID WHERE zadania.status!=100 AND DATE(zadania.data)<'{current.strftime("%Y-%m-%d")}' AND uzytkownicy.ID={user[0]};")
            zadData = mycursor.fetchall()
            for zadanie in zadData:
                # To bedzie zmieniane u kazdego uzytkownika
                parent = ""
                if zadanie[3]!=None:
                    parent = f" o rodzicu {zadanie[3]}"
                discordID = zadanie[2]
                if discordID!=0:
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