from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy.model import Model
from flask_login import login_user, login_required, logout_user
from flask_sqlalchemy import SQLAlchemy

import cv2
import matplotlib.pyplot as plt
from skimage import measure, morphology
from skimage.color import label2rgb
from skimage.measure import regionprops
import numpy as np

app = Flask(__name__)
db = SQLAlchemy(app)
app.config.from_object('config')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///imagedata.db'
app.config['SECRET_KEY'] = 'thisissecret'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_PATH'] = 'inputs'

db.init_app(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))


@app.route('/newuser', methods=['GET', 'POST'])
def newuser(): 
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_user = Users(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return "Sign Up Successful \n <a href='http://127.0.0.1:5000/login'> Click Here to Login</a>"
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
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
        # the parameters are used to remove small size connected pixels outliar
        constant_parameter_1 = 84
        constant_parameter_2 = 250
        constant_parameter_3 = 100

        # the parameter is used to remove big size connected pixels outliar
        constant_parameter_4 = 18

        # read the input image
        uploaded_file = request.files['file'].read()
        npimg = np.fromstring(uploaded_file, np.uint8)
        npimg = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

        img = cv2.imread(npimg, 0)
        img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)[1]  # ensure binary

        # connected component analysis by scikit-learn framework
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
            # print region.area # (for debugging)
            # take regions with large enough areas
            if region.area >= 250:
                if region.area > the_biggest_component:
                    the_biggest_component = region.area

        average = (total_area/counter)
        print("the_biggest_component: " + str(the_biggest_component))
        print("average: " + str(average))

        # experimental-based ratio calculation, modify it for your cases
        # a4_small_size_outliar_constant is used as a threshold value to remove connected outliar connected pixels
        # are smaller than a4_small_size_outliar_constant for A4 size scanned documents
        a4_small_size_outliar_constant = ((average/constant_parameter_1)*constant_parameter_2)+constant_parameter_3
        print("a4_small_size_outliar_constant: " + str(a4_small_size_outliar_constant))

        # experimental-based ratio calculation, modify it for your cases
        # a4_big_size_outliar_constant is used as a threshold value to remove outliar connected pixels
        # are bigger than a4_big_size_outliar_constant for A4 size scanned documents
        a4_big_size_outliar_constant = a4_small_size_outliar_constant*constant_parameter_4
        print("a4_big_size_outliar_constant: " + str(a4_big_size_outliar_constant))

        # remove the connected pixels are smaller than a4_small_size_outliar_constant
        pre_version = morphology.remove_small_objects(blobs_labels, a4_small_size_outliar_constant)
        # remove the connected pixels are bigger than threshold a4_big_size_outliar_constant
        # to get rid of undesired connected pixels such as table headers and etc.
        component_sizes = np.bincount(pre_version.ravel())
        too_small = component_sizes > a4_big_size_outliar_constant
        too_small_mask = too_small[pre_version]
        pre_version[too_small_mask] = 0
        # save the the pre-version which is the image is labelled with colors
        # as considering connected components
        plt.imsave('pre_version.png', pre_version)

        # read the pre-version
        img = cv2.imread('pre_version.png', 0)
        # ensure binary
        img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        # save the the result
        cv2.imwrite("./outputs/output.png", img)

        return '<img src="./output.png" alt="alternatetext">'
    return render_template("addimage.html")

if __name__ == '__main__':
    app.run(debug=True)