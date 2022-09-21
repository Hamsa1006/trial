from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddEmp.html')


@app.route("/about", methods=['POST', ""])
def about():
    return render_template('AboutUs.html')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    department = request.form['department']
    address = request.form['address']


    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s,%s,%s,%s,%s,%s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, department, address))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name, empid=emp_id)

@app.route("/editot", methods=['POST','GET'])
def editot():
    msg=" "
    a,b,c,d,e = "","","","",""
    if request.method == 'POST' and 'emp_id' and 'ot_hour' in request.form:
        emp_id=request.form['emp_id']
        ot_hour=request.form['ot_hour']
        cursor = db_conn.cursor()
        cursor.execute('SELECT * FROM employee WHERE emp_id = %s', (emp_id))
        user = cursor.fetchone()
        db_conn.commit()

        if user:

         try:
            cursor.execute('Update employee SET ot_hour = %s WHERE emp_id = %s', (ot_hour, emp_id))
            db_conn.commit()
            msg="Updated"
         except:
            msg="Failed"
        else:
            msg="Employee does not exist"



    return render_template("editot.html", msg=msg)

@app.route("/checksalary", methods=['POST','GET'])
def checksalary():
    import re
    import datetime
    time = datetime.datetime.now()
    msg = " "
    a,b,c,d,e="","","","",""


    total_salary=""
    if request.method == 'POST' and 'emp_id' in request.form:
        emp_id = request.form['emp_id']
        cursor = db_conn.cursor()
        cursor.execute('SELECT * FROM employee WHERE emp_id = %s', (emp_id))
        user = cursor.fetchone()
        if user:
            cursor.execute('SELECT ot_hour FROM employee WHERE emp_id = %s', (emp_id))
            ot_hour = cursor.fetchone()
            ot_hour2 = re.sub(r'[^a-zA-Z0-9]', '', str(ot_hour))

            cursor.execute('SELECT un_leave FROM employee WHERE emp_id = %s', (emp_id))
            unpaid = cursor.fetchone()
            unpaid2 = re.sub(r'[^a-zA-Z0-9]', '', str(unpaid))
            cursor.execute('SELECT first_name FROM employee WHERE emp_id = %s', (emp_id))
            first = cursor.fetchone()
            first2 = re.sub(r'[^a-zA-Z0-9]', '', str(first))
            cursor.execute('SELECT last_name FROM employee WHERE emp_id = %s', (emp_id))
            last = cursor.fetchone()
            last2 = re.sub(r'[^a-zA-Z0-9]', '', str(last))
            cursor.execute('SELECT department FROM employee WHERE emp_id = %s', (emp_id))
            department = cursor.fetchone()
            department2 = re.sub(r'[^a-zA-Z0-9]', '', str(department))
            cursor.execute('SELECT basic_salary FROM employee WHERE emp_id = %s', (emp_id))
            bas_salary = cursor.fetchone()
            bas_salary2= re.sub(r'[^a-zA-Z0-9]', '', str(bas_salary))
            db_conn.commit()
            name2= first2+" "+ last2
            ot_hour3 = float(ot_hour2) / float(10)
            ot_hour4=str(ot_hour3)
            a="Employee "+name2+" from department of "+ department2+":"
            b= "Basic Salary : RM "+bas_salary2
            c= "Total Overtime Hours : "+ot_hour4
            d="Unpaid Leave taken : "+ unpaid2+ " days"

            ot_pay=float(ot_hour4)*float(5)
            rough_sal=float(bas_salary2)+float(ot_pay)
            sal_ded=int(unpaid2)*45
            total_salary = float(rough_sal)-float(sal_ded)
            f=str(total_salary)
            e="Total Salary of Employee as of ("+ str(time) + ") : RM "+f

        else:
            msg="Employee does not exist"



    return render_template("checksalary.html", msg=msg, a=a,b=b, c=c, d=d, e=e)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
