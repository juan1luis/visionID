import cv2
import numpy as np
import pandas as pd
import os
from app import app as APP
import re
import pytesseract as tess
#tess.pytesseract.tesseract_cmd = os.path.join(os.path.dirname(APP.config['APP_PATH']),r'Tesseract-OCR/tesseract.exe')
tess.pytesseract.tesseract_cmd = '/usr/bin/tesseract'



class ExtractData:

    def __init__(self, img_path):
        self.img_path = img_path
        
        self.doc_text = ''
        self.text_struct = ''
        self.indx_clv_elec = -1

        self.msgs = []

        self.send_data = []
        self.perc_found = 0

        self.graph_data = {}

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
    
    def extract_text_from_image(self):
        # Load the image using OpenCV
        image = cv2.imread(self.img_path)
        
        # Resize the image for better accuracy (optional)
        
        # Convert the image to grayscale
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply a median blur to reduce noise
        gray_image = cv2.medianBlur(gray_image, 3)
        
        # Apply adaptive thresholding
        adaptive_thresh = cv2.adaptiveThreshold(
            gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 91, 2)
        
        # Apply morphological operations to close gaps and reduce noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        morph_image = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
        
        # Apply Canny edge detection
        edges = cv2.Canny(morph_image, 50, 150)
        
        # Find contours in the edged image
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Initialize a variable to store the largest rectangle contour
        largest_rect = None
        largest_area = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 1000:  # Filter out small contours by area
                continue

            # Approximate the contour to a polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Check if the approximated contour has four points (rectangle)
            if len(approx) == 4:
                if area > largest_area:
                    largest_area = area
                    largest_rect = approx
        
        # Draw all contours for visualization
        contour_image = image.copy()
        cv2.drawContours(contour_image, contours, -1, (0, 255, 0), 2)  # Draw all contours in green
        
        # Draw all rectangular contours
        for contour in contours:
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            if len(approx) == 4:
                cv2.drawContours(contour_image, [approx], -1, (255, 0, 0), 2)  # Draw all rectangles in blue
        
        # Draw the largest rectangle contour in red
        if largest_rect is not None:
            cv2.drawContours(contour_image, [largest_rect], -1, (0, 0, 255), 2)  # Draw the largest rectangle in red

        # Display the image with contours

        # If a rectangle was found, crop the image to that rectangle
        if largest_rect is not None:
            x, y, w, h = cv2.boundingRect(largest_rect)
            cropped_image = image[y:y+h, x:x+w]
        else:
            cropped_image = image
        
        #cv2.imshow('cropped_image', cropped_image)


        cropped_image_re = cv2.resize(cropped_image, (0, 0), fx=1.8, fy=1.8)

        
        # Convert the cropped image to grayscale
        gray_cropped = cv2.cvtColor(cropped_image_re, cv2.COLOR_BGR2GRAY)
        
        #cv2.imshow('gray_cropped', gray_cropped)

        # Apply a median blur to reduce noise
        gray_cropped = cv2.medianBlur(gray_cropped, 1)

        # Apply binary thresholding
        _, binary_image = cv2.threshold(gray_cropped, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        #cv2.imshow('binary_image', binary_image)

        
        # Use Tesseract to extract text
        text = tess.image_to_string(binary_image)
        


        #cv2.waitKey(0)
        #cv2.destroyAllWindows()
        self.doc_text = text
        
        return True

    def structure_data(self):

        lines = self.doc_text.split('\n')
        data = {}
        count = 0
        for i in range(len(lines)):

            if lines[i] != '' and len(lines[i]) >= 3:
                data[count] = lines[i]
                count += 1

        self.text_struct = data

        return True

    #Find Data   
    def num_from_str(self, string):
        # Find all numeric sequences in the text
        numbers = re.findall(r'\d+', string)
        
        # Join all numbers into a single string
        concatenated_number = ''.join(numbers)
        
        return concatenated_number

    def extract_NOMBRE_NACIM_SEX(self):
        pattern = re.compile(r'\b\w*NOMBRE\w*\b', re.IGNORECASE)

        for key, line in self.text_struct.items():

            match = pattern.search(line)

            if match:

                try:

                    line_data_1 = self.text_struct[key+1].split(' ')
                    last_name_1 = line_data_1[0]

                    #The born date is in the same line as the first last name
                    self.data_f['nacimiento'] = line_data_1[1]

                    line_data_2 = self.text_struct[key + 2].split(' ')
                    last_name_2 = line_data_2[0]

                    #The sex is in the same line as the second last name
                    if len(line_data_2) >= 3:
                        
                        self.data_f['sexo'] = line_data_2[2]
                    
                    raw_name = self.text_struct[key + 3].split(' ')

                    filter_name = [part for part in raw_name if len(part) > 1]
            
                    # Join the filtered words into a single string
                    name = ' '.join(filter_name)
                    
                    self.data_f['nombre'] = f'{name} {last_name_1} {last_name_2}'
                    return True
                except:
                    return False

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
                try:
                    extracted_value = match.group(1)  # Get the first capturing group
                    self.data_f['clave_elector'] = extracted_value
                except:
                    pass
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
                line_values = line.split(' ')
                try:
                    self.data_f['estado'] = self.num_from_str(line_values[1])
                except:
                    pass
                try:
                    self.data_f['municipio'] = self.num_from_str(line_values[3])
                except:
                    pass
                try:
                    self.data_f['seccion'] = self.num_from_str(line_values[5])
                except:
                    pass

    def extract_CURP_REGIS(self):

        pattern = re.compile(r'\b\w*CUR\w*\b', re.IGNORECASE)

        for key, line in self.text_struct.items():

            match = pattern.search(line)

            if match:
                line_data = self.text_struct[key].split(' ')
                try:
                    self.data_f['curp'] = line_data[1]
                except:
                    pass
                try:
                    self.data_f['registro'] = line_data[-2]
                except:
                    pass

                return True
        self.msgs.append({'detail':'CURP not found'})
        return False

    def extract_LOC_EMIS_VIGEN(self):

        # Pattern to match any word containing 'ESTADO'
        pattern =  re.compile(r'\b\w*(?:LOCALIDAD|EMISION|VIGENCIA)\w*\b', re.IGNORECASE)

        # Iterate over the lines in self.text_struct
        for key, line in self.text_struct.items():
            
            # Search for the pattern in the line
            match = pattern.findall(line)
            if match:
                line_values = line.split(' ')
                try:
                    self.data_f['localidad'] =self.num_from_str(line_values[1])
                except:
                    pass                    
                try:
                    self.data_f['emision'] = self.num_from_str(line_values[3])
                except:
                    pass
                try:
                    self.data_f['vigencia'] =  self.num_from_str(line_values[5])
                except:
                    pass
                return True
            
        return False
    
    def sinte(self):
        data = []
        count_found = 0
        indx = 0
        for key, value in self.data_f.items():

            found = value != ''

            item = {
                'id': indx,
                'key': key,
                'value': value,
                'found': found
            }

            data.append(item)

            #Increment values found
            if found:
                count_found +=1

            #Increment index value
            indx +=1

        if count_found !=0:
            self.perc_found = np.round((count_found/len(self.data_f))*100)
        
        self.send_data = data

        return True

    def calculate_perce(self):
        perc_local = self.perc_found

        graph = {
            'values': [perc_local,100-perc_local],
            'lables': ['',''],
            'colors': ['#FDFEFE','#FDFEFE'],
            'percentage': perc_local
        }
    
        if perc_local >= 95:
            graph['colors'][0] = '#2ECC71'

        elif perc_local >= 75:
            graph['colors'][0] = '#F4D03F'

        elif perc_local >= 50:
            graph['colors'][0] = '#F39C12'
        else:
            graph['colors'][0] = '#E74C3C'

        self.graph_data = graph

        return True

    def start_finding(self):

        self.extract_NOMBRE_NACIM_SEX()
        self.extract_CLAVE_DE_ELECTOR()
        if self.indx_clv_elec != -1:
            self.extract_DOMICILIO()
        self.extract_EDO_MUNP_SECC()
        self.extract_CURP_REGIS()
        self.extract_LOC_EMIS_VIGEN()

    def execute(self):

        self.extract_text_from_image()
        self.structure_data()

        self.start_finding()

        self.sinte()
        self.calculate_perce()