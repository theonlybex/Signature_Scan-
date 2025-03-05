

import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage import measure, morphology
from skimage.color import label2rgb
from skimage.measure import regionprops
#from models import Img
from werkzeug.utils import secure_filename


from flask import Flask, render_template, request, redirect, url_for, Response
from flask_sqlalchemy.model import Model
from flask_login import login_user, login_required, logout_user
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
db = SQLAlchemy(app)
app.config.from_object('config')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///imagedata.db'
app.config['SECRET_KEY'] = 'thisissecret'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))

class Img(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    img = db.Column(db.Text, unique=True, nullable=False)
    name = db.Column(db.Text, nullable=False)

db.create_all()

@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        pic = request.files['files']

        if not pic:
            return "no pic uploaded", 400

        filename = secure_filename(pic.filename)

        img = Img(img=pic.read(), name=filename)
        db.session.add(img)
        db.session.commit()

        return "Img has been uploaded!", 200
    return render_template('addimage.html')

@app.route('/<int:id>')
def get_img(id):
    img = Img.query.filter_by(id=id).first()
    if not img:
        return "No img is found with this id", 404
    return Response(img)



@app.route('/newuser', methods=['GET', 'POST'])
def newuser(): 
    from models import Users
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        new_user = Users(name=name, email=email, username=username, password=password, is_admin=bool(role))
        if role:
            new_user.add_roles('admin')
        else:
            new_user.add_roles('user')
        db.session.add(new_user)
        db.session.commit()
        return "Sign Up Successful \n <a href='http://127.0.0.1:5000/login'> Click Here to Login</a>"
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    from models import Users
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Users.query.filter_by(username=username).first()
        if user:
            if user.password == password:
                login_user(user)
                return redirect(url_for('index'))
            else:
                return "Incorrect password \n <a href='/login'> Try Again</a>"
        else:
            return "Username Not Found!! \n <a href='/newuser'> Sign-up </a> \n <a href='/login'> Try Again</a>"
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return "User Logged Out"

@app.route('/', methods=['GET', 'POST'])
# @login_required
def index():
    if request.method == 'POST':
        constant_parameter_1 = 84
        constant_parameter_2 = 250
        constant_parameter_3 = 100

        constant_parameter_4 = 18

        # read the image
        id = request.form['filename']
        img = Img.query.filter_by(id=id).first()

        img = cv2.imread(img.img, 0)
        img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)[1]


        blobs = img > img.mean()
        blobs_labels = measure.label(blobs, background=1)
        image_label_overlay = label2rgb(blobs_labels, image=img)

        fig, ax = plt.subplots(figsize=(10, 6))

        '''
        # plot the connected components (for debugging)
        ax.imshow(image_label_overlay)
        ax.set_axis_off()
        plt.tight_layout()
        plt.show()
        '''

        the_biggest_component = 0
        total_area = 0
        counter = 0
        average = 0.0
        for region in regionprops(blobs_labels):
            if region.area > 10:
                total_area = total_area + region.area
                counter = counter + 1

            if region.area >= 250:
                if region.area > the_biggest_component:
                    the_biggest_component = region.area

        average = (total_area/counter)
        print("the_biggest_component: " + str(the_biggest_component))
        print("average: " + str(average))

        a4_small_size_outliar_constant = ((average/constant_parameter_1)*constant_parameter_2)+constant_parameter_3
        print("a4_small_size_outliar_constant: " + str(a4_small_size_outliar_constant))

        a4_big_size_outliar_constant = a4_small_size_outliar_constant*constant_parameter_4
        print("a4_big_size_outliar_constant: " + str(a4_big_size_outliar_constant))

        pre_version = morphology.remove_small_objects(blobs_labels, a4_small_size_outliar_constant)

        component_sizes = np.bincount(pre_version.ravel())
        too_small = component_sizes > a4_big_size_outliar_constant
        too_small_mask = too_small[pre_version]
        pre_version[too_small_mask] = 0

        plt.imsave('pre_version.png', pre_version)

        img = cv2.imread('pre_version.png', 0)

        img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        # save the result
        cv2.imwrite("./outputs/output.png", img)

        return '<img src="./outputs/output.png" alt="alternatetext">'
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)