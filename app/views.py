from flask import render_template, Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from flask.views import View
import os
import glob
from datetime import datetime

# Import required modules
from app.vision import ExtractData

from . import app
app.app_context().push()

running = Blueprint('running', __name__)

def delete_all_images(except_path, static_path):
    directory = os.path.join(static_path, 'img_worked')
    image_extensions = ('*.png', '*.jpg', '*.jpeg', '*.gif')
     # Iterate over each image extension
    for extension in image_extensions:
        files = glob.glob(os.path.join(directory, extension))
        num_of_images = len(files)

        if num_of_images >= 10:
            # Iterate over the found files and delete them
            for file in files:
                #We avoid to delete the img just processed to show it.
                if except_path != file:
                    try:
                        os.remove(file)
                    except Exception as e:
                        print(f"Error deleting {file}: {e}")

class BaseView(View):
    ALLOWED_EXTENSIONS = {'jpg'}

    def __init__(self):
        self.path_file_save_w = os.path.join(app.config['APP_PATH'], 'workfiles')
        self.path_file_save_s = os.path.join(app.config['STATIC_PATH'], 'img_worked')

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in BaseView.ALLOWED_EXTENSIONS

    def save_file(self, file):
        #First secure the name then create a unique name to stored for a moment, so the user can whatch the image
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        hashed_filename = timestamp + filename
        file_data = file.read()

        #Then the image is saved in two diferent paths, one if the work with it
        # and the second is for the user.
        path_file_w = os.path.join(self.path_file_save_w, hashed_filename)
        with open(path_file_w, 'wb') as f:
            f.write(file_data)

        path_file_s = os.path.join(self.path_file_save_s, hashed_filename)
        with open(path_file_s, 'wb') as f:
            f.write(file_data)

        return path_file_w, path_file_s, hashed_filename

    def process_image(self, path_file_w):
        # We use this class to process the images, and we get the data.
        extract = ExtractData(img_path=path_file_w)
        extract.execute()

        return {
            'structured_data': extract.send_data,
            'raw_data': extract.data_f,
            'data_extracted': extract.text_struct,
            'graph_data': extract.graph_data,
        }
    
#This View is gonna be used for the user to interact
class MainView(BaseView):
    def __init__(self):
        super().__init__()
        self.maintem = 'index.html'

    def dispatch_request(self):
        if request.method == 'GET':
            return self.get()
        elif request.method == 'POST':
            return self.post()
        else:
            return 'Method not allowed', 405

    def get(self):
        context = {'post_page': False}
        return render_template(self.maintem, **context)

    def post(self):
        file = request.files.get('image_file') # Access the uploaded file
        if not file:
            return render_template(self.maintem, {'msg': "You didn't provide a file.", 'post_page': False})

        if self.allowed_file(file.filename):
            #First save the file
            path_file_w, path_file_s, hashed_filename = self.save_file(file)
            # Then we start the process and send the data
            data = self.process_image(path_file_w)
            data['img_path'] = f'img_worked/{hashed_filename}'
            context = {'data': data}
            try:
                pass
            except Exception:
                context = {'data': {}, 'msg': 'Something went wrong', 'post_page': False}
            finally:
                os.remove(path_file_w)
                delete_all_images(path_file_s, app.config['STATIC_PATH'])
        else:
            context = {'msg': "Is not a correct file '.jpg'", 'post_page': False}

        return render_template(self.maintem, **context)

#This View allow to offert a service to who wants to use this app as a service for their own app.
class APIRestView(BaseView):
    def dispatch_request(self):
        if request.method == 'POST':
            return self.post()
        else:
            return jsonify({'error': 'Method not allowed'}), 405

    def post(self):
        file = request.files.get('image_file')
        if not file:
            return jsonify({'error': "You didn't provide a file."}), 400

        if self.allowed_file(file.filename):
            path_file_w, path_file_s, hashed_filename = self.save_file(file)
            data = self.process_image(path_file_w)
            data['img_path'] = f'img_worked/{hashed_filename}'
            return jsonify(data), 200
            try:
                pass
            except Exception as e:
                return jsonify({'error': str(e)}), 500
            finally:
                os.remove(path_file_w)
                delete_all_images(path_file_s, app.config['STATIC_PATH'])
        else:
            return jsonify({'error': "The file provided is not a correct '.jpg' file."}), 400



#We let notice Flask about the views
app.add_url_rule('/', view_func=MainView.as_view('MainView'), methods=['GET', 'POST'])
app.add_url_rule('/api-request', view_func=APIRestView.as_view('APIRestView'), methods=['POST'])