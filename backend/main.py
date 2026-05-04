from flask import request, jsonify, json
from flask import Flask
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from datetime import datetime
import os

from config import Config

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "python"
app.config['MYSQL_PASSWORD'] = os.getenv('PASS')
app.config['MYSQL_DB'] = os.getenv('DB')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

@app.route("/zadania/<int:ID>/<string:DATE>", methods=["GET"])
def get_tasks(ID,DATE):
    where = ""
    if (DATE!="any"):
        where = (f"HAVING date(parents.data)='{DATE}' ")
    cursor = mysql.connection.cursor()

    # Skomplikowany kod SQL ktory pobiera zadania, przypisuje im dzieci i oblicza sredni stopien wykonania dla grupy
    cursor.execute(f"SELECT parents.*, JSON_ARRAYAGG(JSON_OBJECT('ID', children.ID, 'nazwa', children.nazwa, 'status', children.status, 'data', CONCAT(DATE_FORMAT(children.data, '%a, %d %b %Y %H:%i:%s'),' GMT'))) AS children, ratio.r AS ratio FROM (SELECT * FROM zadania WHERE status!=100) AS parents LEFT JOIN (SELECT * FROM zadania WHERE status!=100) AS children ON parents.ID=children.parentID LEFT JOIN (SELECT parentID,  SUM(status)/(COUNT(status)) AS r FROM zadania GROUP BY parentID HAVING parentID!=0) AS ratio ON ratio.parentID=parents.ID  WHERE parents.uzytkownik={ID} GROUP BY ID {where}ORDER BY data ASC, ID ASC;")

    temp = cursor.fetchall()
    cursor.close()
    return jsonify({"zadania" : temp})

@app.route("/noweZadanie/<int:USER>", methods=["POST"])
def addTask(USER):
    nazwa = request.json.get("nazwa")
    data = request.json.get("dataTemp")
    rodzic = request.json.get("rodzic")

    if nazwa and data and rodzic:
        cursor = mysql.connection.cursor()
        if data!="NULL":
            cursor.execute(f"INSERT INTO zadania (status, uzytkownik, nazwa, data, parentID) VALUES (0, {USER}, '{nazwa}', '{data}', {rodzic})")
        else:
            cursor.execute(f"INSERT INTO zadania (status, uzytkownik, nazwa, data, parentID) VALUES (0, {USER}, '{nazwa}', {data}, {rodzic})")
        mysql.connection.commit()
        cursor.close()
        return jsonify({"message":"Udalo sie dodac zadanie!"}), 201
    else:
        return jsonify({"message" : "Musisz wypełnić wszystkie dane w formularzu!"}),400
    
@app.route("/usunZadanie/<int:ID>", methods=["DELETE"])
def usunZadanie(ID):
    if ID:
        cursor = mysql.connection.cursor()
        cursor.execute(f"DELETE FROM zadania WHERE ID={ID}")
        mysql.connection.commit()
        cursor.close()
        return jsonify({"message":"Udalo sie usunac zadanie!"}), 202
    
@app.route("/wykonajZadanie/<int:ID>", methods=["PATCH"])
def wykonajZadanie(ID):
    if ID:
        cursor = mysql.connection.cursor()
        cursor.execute(f"UPDATE zadania SET status=100 WHERE ID={ID}")
        mysql.connection.commit()
        cursor.close()
        return jsonify({"message":"Udalo sie wykonac zadanie!"}), 203
    
@app.route("/harmonogram/<int:ID>", methods=["GET"])
def wyslijHarmo(ID):
    if ID:
        cursor = mysql.connection.cursor()
        cursor.execute(f"SELECT * FROM harmonogram WHERE uzytkownik={ID};")
        temp = cursor.fetchall()
        cursor.close()
        for row in temp:
            if row["dni"]:
                row["dni"] = json.loads(row["dni"])
        return jsonify({"harmonogram" : temp})
    
@app.route("/harmonogramCreate/<int:IDuser>", methods=["POST"])
def noweHarmo(IDuser):
    nazwa = request.json.get("nazwa")
    dni = request.json.get("dniD")
    if "'" in str(dni):
        dni = json.dumps(dni)
    if IDuser and nazwa and dni:
        cursor = mysql.connection.cursor()
        cursor.execute(f"INSERT INTO harmonogram (nazwa, dni, uzytkownik) VALUES (%s, %s,{IDuser})", (nazwa, dni))
        mysql.connection.commit()
        cursor.close()
        return jsonify({"message" :"Udalo sie dodać nowy plan do harmonogramu!"}),204
    else:
        return jsonify({"message" :"Nie udalo sie dodać nowego planu do harmonogramu!"}),401

@app.route("/harmonogramEdit/<int:ID>", methods=["PATCH"])
def edytujHarmo(ID):
    nazwa = request.json.get("nazwa")
    dni = request.json.get("dniD")
    print(list(dni.keys()))
    if "'" in str(dni):
        dni = json.dumps(dni)
    if ID:
        cursor = mysql.connection.cursor()
        cursor.execute(f"UPDATE harmonogram SET nazwa=%s, dni=%s WHERE ID={ID}", (nazwa, dni))
        mysql.connection.commit()
        cursor.close()
        return jsonify({"message":"Udalo sie wykonac zadanie!"}), 205

@app.route("/register", methods=["POST"])
def register():
    login = request.json.get("login")
    haslo = request.json.get("haslo")
    haslo = bcrypt.generate_password_hash(haslo).decode('utf-8')
    cursor = mysql.connection.cursor()
    cursor.execute(f"SELECT login FROM uzytkownicy WHERE login='{login}';")
    temp = cursor.fetchall()
    if len(temp) >0:
        cursor.close()
        return jsonify({"message" : "Dany użytkownik już istnieje!"}), 402
    else:
        cursor.execute(f'INSERT INTO uzytkownicy (login, haslo) VALUES ("{login}", "{haslo}");')
        mysql.connection.commit()
        cursor.close()
        return jsonify({"message" : "Dodano uzytkownika do bazy!"}), 206
    
@app.route("/login", methods=["POST"])
def login():
    login = request.json.get("login")
    haslo = request.json.get("haslo")
    cursor = mysql.connection.cursor()
    cursor.execute(f"SELECT id, login, haslo FROM uzytkownicy WHERE login='{login}';")
    temp = cursor.fetchall()
    cursor.close()
    if len(temp) ==0:
        return jsonify({"message" : "Dany użytkownik nie istnieje!"}), 410
    else:
        password = temp[0]['haslo']
        if not bcrypt.check_password_hash(password, haslo):
            return jsonify({"message" : "Błędne hasło!"}), 411
        else:
            return jsonify({"dane" : temp[0]['id']}), 208

@app.route("/userData/<int:ID>")
def getUserData(ID):
    cursor = mysql.connection.cursor()
    cursor.execute(f"SELECT * FROM uzytkownicy LEFT JOIN zadania ON zadania.uzytkownik=uzytkownicy.ID WHERE uzytkownicy.ID={ID};")
    result = cursor.fetchall()
    cursor.close()
    return jsonify({"dane":result}),209

@app.route("/harmoRemove/<int:ID>", methods=["DELETE"])
def removeHarmo(ID):
    cursor = mysql.connection.cursor()
    cursor.execute(f"DELETE FROM harmonogram WHERE ID={ID};")
    mysql.connection.commit()
    cursor.close()
    return jsonify({"wynik": "Usunięto wybrany wpis"}),210

@app.route("/userChange/<int:ID>", methods=["PATCH"])
def changeUser(ID):
    what = request.json.get("what")
    value = request.json.get("value")
    if what=="haslo":
        value = bcrypt.generate_password_hash(value).decode('utf-8')
    cursor = mysql.connection.cursor()
    cursor.execute(f"UPDATE uzytkownicy SET {what}='{value}' WHERE ID={ID};")
    mysql.connection.commit()
    cursor.close()
    return jsonify({"wynik": "Edytowano wybrany wpis"}),211

@app.route("/userRemove/<int:ID>", methods=["DELETE"])
def removeUser(ID):
    cursor = mysql.connection.cursor()
    cursor.execute(f"DELETE FROM uzytkownicy WHERE ID={ID};")
    mysql.connection.commit()
    cursor.close()
    return jsonify({"wynik": "Usunięto uzytkownika!"}),212

@app.route("/updateTaskInfo/<int:ID>", methods=["PATCH"])
def updateInfoTask(ID):
    data = request.json.get("data")
    data = datetime.strptime(data, "%a, %d %b %Y %H:%M:%S %Z")
    data = data.strftime("%Y-%m-%d %H:%M:%S")
    nazwa = request.json.get("nazwa")
    cursor = mysql.connection.cursor()
    cursor.execute(f"UPDATE zadania SET nazwa='{nazwa}', data='{data}' WHERE ID={ID};")
    mysql.connection.commit()
    cursor.close()
    return jsonify({"wynik": "Zaktualizowano zadanie!"}),213

@app.route("/updateFCM/<int:ID>", methods=["PATCH"])
def updateFCM(ID):
    fcm = request.json
    cursor = mysql.connection.cursor()
    cursor.execute(f"UPDATE uzytkownicy SET androidToken='{fcm}' WHERE ID={ID};")
    mysql.connection.commit()
    cursor.close()
    return jsonify({"wynik": "Zaktualizowano FCM!"}),214

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)