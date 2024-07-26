from flask import render_template, Blueprint, request
from werkzeug.utils import secure_filename
from flask.views import View
import os
import glob
from datetime import datetime

#Import required modules
from app.vision import ExtractData

from . import app
app.app_context().push()

running = Blueprint('running', __name__)


def delete_all_images(except_path):

    directory = os.path.join(app.config['STATIC_PATH'],r'img_worked')
    image_extensions = ('*.png', '*.jpg', '*.jpeg', '*.gif')
    
    # Iterate over each image extension
    for extension in image_extensions:
        
        files = glob.glob(os.path.join(directory, extension))
        
        num_of_images = len(files)

        if num_of_images >= 10:

            # Iterate over the found files and delete them
            for file in files:
                try:
                    #We avoid to delete the img just processed to show it.
                    if except_path != file:
                        os.remove(file)
                except Exception as e:
                    print(f"Error deleting {file}: {e}")



class MainView(View):
    def __init__(self):
        self.ALLOWED_EXTENSIONS = {'jpg'}
        self.maintem = 'index.html'
        self.path_file_save_w = os.path.join(app.config['APP_PATH'],r'workfiles')
        self.path_file_save_s = os.path.join(app.config['STATIC_PATH'],r'img_worked')

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    

    def dispatch_request(self):
        if request.method == 'GET':
            return self.get()
        elif request.method == 'POST':
            return self.post()
        else:
            return 'Method not allowed', 405
        
    def get(self):
        
        context = {
            'post_page': False
                   }
        
        return render_template(self.maintem, **context)
    
    def post(self):
        file = request.files['image_file']  # Access the uploaded file
            
        if file:

            #Validate the file name and save it.
            if file and self.allowed_file(file.filename):
                filename = secure_filename(file.filename)
                
                # Generate unique name
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')   
                hashed_filename = timestamp + filename


                file_data = file.read()

                #Save image in dir for work
                path_file_w = os.path.join(self.path_file_save_w, hashed_filename)
                with open(path_file_w, 'wb') as f:
                    f.write(file_data)

                #Save image in for static
                path_file_s = os.path.join(self.path_file_save_s, hashed_filename)
                with open(path_file_s, 'wb') as f:
                    f.write(file_data)

                extract = ExtractData(img_path=path_file_w)
                extract.execute()

                data = {
                    'structed_data': extract.send_data,
                    'raw_data': extract.data_f,
                    'grap_data': extract.graph_data,
                    'img_path': f'img_worked/{hashed_filename}'

                }
                context = {
                        'data': data,
                        'msgs' : extract.msgs
                    }
                try:
                    pass
                except:
                    pass#context = {'data':{}, 'msg': 'Something went wrong', 'post_page':False}
                
                os.remove(path_file_w)
                delete_all_images(path_file_s)

                return render_template(self.maintem, **context)
            else:
                context = {'msg': "Is not a correct file '.jpg' ", 'post_page':False}
            return render_template(self.maintem, **context)
        context = {'msg': "You didn't provide a file.", 'post_page': False}
        return render_template(self.maintem, **context)

running.add_url_rule('/', view_func=MainView.as_view('MainView'), methods=['GET', 'POST'])