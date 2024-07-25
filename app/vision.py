import cv2
import numpy as np
import pandas as pd
import os
from app import app as APP
import re
import pytesseract as tess
tess.pytesseract.tesseract_cmd = os.path.join(os.path.dirname(APP.config['APP_PATH']),r'Tesseract-OCR\tesseract.exe')






class ExtractData:

    def __init__(self, img_path):
        self.img_path = img_path
        
        self.doc_text = ''
        self.text_struct = ''
        self.indx_clv_elec = -1

        self.indx_ready = set()

        self.msgs = []

        self.send_data = []
        self.perc_found = 0

        self.data_f = {
                'nombre': '',
                'domicilio': '',
                'clave_elector': '',
                'curp': '',
                'registro': '',
                'estado': '',
                'municipio': '',
                'seccion': '',
                'localidad': '',
                'emision': '',
                'vigencia': '',
                'nacimiento': '',
                'sexo': ''
            }
    
    #Extract text
    def extract_text_from_image(self):
        # Load the image using OpenCV
        image = cv2.imread(self.img_path)
        
        # Display the original image
        #cv2.imshow('Original Image', image)
        image = cv2.resize(image, (0,0), fx=1.8, fy=1.8)
        # Convert the image to grayscale
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply some preprocessing (optional, depends on the image)
        gray_image = cv2.medianBlur(gray_image, 3)  # Reduce noise

        #cv2.imshow('Gray Scale', gray_image)
        _, binary_image = cv2.threshold(gray_image, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Display the processed image
        #cv2.imshow('Processed Image', binary_image)
        
        # Wait for a key press and close the image windows
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        # Use Tesseract to extract text
        text = tess.image_to_string(binary_image)
        #text = tess.image_to_string(binary_image, lang='spa', config=f'--oem 3 --psm 6  -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789()/-.calmg* "')

        self.doc_text = text
        
        return True  
        
    def structure_data(self):

        lines = self.doc_text.split('\n')
        data = {}
        count = 0
        for i in range(len(lines)):

            if lines[i] != '':
                data[count] = lines[i]
                count += 1

        self.text_struct = data

        return True
    
    def extract_NOMBRE_NACIM_SEX(self):
        pattern = re.compile(r'\b\w*NOMBRE\w*\b', re.IGNORECASE)

        for key, line in self.text_struct.items():

            match = pattern.search(line)

            if match:
                self.indx_ready.add(key) #Index where the word 'NAME' is.

                line_data_1 = self.text_struct[key+1].split(' ')
                self.indx_ready.add(key + 1) #Index where the word First last name is.
                last_name_1 = line_data_1[0]

                #The born date is in the same line as the first last name
                self.data_f['nacimiento'] = line_data_1[1]

                line_data_2 = self.text_struct[key + 2].split(' ')
                self.indx_ready.add(key + 2) #Index where the word Second last name is.
                last_name_2 = line_data_2[0]

                #The sex is in the same line as the second last name
                if len(line_data_2) >= 3:
                    
                    self.data_f['sexo'] = line_data_2[2]
                
                raw_name = self.text_struct[key + 3].split(' ')
                self.indx_ready.add(key + 3) #Index where the word Name is.

                filter_name = [part for part in raw_name if len(part) > 1]
        
                # Join the filtered words into a single string
                name = ' '.join(filter_name)
                
                self.data_f['nombre'] = f'{name} {last_name_1} {last_name_2}'

    #Find Data   
    def extract_DOMICILIO(self):

        pattern = re.compile(r'\bDOMIC\w*\b', re.IGNORECASE)

        for key, value in self.text_struct.items():
            if pattern.search(value):

                indx_domici = key
                direc = ''
                for key_2, value in self.text_struct.items():
                    if indx_domici < key_2 < self.indx_clv_elec:
                        direc += ' ' + value

                self.data_f['domicilio'] = direc
                return True
            
        print('Domicilio not found')
        return False
    
    def extract_CLAVE_DE_ELECTOR(self):

        pattern = re.compile(r'\bCLAVE\s+DE\s+ELECTOR\s+(\S+)', re.IGNORECASE)

        for key, line in self.text_struct.items():

            match = pattern.search(line)

            # Check if the pattern matched
            if match:
                self.indx_ready.add(key + 2) #Index where the word Clave De ELECTOR is.

                extracted_value = match.group(1)  # Get the first capturing group
                self.data_f['clave_elector'] = extracted_value
                self.indx_clv_elec = key
                return True
            
        print('CLAVE DE ELECTOR not found')
        return False
    
    def extract_EDO_MUNP_SECC(self):

        # Pattern to match any word containing 'ESTADO'
        pattern_edo = re.compile(r'\b\w*ESTA\w*\b', re.IGNORECASE)

        # Iterate over the lines in self.text_struct
        for key, line in self.text_struct.items():
            
            # Search for the pattern in the line
            match = pattern_edo.search(line)
            
            # Print whether a match was found
            if match:
                self.indx_ready.add(key) #Index with the 3 values
                
                line_values = line.split(' ')
                self.data_f['estado'] = line_values[1]
                self.data_f['municipio'] = line_values[3]
                self.data_f['seccion'] = line_values[5]

    def extract_CURP_REGIS(self):

        pattern = re.compile(r'\b\w*CURP\w*\b', re.IGNORECASE)

        for key, line in self.text_struct.items():

            match = pattern.search(line)

            if match:
                self.indx_ready.add(key) #Index with the CURP
                line_data = self.text_struct[key].split(' ')

                self.data_f['curp'] = line_data[1]

                self.data_f['registro'] = line_data[-2]
                



                return True
        self.msgs.append({'detail':'CURP not found'})
        return False

    def extract_LOC_EMIS_VIGEN(self):

        # Pattern to match any word containing 'ESTADO'
        pattern_edo = re.compile(r'\b\w*LOCALIDAD\w*\b', re.IGNORECASE)

        # Iterate over the lines in self.text_struct
        for key, line in self.text_struct.items():
            
            # Search for the pattern in the line
            match = pattern_edo.search(line)
            
            # Print whether a match was found
            if match:
                self.indx_ready.add(key) #Index with the 3 values

                line_values = line.split(' ')
                try:
                    self.data_f['localidad'] = line_values[1]
                except:
                    self.msgs.append({'detail':'LOCALIDAD not found'})
                    
                try:
                    self.data_f['municipio'] = line_values[3]
                except:
                    self.msgs.append({'detail':'SECCION not found'})

                try:
                    self.data_f['seccion'] = line_values[5]
                except:
                    self.msgs.append({'detail':'SECCION not found'})

                return True
            
        self.msgs.append({'detail':'LOCALIDAD not found'})
        return False
    
    def sinte(self):
        data = []
        count_found = 0

        for key, value in self.data_f.items():

            found = value != ''

            item = {
                'key': key,
                'value': value,
                'found': found
            }

            data.append(item)

            if found:
                count_found +=1


        if count_found !=0:
            self.perc_found = np.round(len(self.data_f)/count_found)*100
        
        self.send_data = data

        return True


    def start_finding(self):

        self.extract_NOMBRE_NACIM_SEX()
        self.extract_CLAVE_DE_ELECTOR()
        if self.indx_clv_elec != -1:
            self.extract_DOMICILIO()
        self.extract_EDO_MUNP_SECC()
        self.extract_CURP_REGIS()

    def execute(self):

        self.extract_text_from_image()
        self.structure_data()

        self.start_finding()

        self.sinte()