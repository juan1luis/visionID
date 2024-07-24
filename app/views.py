from flask import render_template, Blueprint, request
from werkzeug.utils import secure_filename
from flask.views import View
import os

#Import required modules
from app.vision import ExtractData

from . import app
app.app_context().push()

running = Blueprint('running', __name__)



class MainView(View):
    def __init__(self):
        self.ALLOWED_EXTENSIONS = {'jpg'}
        self.maintem = 'index.html'
        self.path_file_save = os.path.join(app.config['APP_PATH'],r'workfiles')

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
            'data': {},
            'post_page': False

            }
        
        return render_template(self.maintem, **context)
    
    def post(self):
        file = request.files['image_file']  # Access the uploaded file
            
        if file:
            #Validate the file name and save it.
            if file and self.allowed_file(file.filename):
                filename = secure_filename(file.filename)
                path_file = os.path.join(self.path_file_save, filename)
                file.save(path_file)


                try:
                    extract = ExtractData(img_path=path_file)
                    extract.execute()
                    
                    context = {
                        'data': extract.data_f,
                        'msgs' : extract.msgs
                    }
                except:
                    context = {'data':{}, 'msg': 'Something went wrong :/', 'post_page':False}
                
                os.remove(path_file)

                return render_template(self.maintem, **context)
            else:
                context = {'msg': "Is not a correct file '.jpg' ", 'post_page':False}
            return render_template(self.maintem, **context)
        context = {'msg': "You didn't provide a file.", 'post_page': False}
        return render_template(self.maintem, **context)

running.add_url_rule('/', view_func=MainView.as_view('MainView'), methods=['GET', 'POST'])