from flask import *
from flask import redirect
import mysql.connector
import hashlib
import os
from flask.wrappers import Response
app=Flask(__name__)
app.secret_key='secret_key'

# mydb=mysql.connector.connect(host='localhost',user='root',password='Mukesh@2003',database='db')
db=os.environ['RDS_DB_NAME']
user=os.environ['RDS_USERNAME']
password=os.environ['RDS_PASSWORD']
host=os.environ['RDS_HOSTNAME']
port=os.environ['RDS_PORT']
with mysql.connector.connect(host=host,user=user,password=password,db=db) as conn:
    cursor=conn.cursor(buffered=True)
    cursor.execute("create table if not exists detail (name varchar(255),rollno varchar(10) PRIMARY KEY,password VARCHAR(255))")
    cursor.execute("create table if not exists Student_Info (id INT AUTO_INCREMENT UNIQUE KEY, name VARCHAR(255) NOT NULL, roll_number VARCHAR(10) PRIMARY KEY, total_classes INT,classes_attended INT,attendance_percent INT)")
    cursor.execute("create table if not exists Assignments (id INT AUTO_INCREMENT PRIMARY KEY, roll_num VARCHAR(10),Assignment_name VARCHAR(255) NOT NULL,file_name VARCHAR(255) NOT NULL ,filedata LONGBLOB,FOREIGN KEY(roll_num) REFERENCES Student_Info(roll_number))")
    cursor.execute("create table if not exists Records (id INT AUTO_INCREMENT PRIMARY KEY, roll_num VARCHAR(10),record_name VARCHAR(255) NOT NULL, file_name VARCHAR(255) NOT NULL,filedata LONGBLOB,FOREIGN KEY(roll_num) REFERENCES Student_Info(roll_number))")
mydb=mysql.connector.connect(host=host,user=user,password=password,db=db)

@app.route('/')
def index1():
    return render_template('index.html')

@app.route('/login',methods=['POST','GET'])
def login():
    if session.get('user'):
        return flask.redirect(url_for('index1', target='_self'))
    if request.method=='POST':
        rollno=request.form['rollno']
        password=request.form['password']
        
        hash=hashlib.sha1(password.encode()).hexdigest()

        cursor=mydb.cursor(buffered='True')
        cursor.execute('select * from detail where rollno=%s and password=%s',(rollno,hash))

        user=cursor.fetchone()

        if user is not None:
            session['loggedin']=True
            session['username']=user
            
            return  render_template('dashstu.html',roll=rollno)                 #'''redirect(url_for('dashboard'))'''
        else:
            return render_template('login.html',error="Incorrect username or password")

    return render_template('login.html')

@app.route('/register',methods=['POST','GET'])
def register():
    if request.method=='POST':
        name=request.form['name']
        rollno=request.form['rollno']
        password=request.form['password']

        hash=hashlib.sha1(password.encode()).hexdigest()

        cursor=mydb.cursor(buffered='True')

        cursor.execute('select * from detail where rollno=%s ',(rollno,))
        user=cursor.fetchone()

        if user is not None:
            return render_template("register.html",error="User already exists")
        else:
            cursor.execute('insert into detail (name,rollno,password) values(%s,%s,%s)',(name,rollno,hash ))
            cursor.execute('insert into Student_Info(name,roll_number,total_classes,classes_attended,attendance_percent) values(%s,%s,%s,%s,%s)',(name,rollno,'0','0','0'))

        mydb.commit()
        cursor.close()

        return render_template('login.html',error="Successfully registered")
    
    return render_template('register.html')

@app.route('/logf',methods=['POST','GET'])
def log():
    if request.method=='POST':
        user=request.form['uname']
        password=request.form['password']

        if (user== "abc" and password== "123") or (user== "faculty" and password== "hii") or (user== "hello" and password== "100") or (user== "fac" and password== "abc") :
            session['loggedin']=True
            
            session['username']='user'
            return  render_template('dashfac.html')   #'succesful logged as faculty' 
        else:
            return render_template('logf.html',error="Invalid USER")
            
    return render_template('logf.html')

@app.route('/fi')
def findex():
    return render_template('fi.html')

@app.route('/hello')
def hello():
    return render_template('hello.html')

@app.route('/si/<roll>')
def si(roll):
    return render_template('stuindex.html',roll=roll)

@app.route('/hellos')
def hellos():
    return render_template('hellos.html')

@app.route('/logout')
def logout():
    # if session.get('user'):
    #     session.pop('user')
    #     return flask.redirect(url_for('index1', target='_self'))
    # else:
    session.clear()
    return flask.redirect(url_for('index1', target='_self'))

 
@app.route('/submit_assignment/<roll>',methods=["GET","POST"])
def submit_assignment(roll):
    return render_template("submit_assignment.html",roll=roll)

@app.route('/upload/<roll>',methods=["POST","GET"])
def upload_file(roll):
    uploaded_file=request.files['file']
    filename=uploaded_file.filename
    assignname=request.form['filename']
    file_data=uploaded_file.read()
    cursor = mydb.cursor()
    try:
        ins="INSERT into Assignments(roll_num,Assignment_name,file_name,filedata) VALUES (%s,%s,%s,%s)"
        val=(roll,assignname,filename,file_data)
        cursor.execute(ins,val)
        mydb.commit()
        msg="Assignment uploaded successfully"
    except mysql.connector.Error as err:
        msg="Error: {}".format(err)
    cursor.close()
    return render_template("submit_assignment.html",msg=msg)

@app.route("/view_assignment/")
def view_assignment():
    return render_template("view_assignment.html")

@app.route("/view_assign",methods = ["POST"])
def view_assign():
    msg="msg"
    id = request.form["roll"]
    cursor = mydb.cursor()
    up="select * from Assignments where roll_num = %s"
    p=(id,)
    cursor.execute(up,p)
    rows = cursor.fetchall()
    if not rows == []:
        return render_template("view_assignment1.html", rows=rows)
    else:
        msg = "Enter correct roll number"
        return render_template("view_assignment.html", msg=msg)

@app.route("/download/<filename>",methods=["GET"])
def download_file(filename):
    cursor = mydb.cursor()
    query = "SELECT filedata FROM Assignments WHERE file_name = %s"
    cursor.execute(query, (filename,))
    file_data = cursor.fetchone()
    if file_data:
        response = make_response(file_data[0])
        response.headers["Content-Type"] = "application/octet-stream"
        response.headers["Content-Disposition"] = f"attachment; filename=\"{filename}\""
        return response
    else:
        return "File not found"

@app.route("/store_records/<roll>",methods=["GET","POST"])
def store_records(roll):
    return render_template("store_record.html",roll=roll)

@app.route('/upload_record/<roll>',methods=["POST","GET"])
def upload_record(roll):
    uploaded_file=request.files['file']
    recordname=request.form['filename']
    filename=uploaded_file.filename
    file_data=uploaded_file.read()
    cursor = mydb.cursor()
    try:
        ins="INSERT into Records(roll_num,record_name,file_name,filedata) VALUES (%s,%s,%s,%s)"
        val=(roll,recordname,filename,file_data)
        cursor.execute(ins,val)
        mydb.commit()
        msg="Record uploaded successfully"
    except mysql.connector.Error as err:
        msg="Error: {}".format(err)
    cursor.close()
    return render_template("store_record.html",msg=msg)

@app.route("/view_record")
def view_record():
    return render_template("view_record.html")

@app.route("/view_record1",methods = ["POST"])
def view_record1():
    msg="msg"
    id = request.form["roll"]
    cursor = mydb.cursor()
    up="select * from Records where roll_num = %s "
    p=(id,)
    cursor.execute(up,p)
    rows = cursor.fetchall()
    if not rows == []:
        return render_template("view_record1.html", rows=rows)
    else:
        msg = "Enter correct roll number"
        return render_template("view_record.html", msg=msg)

@app.route("/download_record/<filename>",methods=["GET"])
def download_record(filename):
    cursor = mydb.cursor()
    query = "SELECT filedata FROM Records WHERE file_name = %s"
    cursor.execute(query, (filename,))
    file_data = cursor.fetchone()
    if file_data:
        response = make_response(file_data[0])
        response.headers["Content-Type"] = "application/octet-stream"
        response.headers["Content-Disposition"] = f"attachment; filename=\"{filename}\""
        return response
    else:
        return "File not found,please try again"

@app.route("/view_myrecords/<roll>",methods = ["POST","GET"])
def view_myrecords(roll):
    msg="msg"
    cursor = mydb.cursor()
    up="select * from Records where roll_num = %s "
    p=(roll,)
    cursor.execute(up,p)
    rows = cursor.fetchall()
    if not rows == []:
        return render_template("view_record1.html", rows=rows)
    else:
        msg = "No records stored"
        return render_template("view_record1.html", msg=msg)

@app.route("/view_attendance/<roll>",methods = ["POST","GET"])
def view_attendance(roll):
    cursor = mydb.cursor()
    up="select * from Student_Info where roll_number = %s"
    p=(roll,)
    cursor.execute(up,p)
    rows = cursor.fetchall()
    if not rows == []:
        return render_template("view_attendance1.html", rows=rows)
    else:
        msg = "pls try again"
        return render_template("/hellos", msg=msg)

@app.route("/update_attendance")
def update_attendance():
    return render_template("update_attendance.html")

@app.route("/update_att",methods = ["POST"])
def update_att():
    msg="msg"
    id = request.form["roll"]
    cursor = mydb.cursor()
    up="select * from Student_Info where roll_number = %s"
    p=(id,)
    cursor.execute(up,p)
    rows = cursor.fetchall()
    if not rows == []:
        return render_template("update_attendance1.html", rows=rows)
    else:
        msg = "Enter the correct roll number"
        return render_template("update_attendance.html", msg=msg)

@app.route("/update_att1",methods = ["GET","POST"])
def update_att1():
    msg = "Attendance not updated"
    if request.method == "POST":
        try:
            roll = request.form["roll"]
            cls_con = int(request.form["new_cls_conducted"])
            cls_att = int(request.form["new_cls_attended"])
            tot_con= int(request.form["Total_cls_conducted"])
            tot_att=int(request.form["Total_cls_att"])
            classes_attended=tot_att+cls_att
            total_classes=tot_con+cls_con
            if cls_att>cls_con:
                msg = "We can not update attendance to the database"
                mydb.rollback()
            if total_classes !='0':
                percent=((cls_att+tot_att)/(tot_con+cls_con))*100
            cursor = mydb.cursor()
            upd= "UPDATE Student_Info SET total_classes=%s,classes_attended=%s,attendance_percent=%s WHERE roll_number = %s"
            cursor.execute(upd,(total_classes,classes_attended,percent,roll))
            mydb.commit()
            msg = "Student attendance successfully Updated"
        except:
            mydb.rollback()
            msg = "We can not update attendance to the database"
        finally:
            return render_template("update_attendance.html",msg = msg) 
        
if __name__=="__main__":
    app.run()
        