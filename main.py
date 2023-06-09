from flask import Flask, render_template, request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from flask_mail import Mail
import os
from werkzeug.utils import secure_filename
import math

app = Flask(__name__)

# ------ Todo Secret Key -----
app.secret_key = 'super-secret-key'


#  -------- Todo Config.json File Loded --------
try:
    with open('config.json','r',encoding='utf-8')as f:
        params=json.load(f)["params"]
except Exception as e:
    print(e)

# --------- Todo CONFIG A UPLOAF A FILE --
app.config['UPLOAD_FOLDER']=params['upload_locations']


# ---- Todo Configure MAIL SETUP-------------
try:
    app.config.update(
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT='465',
        MAIL_USE_SSL=True,
        MAIL_USERNAME=params['gmail-user'],
        MAIL_PASSWORD=params['gmail-password']
    )

    mail=Mail(app)
except Exception as e:
    print(e)
local_server=True

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)

class Contacts(db.Model):
    '''
    sno, name phone_num, msg, date, email
    '''
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    email = db.Column(db.String(20), nullable=False)

class Posts(db.Model):
    '''
    sno, name phone_num, msg, date, email
    '''
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String(12), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    slug = db.Column(db.String(21), nullable=False)
    img_file = db.Column(db.String(50), nullable=False)

# @app.route("/")
# def index():
#     posts = Posts.query.filter_by().all()
#     posts = Posts.query.filter_by().all()[0:params['no_of_posts']]
#     return render_template('index.html',params=params,posts=posts)

@app.route("/")
def home():
    posts=Posts.query.filter_by().all()
    last=math.ceil(len(posts)/int(params['no_of_posts']))
    page=request.args.get('page')
    if (not str(page).isnumeric()):
        page=1
    page=int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]

    if (page==1):
        prev='#'
        next="/?page="+  str(page+1)
    elif (page==last):
        prev="/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)


    return render_template('index.html',params=params,posts=posts,prev=prev,next=next)


@app.route("/about")
def about():
    return render_template('about.html',params=params)

@app.route("/post")
def post():
    return render_template('post.html',params=params)

@app.route("/post/<string:post_slug>",methods=['GET'])
def post_route(post_slug):
    post=Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=post)


@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_num = phone, msg = message, date= datetime.now(),email = email )
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New Message From ' + name ,
                          sender=email,
                          recipients=[params['gmail-user']],
                          body=message + "\n" + phone
                          )
    return render_template('contact.html',params=params)

@app.route("/dashboard",methods=['GET','POST'])
def dashboard():
    posts = Posts.query.filter_by().all()
    if 'user' in session and session['user']==params['admin_user']:
        return render_template('dashboard.html',params=params,posts=posts)

    if request.method=="POST":
        admin_email=request.form.get('admin_email')
        admin_password=request.form.get('admin_pass')
        if admin_email==params['admin_user'] and admin_password==params['admin_password']:
            session['user']=admin_email
            return render_template('dashboard.html', params=params, posts=posts)

    return render_template('login.html',params=params)

@app.route("/edit/<string:sno>",methods=['GET','POST'])
def edit(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method=='POST':
            title=request.form.get('title')
            content=request.form.get('content')
            slug=request.form.get('slug')
            img_file=request.form.get('img_file')
            date=datetime.now()
            print(title,content,slug,img_file)
            print(sno)

            if sno=='0':
                post=Posts(title=title,content=content,slug=slug,img_file=img_file,date=date)
                db.session.add(post)
                db.session.commit()
                # return redirect('/edit/'+sno)
            else:
                post=Posts.query.filter_by(sno=sno).first()
                post.title=title
                post.content=content
                post.slug=slug
                post.img_file=img_file
                post.date=date
                db.session.commit()
                return redirect('/edit/'+sno)

        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html',params=params,post=post)

@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method=='POST':
            f=request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return "UPLOAD SUCCESSFULLY"


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:sno>",methods=['GET','POST'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')

app.run(debug=True)


